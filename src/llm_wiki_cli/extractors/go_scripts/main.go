// Go AST extractor for agent-wiki-cli.
//
// Usage: go run . --src-dir <path> [--only-files <f1,f2,...>] [--deep]
//
// Outputs a JSON inventory to stdout (same canonical schema as PythonExtractor
// and TypeScriptExtractor). The "language" field is intentionally absent —
// GoExtractor stamps it in Python.
// Errors/warnings go to stderr.  Exit 0 on success.
package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"go/ast"
	"go/parser"
	"go/token"
	"os"
	"path/filepath"
	"strings"
	"unicode"
)

// ── Excluded directories ──────────────────────────────────────────────────────

var excludedDirs = map[string]bool{
	".cache":           true,
	".direnv":          true,
	".eggs":            true,
	".env":             true,
	".git":             true,
	".mypy_cache":      true,
	".next":            true,
	".nox":             true,
	".npm":             true,
	".nuxt":            true,
	".parcel-cache":    true,
	".pnpm-store":      true,
	".pyre":            true,
	".pytest_cache":    true,
	".ruff_cache":      true,
	".svelte-kit":      true,
	".tox":             true,
	".venv":            true,
	".virtualenv":      true,
	".vite":            true,
	".yarn":            true,
	"__pycache__":      true,
	"__pypackages__":   true,
	"bower_components": true,
	"build":            true,
	"coverage":         true,
	"dist":             true,
	"env":              true,
	"htmlcov":          true,
	"jspm_packages":    true,
	"node_modules":     true,
	"out":              true,
	"site-packages":    true,
	"target":           true,
	"testdata":         true,
	"vendor":           true,
	"venv":             true,
	"virtualenv":       true,
}

// ── Schema types ──────────────────────────────────────────────────────────────

type ParamInfo struct {
	Name string `json:"name"`
	Type string `json:"type,omitempty"`
}

type MethodInfo struct {
	Name       string      `json:"name"`
	Line       int         `json:"line"`
	IsAsync    bool        `json:"is_async"`
	Docstring  string      `json:"docstring,omitempty"`
	Decorators []string    `json:"decorators,omitempty"`
	Params     []ParamInfo `json:"params,omitempty"`
	ReturnType string      `json:"return_type,omitempty"`
}

type AttributeInfo struct {
	Name    string `json:"name"`
	Type    string `json:"type,omitempty"`
	Default string `json:"default,omitempty"`
	Tag     string `json:"tag,omitempty"`
}

type ClassInfo struct {
	Name       string          `json:"name"`
	Kind       string          `json:"kind"`
	Bases      []string        `json:"bases"`
	Line       int             `json:"line"`
	Docstring  string          `json:"docstring,omitempty"`
	Decorators []string        `json:"decorators,omitempty"`
	Attributes []AttributeInfo `json:"attributes,omitempty"`
	Methods    []MethodInfo    `json:"methods,omitempty"`
}

type FunctionInfo struct {
	Name       string      `json:"name"`
	Line       int         `json:"line"`
	IsAsync    bool        `json:"is_async"`
	Receiver   string      `json:"receiver,omitempty"`
	Docstring  string      `json:"docstring,omitempty"`
	Decorators []string    `json:"decorators,omitempty"`
	Params     []ParamInfo `json:"params,omitempty"`
	ReturnType string      `json:"return_type,omitempty"`
}

type ImportInfo struct {
	Module string  `json:"module"`
	Name   string  `json:"name"`
	Alias  *string `json:"alias"`
	Type   string  `json:"type"`
}

type FileEntry struct {
	Classes   []ClassInfo    `json:"classes"`
	Functions []FunctionInfo `json:"functions"`
	Imports   []ImportInfo   `json:"imports,omitempty"`
}

// ── Helpers ───────────────────────────────────────────────────────────────────

func isExported(name string) bool {
	if name == "" {
		return false
	}
	return unicode.IsUpper(rune(name[0]))
}

