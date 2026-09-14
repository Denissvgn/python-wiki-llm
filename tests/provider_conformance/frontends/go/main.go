// Parse-only independent observer using the Go standard library.
package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"go/ast"
	"go/parser"
	"go/printer"
	"go/token"
	"io"
	"os"
	"reflect"
	"strconv"
	"strings"
)

type Job struct {
	Mode string `json:"mode"`
	Text string `json:"text"`
}
type Record = map[string]any

func printed(node any) string {
	var b bytes.Buffer
	if node != nil {
		_ = printer.Fprint(&b, token.NewFileSet(), node)
	}
	return b.String()
}
func canonical(v reflect.Value) any {
	if !v.IsValid() {
		return nil
	}
	if v.Kind() == reflect.Interface || v.Kind() == reflect.Pointer {
		if v.IsNil() {
			return nil
		}
		if par, ok := v.Interface().(*ast.ParenExpr); ok {
			return canonical(reflect.ValueOf(par.X))
		}
		return canonical(v.Elem())
	}
	if v.Type() == reflect.TypeOf(token.Pos(0)) {
		return nil
	}
	if v.Kind() == reflect.Struct {
		out := Record{"node": v.Type().Name()}
		for i := 0; i < v.NumField(); i++ {
			field := v.Type().Field(i)
			if field.PkgPath != "" || field.Type == reflect.TypeOf(token.Pos(0)) {
				continue
			}
			if field.Name == "Obj" || field.Name == "Scope" || field.Name == "Doc" || field.Name == "Comment" || field.Name == "Comments" {
				continue
			}
			out[field.Name] = canonical(v.Field(i))
		}
		if lit, ok := v.Interface().(ast.BasicLit); ok && (lit.Kind == token.STRING || lit.Kind == token.CHAR) {
			value, err := strconv.Unquote(lit.Value)
			if err == nil {
				out["Value"] = value
			}
		}
		return out
	}
	if v.Kind() == reflect.Slice {
		out := []any{}
		for i := 0; i < v.Len(); i++ {
			out = append(out, canonical(v.Index(i)))
		}
		return out
	}
	return v.Interface()
}
func params(fields *ast.FieldList) []Record {
	result := []Record{}
	if fields == nil {
		return result
	}
	for _, field := range fields.List {
		if len(field.Names) == 0 {
			result = append(result, Record{"name": "", "type": printed(field.Type)})
		}
		for _, name := range field.Names {
			result = append(result, Record{"name": name.Name, "type": printed(field.Type)})
		}
	}
	return result
}
func resultType(fields *ast.FieldList) string {
	if fields == nil {
		return ""
	}
	parts := []string{}
	for _, field := range fields.List {
		n := len(field.Names)
		if n == 0 {
			n = 1
		}
		for i := 0; i < n; i++ {
			parts = append(parts, printed(field.Type))
		}
	}
	if len(parts) == 1 {
		return parts[0]
	}
	return "(" + strings.Join(parts, ", ") + ")"
}
func observe(text string) (any, error) {
	fset := token.NewFileSet()
	file, err := parser.ParseFile(fset, "probe.go", text, parser.AllErrors)
	if err != nil {
		return nil, err
	}
	records, imports := []Record{}, []Record{}
	for _, item := range file.Imports {
		path, err := strconv.Unquote(item.Path.Value)
		if err != nil {
			return nil, err
		}
		imports = append(imports, Record{"module": path, "line": fset.Position(item.Pos()).Line})
	}
	for _, node := range file.Decls {
		switch d := node.(type) {
		case *ast.FuncDecl:
			owner := ""
			if d.Recv != nil && len(d.Recv.List) > 0 {
				owner = printed(d.Recv.List[0].Type)
				owner = strings.TrimPrefix(owner, "*")
				if i := strings.Index(owner, "["); i >= 0 {
					owner = owner[:i]
				}
			}
			kind := "function"
			if owner != "" {
				kind = "method"
			}
			records = append(records, Record{"kind": kind, "name": d.Name.Name, "owner": owner, "line": fset.Position(d.Pos()).Line, "params": params(d.Type.Params), "return_type": resultType(d.Type.Results), "type_parameters": params(d.Type.TypeParams)})
		case *ast.GenDecl:
			for _, spec := range d.Specs {
				t, ok := spec.(*ast.TypeSpec)
				if !ok {
					continue
				}
				kind := "named_type"
				switch t.Type.(type) {
				case *ast.StructType:
					kind = "struct"
				case *ast.InterfaceType:
					kind = "interface"
				}
				records = append(records, Record{"kind": "class", "declaration_kind": kind, "name": t.Name.Name, "owner": "", "line": fset.Position(t.Pos()).Line, "type": printed(t.Type), "alias": t.Assign.IsValid()})
				if st, ok := t.Type.(*ast.StructType); ok {
					for _, field := range st.Fields.List {
						for _, name := range field.Names {
							records = append(records, Record{"kind": "attribute", "name": name.Name, "owner": t.Name.Name, "line": fset.Position(field.Pos()).Line, "type": printed(field.Type)})
						}
					}
				}
				if it, ok := t.Type.(*ast.InterfaceType); ok {
					for _, field := range it.Methods.List {
						fn, ok := field.Type.(*ast.FuncType)
						if !ok {
							continue
						}
						for _, name := range field.Names {
							records = append(records, Record{"kind": "method", "name": name.Name, "owner": t.Name.Name, "line": fset.Position(field.Pos()).Line, "params": params(fn.Params), "return_type": resultType(fn.Results)})
						}
					}
				}
			}
		}
	}
	return Record{"declarations": records, "imports": imports, "module": file.Name.Name}, nil
}
func run(job Job) (any, error) {
	if job.Mode == "source" {
		return observe(job.Text)
	}
	if job.Mode == "type" && strings.HasPrefix(strings.TrimSpace(job.Text), "...") {
		file, e := parser.ParseFile(token.NewFileSet(), "probe.go", "package p\nfunc probe(value "+job.Text+") {}", 0)
		if e != nil {
			return nil, e
		}
		return canonical(reflect.ValueOf(file.Decls[0].(*ast.FuncDecl).Type.Params.List[0].Type)), nil
	}
	expr, err := parser.ParseExpr(job.Text)
	if err != nil && job.Mode == "type" && strings.HasPrefix(strings.TrimSpace(job.Text), "(") {
		fs := token.NewFileSet()
		file, e := parser.ParseFile(fs, "probe.go", "package p\nfunc probe() "+job.Text+" {}", 0)
		if e == nil {
			return canonical(reflect.ValueOf(file.Decls[0].(*ast.FuncDecl).Type.Results)), nil
		}
	}
	if err != nil {
		return nil, err
	}
	return canonical(reflect.ValueOf(expr)), nil
}
func main() {
	data, err := io.ReadAll(os.Stdin)
	if err != nil {
		panic(err)
	}
	var jobs []Job
	if err = json.Unmarshal(data, &jobs); err != nil {
		panic(err)
	}
	out := []any{}
	for _, job := range jobs {
		value, e := run(job)
		if e != nil {
			fmt.Fprintln(os.Stderr, e)
			os.Exit(2)
		}
		out = append(out, value)
	}
	if err = json.NewEncoder(os.Stdout).Encode(out); err != nil {
		panic(err)
	}
}