func exprToString(expr ast.Expr) string {
	if expr == nil {
		return ""
	}
	switch e := expr.(type) {
	case *ast.Ident:
		return e.Name
	case *ast.SelectorExpr:
		return exprToString(e.X) + "." + e.Sel.Name
	case *ast.StarExpr:
		return "*" + exprToString(e.X)
	case *ast.ArrayType:
		return "[]" + exprToString(e.Elt)
	case *ast.MapType:
		return "map[" + exprToString(e.Key) + "]" + exprToString(e.Value)
	case *ast.InterfaceType:
		return "interface{}"
	case *ast.ChanType:
		switch e.Dir {
		case ast.SEND:
			return "chan<- " + exprToString(e.Value)
		case ast.RECV:
			return "<-chan " + exprToString(e.Value)
		default:
			return "chan " + exprToString(e.Value)
		}
	case *ast.FuncType:
		return "func(...)"
	case *ast.Ellipsis:
		return "..." + exprToString(e.Elt)
	case *ast.IndexExpr:
		return exprToString(e.X) + "[" + exprToString(e.Index) + "]"
	case *ast.IndexListExpr:
		parts := make([]string, len(e.Indices))
		for i, idx := range e.Indices {
			parts[i] = exprToString(idx)
		}
		return exprToString(e.X) + "[" + strings.Join(parts, ", ") + "]"
	default:
		return ""
	}
}

func docText(doc *ast.CommentGroup) string {
	if doc == nil {
		return ""
	}
	return strings.TrimSpace(doc.Text())
}

func extractParams(fields *ast.FieldList) []ParamInfo {
	if fields == nil {
		return nil
	}
	var params []ParamInfo
	for _, f := range fields.List {
		typeStr := exprToString(f.Type)
		if len(f.Names) == 0 {
			// Unnamed parameter (e.g. in interface method signatures)
			params = append(params, ParamInfo{Name: "", Type: typeStr})
		} else {
			for _, name := range f.Names {
				params = append(params, ParamInfo{Name: name.Name, Type: typeStr})
			}
		}
	}
	return params
}

func extractReturnType(fields *ast.FieldList) string {
	if fields == nil || len(fields.List) == 0 {
		return ""
	}
	if len(fields.List) == 1 && len(fields.List[0].Names) == 0 {
		return exprToString(fields.List[0].Type)
	}
	// Multiple return values: (Type1, Type2, ...)
	parts := make([]string, 0, len(fields.List))
	for _, f := range fields.List {
		typeStr := exprToString(f.Type)
		if len(f.Names) == 0 {
			parts = append(parts, typeStr)
		} else {
			for _, name := range f.Names {
				parts = append(parts, name.Name+" "+typeStr)
			}
		}
	}
	return "(" + strings.Join(parts, ", ") + ")"
}

func receiverTypeName(fn *ast.FuncDecl) string {
	if fn.Recv == nil || len(fn.Recv.List) == 0 {
		return ""
	}
	t := fn.Recv.List[0].Type
	// Dereference pointer receivers: *T → T
	if star, ok := t.(*ast.StarExpr); ok {
		t = star.X
	}
	if ident, ok := t.(*ast.Ident); ok {
		return ident.Name
	}
	// Generic receiver: T[K] — use the base type name.
	if idx, ok := t.(*ast.IndexExpr); ok {
		if ident, ok := idx.X.(*ast.Ident); ok {
			return ident.Name
		}
	}
	if idx, ok := t.(*ast.IndexListExpr); ok {
		if ident, ok := idx.X.(*ast.Ident); ok {
			return ident.Name
		}
	}
	return ""
}

// ── File collection ───────────────────────────────────────────────────────────

func collectGoFiles(root string, includeTests bool) ([]string, error) {
	var files []string
	err := filepath.Walk(root, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return nil // skip unreadable entries
		}
		if info.IsDir() {
			name := info.Name()
			if excludedDirs[name] || strings.HasPrefix(name, ".") || strings.HasPrefix(name, "_") {
				return filepath.SkipDir
			}
			return nil
		}
		if filepath.Ext(path) == ".go" && (includeTests || !strings.HasSuffix(info.Name(), "_test.go")) {
			files = append(files, path)
		}
		return nil
	})
	return files, err
}

func isOutsideRoot(rel string) bool {
	return rel == ".." || filepath.IsAbs(rel) || strings.HasPrefix(rel, ".."+string(filepath.Separator))
}

func hasExcludedDir(relPath string) bool {
	dir := filepath.Dir(relPath)
	if dir == "." || dir == "" {
		return false
	}
	for _, part := range strings.Split(filepath.ToSlash(dir), "/") {
		if part == "" {
			continue
		}
		if excludedDirs[part] || strings.HasPrefix(part, ".") || strings.HasPrefix(part, "_") {
			return true
		}
	}
	return false
}

// ── Per-file extraction ───────────────────────────────────────────────────────

func extractFile(filename string, fset *token.FileSet, deep bool) (*FileEntry, error) {
	src, err := os.ReadFile(filename)
	if err != nil {
		return nil, err
	}

	mode := parser.ParseComments
	f, err := parser.ParseFile(fset, filename, src, mode)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Warning: could not parse %s: %v\n", filename, err)
		return nil, err
	}

	entry := &FileEntry{
		Classes:   []ClassInfo{},
		Functions: []FunctionInfo{},
	}

	// Collect receiver methods so we can attach them to structs in deep mode.
	type methodEntry struct {
		receiver string
		method   MethodInfo
	}
	var receiverMethods []methodEntry

	// Map struct/interface name → index in entry.Classes for attaching methods.
	classIndex := map[string]int{}

	for _, decl := range f.Decls {
		switch d := decl.(type) {
		case *ast.GenDecl:
			for _, spec := range d.Specs {
				ts, ok := spec.(*ast.TypeSpec)
				if !ok {
					continue
				}
				if !isExported(ts.Name.Name) {
					continue
				}

				switch st := ts.Type.(type) {
				case *ast.StructType:
					ci := ClassInfo{
						Name:  ts.Name.Name,
						Kind:  "struct",
						Bases: []string{},
						Line:  fset.Position(ts.Pos()).Line,
					}
					if deep {
						ci.Docstring = docText(d.Doc)
						if ci.Docstring == "" {
							ci.Docstring = docText(ts.Doc)
						}
						ci.Decorators = []string{}
						ci.Attributes = []AttributeInfo{}
						ci.Methods = []MethodInfo{}
					}
					// Extract embedded types as bases + attributes.
					if st.Fields != nil {
						for _, field := range st.Fields.List {
							if len(field.Names) == 0 {
								// Embedded type → base
								ci.Bases = append(ci.Bases, exprToString(field.Type))
							} else if deep {
								// Named field → attribute
								tag := ""
								if field.Tag != nil {
									tag = field.Tag.Value
								}
								for _, name := range field.Names {
									if isExported(name.Name) {
										ci.Attributes = append(ci.Attributes, AttributeInfo{
											Name: name.Name,
											Type: exprToString(field.Type),
											Tag:  tag,
										})
									}
								}
							}
						}
					}
					classIndex[ci.Name] = len(entry.Classes)
					entry.Classes = append(entry.Classes, ci)

				case *ast.InterfaceType:
					ci := ClassInfo{
						Name:  ts.Name.Name,
						Kind:  "interface",
						Bases: []string{},
						Line:  fset.Position(ts.Pos()).Line,
					}
					if deep {
						ci.Docstring = docText(d.Doc)
						if ci.Docstring == "" {
							ci.Docstring = docText(ts.Doc)
						}
						ci.Decorators = []string{}
						ci.Attributes = []AttributeInfo{}
						ci.Methods = []MethodInfo{}
					}
					if st.Methods != nil {
						for _, m := range st.Methods.List {
							if len(m.Names) == 0 {
								// Embedded interface
								ci.Bases = append(ci.Bases, exprToString(m.Type))
							} else if deep {
								ft, ok := m.Type.(*ast.FuncType)
								if !ok {
									continue
								}
								ci.Methods = append(ci.Methods, MethodInfo{
									Name:       m.Names[0].Name,
									Line:       fset.Position(m.Pos()).Line,
									IsAsync:    false,
									Docstring:  docText(m.Doc),
									Decorators: []string{},
									Params:     extractParams(ft.Params),
									ReturnType: extractReturnType(ft.Results),
								})
							}
						}
					}
					classIndex[ci.Name] = len(entry.Classes)
					entry.Classes = append(entry.Classes, ci)

				default:
					// Type alias (type X = Y) or named type (type X Y).
					kind := "named_type"
					if ts.Assign.IsValid() {
						kind = "type_alias"
					}
					ci := ClassInfo{
						Name:  ts.Name.Name,
						Kind:  kind,
						Bases: []string{},
						Line:  fset.Position(ts.Pos()).Line,
					}
					if deep {
						ci.Docstring = docText(d.Doc)
						if ci.Docstring == "" {
							ci.Docstring = docText(ts.Doc)
						}
						ci.Decorators = []string{}
						ci.Attributes = []AttributeInfo{}
						ci.Methods = []MethodInfo{}
					}
					classIndex[ci.Name] = len(entry.Classes)
					entry.Classes = append(entry.Classes, ci)
				}
			}

		case *ast.FuncDecl:
			if !isExported(d.Name.Name) {
				continue
			}
			recv := receiverTypeName(d)
			if recv != "" {
				// Receiver method — collect for later attachment.
				mi := MethodInfo{
					Name:    d.Name.Name,
					Line:    fset.Position(d.Pos()).Line,
					IsAsync: false,
				}
				if deep {
					mi.Docstring = docText(d.Doc)
					mi.Decorators = []string{}
					mi.Params = extractParams(d.Type.Params)
					mi.ReturnType = extractReturnType(d.Type.Results)
				}
				receiverMethods = append(receiverMethods, methodEntry{
					receiver: recv,
					method:   mi,
				})
			} else {
				// Top-level function.
				fi := FunctionInfo{
					Name:    d.Name.Name,
					Line:    fset.Position(d.Pos()).Line,
					IsAsync: false,
				}
				if deep {
					fi.Docstring = docText(d.Doc)
					fi.Decorators = []string{}
					fi.Params = extractParams(d.Type.Params)
					fi.ReturnType = extractReturnType(d.Type.Results)
				}
				entry.Functions = append(entry.Functions, fi)
			}
		}
	}

	// Attach receiver methods to their struct in deep mode.
	if deep {
		for _, rm := range receiverMethods {
			if idx, ok := classIndex[rm.receiver]; ok {
				entry.Classes[idx].Methods = append(entry.Classes[idx].Methods, rm.method)
			} else {
				// Receiver type not found as a class (e.g. unexported struct) —
				// expose as a standalone function with receiver field.
				entry.Functions = append(entry.Functions, FunctionInfo{
					Name:       rm.method.Name,
					Line:       rm.method.Line,
					IsAsync:    false,
					Receiver:   rm.receiver,
					Docstring:  rm.method.Docstring,
					Decorators: rm.method.Decorators,
					Params:     rm.method.Params,
					ReturnType: rm.method.ReturnType,
				})
			}
		}
	} else {
		// Shallow mode: receiver methods as standalone functions with receiver field.
		for _, rm := range receiverMethods {
			entry.Functions = append(entry.Functions, FunctionInfo{
				Name:     rm.method.Name,
				Line:     rm.method.Line,
				IsAsync:  false,
				Receiver: rm.receiver,
			})
		}
	}

	// ── Imports (deep only) ──────────────────────────────────────────────────
	if deep && f.Imports != nil {
		entry.Imports = []ImportInfo{}
		for _, imp := range f.Imports {
			path := strings.Trim(imp.Path.Value, `"`)
			// Use the last segment as the name (e.g. "fmt" from "fmt",
			// "json" from "encoding/json").
			parts := strings.Split(path, "/")
			name := parts[len(parts)-1]
			var alias *string
			impType := "import"
			if imp.Name != nil {
				switch imp.Name.Name {
				case ".":
					impType = "dot"
				case "_":
					impType = "blank"
				default:
					a := imp.Name.Name
					alias = &a
				}
			}
			entry.Imports = append(entry.Imports, ImportInfo{
				Module: path,
				Name:   name,
				Alias:  alias,
				Type:   impType,
			})
		}
	}

	return entry, nil
}

// ── Main ──────────────────────────────────────────────────────────────────────

func main() {
	srcDir := flag.String("src-dir", ".", "Root directory to scan")
	onlyFiles := flag.String("only-files", "", "Comma-separated list of files to extract")
	deep := flag.Bool("deep", false, "Include enriched data (docs, attributes, methods, imports)")
	includeTests := flag.Bool("include-tests", false, "Include Go _test.go files")
	flag.Parse()

	fset := token.NewFileSet()
	inventory := map[string]*FileEntry{}

	var files []string
	if *onlyFiles != "" {
		for _, f := range strings.Split(*onlyFiles, ",") {
			f = strings.TrimSpace(f)
			if f == "" {
				continue
			}
			abs := f
			if !filepath.IsAbs(f) {
				abs = filepath.Join(*srcDir, f)
			}
			rel, err := filepath.Rel(*srcDir, abs)
			if err != nil || isOutsideRoot(rel) || hasExcludedDir(rel) {
				continue
			}
			if _, err := os.Stat(abs); err == nil && filepath.Ext(abs) == ".go" && (*includeTests || !strings.HasSuffix(filepath.Base(abs), "_test.go")) {
				files = append(files, abs)
			}
		}
	} else {
		var err error
		files, err = collectGoFiles(*srcDir, *includeTests)
		if err != nil {
			fmt.Fprintf(os.Stderr, "Error walking %s: %v\n", *srcDir, err)
			os.Exit(1)
		}
	}

	for _, file := range files {
		entry, err := extractFile(file, fset, *deep)
		if err != nil {
			continue // warning already printed inside extractFile
		}
		// Use relative path from srcDir as key.
		rel, err := filepath.Rel(*srcDir, file)
		if err != nil {
			rel = file
		}
		inventory[rel] = entry
	}

	// ── Cross-file receiver attachment (deep mode, per-package) ────────────────
	// Go methods are often defined in a different file from the type they extend.
	// After all files are processed, attach any lingering receiver-method functions
	// to their type within the same directory (= package boundary).
	if *deep {
		// Build: dir → typeName → {relPath, classIdx}
		type classRef struct {
			relPath  string
			classIdx int
		}
		dirClassIndex := map[string]map[string]classRef{}
		for relPath, entry := range inventory {
			dir := filepath.Dir(relPath)
			if _, ok := dirClassIndex[dir]; !ok {
				dirClassIndex[dir] = map[string]classRef{}
			}
			for idx, cls := range entry.Classes {
				dirClassIndex[dir][cls.Name] = classRef{relPath: relPath, classIdx: idx}
			}
		}

		// For each file, find functions with a Receiver resolvable within
		// the same directory and move them into the target class's methods.
		for relPath, entry := range inventory {
			dir := filepath.Dir(relPath)
			remaining := make([]FunctionInfo, 0, len(entry.Functions))
			for _, fn := range entry.Functions {
				if fn.Receiver == "" {
					remaining = append(remaining, fn)
					continue
				}
				ref, ok := dirClassIndex[dir][fn.Receiver]
				if !ok {
					// Unexported or unknown type — leave as a function.
					remaining = append(remaining, fn)
					continue
				}
				// Attach to the target class as a method.
				target := inventory[ref.relPath]
				target.Classes[ref.classIdx].Methods = append(
					target.Classes[ref.classIdx].Methods,
					MethodInfo{
						Name:       fn.Name,
						Line:       fn.Line,
						IsAsync:    false,
						Docstring:  fn.Docstring,
						Decorators: fn.Decorators,
						Params:     fn.Params,
						ReturnType: fn.ReturnType,
					},
				)
			}
			entry.Functions = remaining
		}
	}

	enc := json.NewEncoder(os.Stdout)
	enc.SetIndent("", "  ")
	if err := enc.Encode(inventory); err != nil {
		fmt.Fprintf(os.Stderr, "Error encoding JSON: %v\n", err)
		os.Exit(1)
	}
}
