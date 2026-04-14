// Rust AST extractor for llm-wiki-cli.
//
// Usage: cargo run -- --src-dir <path> [--only-files <f1,f2,...>] [--deep]
//
// Outputs a JSON inventory to stdout (same canonical schema as PythonExtractor,
// TypeScriptExtractor, and GoExtractor).  The "language" field is intentionally
// absent — RustExtractor stamps it in Python.
// Errors/warnings go to stderr.  Exit 0 on success.

use std::collections::{BTreeMap, HashMap};
use std::env;
use std::fs;
use std::io::Write;
use std::path::{Path, PathBuf};

use serde::Serialize;

// ── Schema types ──────────────────────────────────────────────────────────────

#[derive(Serialize, Clone, Default)]
struct ParamInfo {
    name: String,
    #[serde(rename = "type", skip_serializing_if = "String::is_empty")]
    ty: String,
}

#[derive(Serialize, Clone, Default)]
struct MethodInfo {
    name: String,
    line: usize,
    is_async: bool,
    #[serde(skip_serializing_if = "String::is_empty")]
    docstring: String,
    #[serde(skip_serializing_if = "Vec::is_empty")]
    decorators: Vec<String>,
    #[serde(skip_serializing_if = "Vec::is_empty")]
    params: Vec<ParamInfo>,
    #[serde(skip_serializing_if = "String::is_empty")]
    return_type: String,
}

#[derive(Serialize, Clone, Default)]
struct AttributeInfo {
    name: String,
    #[serde(rename = "type", skip_serializing_if = "String::is_empty")]
    ty: String,
    #[serde(skip_serializing_if = "String::is_empty")]
    default: String,
}

#[derive(Serialize, Clone)]
struct ClassInfo {
    name: String,
    kind: String,
    bases: Vec<String>,
    line: usize,
    #[serde(skip_serializing_if = "String::is_empty")]
    docstring: String,
    #[serde(skip_serializing_if = "Vec::is_empty")]
    decorators: Vec<String>,
    #[serde(skip_serializing_if = "Vec::is_empty")]
    attributes: Vec<AttributeInfo>,
    #[serde(skip_serializing_if = "Vec::is_empty")]
    methods: Vec<MethodInfo>,
}

#[derive(Serialize, Clone, Default)]
struct FunctionInfo {
    name: String,
    line: usize,
    is_async: bool,
    #[serde(skip_serializing_if = "String::is_empty")]
    receiver: String,
    #[serde(skip_serializing_if = "String::is_empty")]
    docstring: String,
    #[serde(skip_serializing_if = "Vec::is_empty")]
    decorators: Vec<String>,
    #[serde(skip_serializing_if = "Vec::is_empty")]
    params: Vec<ParamInfo>,
    #[serde(skip_serializing_if = "String::is_empty")]
    return_type: String,
}

#[derive(Serialize, Clone)]
struct ImportInfo {
    module: String,
    name: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    alias: Option<String>,
    #[serde(rename = "type")]
    import_type: String,
}

#[derive(Serialize, Default)]
struct FileEntry {
    classes: Vec<ClassInfo>,
    functions: Vec<FunctionInfo>,
    #[serde(skip_serializing_if = "Vec::is_empty")]
    imports: Vec<ImportInfo>,
}

// ── Excluded directories ──────────────────────────────────────────────────────

fn is_excluded_dir(name: &str) -> bool {
    matches!(
        name,
        "target"
            | "vendor"
            | "testdata"
            | ".git"
            | "node_modules"
            | "__pycache__"
            | "venv"
            | ".venv"
            | "env"
            | ".env"
            | ".tox"
            | ".eggs"
            | "build"
            | "dist"
    )
}

// ── Helpers ───────────────────────────────────────────────────────────────────

/// Check if a Rust item has `#[cfg(test)]` attribute.
fn is_cfg_test(attrs: &[syn::Attribute]) -> bool {
    for attr in attrs {
        if attr.path().is_ident("cfg") {
            if let Ok(nested) = attr.parse_args::<syn::Ident>() {
                if nested == "test" {
                    return true;
                }
            }
        }
    }
    false
}

/// Extract doc comments from attributes (/// or #[doc = "..."]).
fn extract_doc_comment(attrs: &[syn::Attribute]) -> String {
    let mut lines = Vec::new();
    for attr in attrs {
        if attr.path().is_ident("doc") {
            if let syn::Meta::NameValue(nv) = &attr.meta {
                if let syn::Expr::Lit(syn::ExprLit {
                    lit: syn::Lit::Str(s),
                    ..
                }) = &nv.value
                {
                    let raw = s.value();
                    // Strip leading space (Rust doc comments have a leading space)
                    let line = raw.strip_prefix(' ').unwrap_or(&raw);
                    lines.push(line.to_string());
                }
            }
        }
    }
    lines.join("\n").trim().to_string()
}

/// Extract #[derive(...)] as decorator names.
fn extract_derives(attrs: &[syn::Attribute]) -> Vec<String> {
    let mut derives = Vec::new();
    for attr in attrs {
        if attr.path().is_ident("derive") {
            if let Ok(nested) =
                attr.parse_args_with(syn::punctuated::Punctuated::<syn::Path, syn::Token![,]>::parse_terminated)
            {
                for path in nested {
                    derives.push(path_to_string(&path));
                }
            }
        }
    }
    derives
}

/// Convert a syn::Type to a string representation.
fn type_to_string(ty: &syn::Type) -> String {
    // Use the token stream for a quick display.
    quote_to_string(ty)
}

fn path_to_string(path: &syn::Path) -> String {
    path.segments
        .iter()
        .map(|seg| seg.ident.to_string())
        .collect::<Vec<_>>()
        .join("::")
}

fn quote_to_string<T: quote::ToTokens>(t: &T) -> String {
    let ts = quote::quote!(#t);
    // Normalize spacing — collapse multiple spaces
    let s = ts.to_string();
    // Remove excess whitespace around punctuation for readability.
    s.replace(" :: ", "::")
        .replace(" < ", "<")
        .replace(" > ", ">")
        .replace(" , ", ", ")
        .replace("& ", "&")
        .replace("& mut ", "&mut ")
}

/// Extract the return type string from a syn::ReturnType.
fn return_type_to_string(ret: &syn::ReturnType) -> String {
    match ret {
        syn::ReturnType::Default => String::new(),
        syn::ReturnType::Type(_, ty) => type_to_string(ty),
    }
}

/// Extract parameters from an `fn` signature, skipping `self`.
fn extract_params(sig: &syn::Signature) -> Vec<ParamInfo> {
    let mut params = Vec::new();
    for input in &sig.inputs {
        match input {
            syn::FnArg::Receiver(_) => {} // skip self
            syn::FnArg::Typed(pat_ty) => {
                let name = quote_to_string(&pat_ty.pat);
                let ty = type_to_string(&pat_ty.ty);
                params.push(ParamInfo { name, ty });
            }
        }
    }
    params
}

/// Compute 1-based line number from a Span using the source text.
fn line_of(span: proc_macro2::Span) -> usize {
    span.start().line
}

// ── File collection ───────────────────────────────────────────────────────────

fn collect_rs_files(root: &Path) -> Vec<PathBuf> {
    let mut files = Vec::new();
    walk_dir(root, &mut files);
    files.sort();
    files
}

fn walk_dir(dir: &Path, out: &mut Vec<PathBuf>) {
    let entries = match fs::read_dir(dir) {
        Ok(e) => e,
        Err(_) => return,
    };
    for entry in entries.flatten() {
        let path = entry.path();
        if path.is_dir() {
            let name = entry.file_name();
            let name_str = name.to_string_lossy();
            if is_excluded_dir(&name_str)
                || name_str.starts_with('.')
                || name_str.starts_with('_')
            {
                continue;
            }
            walk_dir(&path, out);
        } else if path.extension().map_or(false, |e| e == "rs") {
            out.push(path);
        }
    }
}

// ── Per-file extraction ───────────────────────────────────────────────────────

struct ExtractedImpl {
    target: String,          // The type being impl'd (e.g. "Foo")
    trait_name: Option<String>, // If `impl Trait for Foo`, the trait name
    methods: Vec<MethodInfo>,
}

fn extract_file(path: &Path, deep: bool) -> Option<(FileEntry, Vec<ExtractedImpl>)> {
    let source = match fs::read_to_string(path) {
        Ok(s) => s,
        Err(e) => {
            eprintln!("Warning: could not read {}: {}", path.display(), e);
            return None;
        }
    };

    let syntax = match syn::parse_file(&source) {
        Ok(f) => f,
        Err(e) => {
            eprintln!("Warning: could not parse {}: {}", path.display(), e);
            return None;
        }
    };

    let mut entry = FileEntry::default();
    let mut impls = Vec::new();

    // Map class name → index in entry.classes for same-file impl attachment.
    let mut class_index: HashMap<String, usize> = HashMap::new();

    for item in &syntax.items {
        // Skip #[cfg(test)] modules entirely.
        match item {
            syn::Item::Mod(m) if is_cfg_test(&m.attrs) => continue,
            _ => {}
        }

        match item {
            syn::Item::Struct(s) => {
                if !is_pub(&s.vis) {
                    continue;
                }
                let mut ci = ClassInfo {
                    name: s.ident.to_string(),
                    kind: "struct".into(),
                    bases: Vec::new(),
                    line: line_of(s.ident.span()),
                    docstring: String::new(),
                    decorators: Vec::new(),
                    attributes: Vec::new(),
                    methods: Vec::new(),
                };
                if deep {
                    ci.docstring = extract_doc_comment(&s.attrs);
                    ci.decorators = extract_derives(&s.attrs);
                    // Extract fields.
                    if let syn::Fields::Named(ref fields) = s.fields {
                        for f in &fields.named {
                            if let Some(ref ident) = f.ident {
                                ci.attributes.push(AttributeInfo {
                                    name: ident.to_string(),
                                    ty: type_to_string(&f.ty),
                                    default: String::new(),
                                });
                            }
                        }
                    }
                }
                class_index.insert(ci.name.clone(), entry.classes.len());
                entry.classes.push(ci);
            }

            syn::Item::Enum(e) => {
                if !is_pub(&e.vis) {
                    continue;
                }
                let mut ci = ClassInfo {
                    name: e.ident.to_string(),
                    kind: "enum".into(),
                    bases: Vec::new(),
                    line: line_of(e.ident.span()),
                    docstring: String::new(),
                    decorators: Vec::new(),
                    attributes: Vec::new(),
                    methods: Vec::new(),
                };
                if deep {
                    ci.docstring = extract_doc_comment(&e.attrs);
                    ci.decorators = extract_derives(&e.attrs);
                    // Extract variants as attributes.
                    for v in &e.variants {
                        ci.attributes.push(AttributeInfo {
                            name: v.ident.to_string(),
                            ty: String::new(),
                            default: String::new(),
                        });
                    }
                }
                class_index.insert(ci.name.clone(), entry.classes.len());
                entry.classes.push(ci);
            }

            syn::Item::Trait(t) => {
                if !is_pub(&t.vis) {
                    continue;
                }
                let mut ci = ClassInfo {
                    name: t.ident.to_string(),
                    kind: "trait".into(),
                    bases: Vec::new(),
                    line: line_of(t.ident.span()),
                    docstring: String::new(),
                    decorators: Vec::new(),
                    attributes: Vec::new(),
                    methods: Vec::new(),
                };
                // Supertraits as bases.
                for bound in &t.supertraits {
                    if let syn::TypeParamBound::Trait(tb) = bound {
                        ci.bases.push(path_to_string(&tb.path));
                    }
                }
                if deep {
                    ci.docstring = extract_doc_comment(&t.attrs);
                    // Trait methods.
                    for item in &t.items {
                        if let syn::TraitItem::Fn(m) = item {
                            ci.methods.push(MethodInfo {
                                name: m.sig.ident.to_string(),
                                line: line_of(m.sig.ident.span()),
                                is_async: m.sig.asyncness.is_some(),
                                docstring: extract_doc_comment(&m.attrs),
                                decorators: Vec::new(),
                                params: extract_params(&m.sig),
                                return_type: return_type_to_string(&m.sig.output),
                            });
                        }
                    }
                }
                class_index.insert(ci.name.clone(), entry.classes.len());
                entry.classes.push(ci);
            }

            syn::Item::Type(t) => {
                if !is_pub(&t.vis) {
                    continue;
                }
                let mut ci = ClassInfo {
                    name: t.ident.to_string(),
                    kind: "type_alias".into(),
                    bases: Vec::new(),
                    line: line_of(t.ident.span()),
                    docstring: String::new(),
                    decorators: Vec::new(),
                    attributes: Vec::new(),
                    methods: Vec::new(),
                };
                if deep {
                    ci.docstring = extract_doc_comment(&t.attrs);
                }
                class_index.insert(ci.name.clone(), entry.classes.len());
                entry.classes.push(ci);
            }

            syn::Item::Fn(f) => {
                if !is_pub(&f.vis) {
                    continue;
                }
                let mut fi = FunctionInfo {
                    name: f.sig.ident.to_string(),
                    line: line_of(f.sig.ident.span()),
                    is_async: f.sig.asyncness.is_some(),
                    ..Default::default()
                };
                if deep {
                    fi.docstring = extract_doc_comment(&f.attrs);
                    fi.params = extract_params(&f.sig);
                    fi.return_type = return_type_to_string(&f.sig.output);
                }
                entry.functions.push(fi);
            }

            syn::Item::Impl(imp) => {
                // Determine the target type name.
                let target_name = if let syn::Type::Path(tp) = imp.self_ty.as_ref() {
                    tp.path.segments.last().map(|s| s.ident.to_string())
                } else {
                    None
                };
                let target_name = match target_name {
                    Some(n) => n,
                    None => continue,
                };

                // Trait name if `impl Trait for Type`.
                let trait_name = imp.trait_.as_ref().map(|(_, path, _)| path_to_string(path));

                let mut methods = Vec::new();
                for impl_item in &imp.items {
                    if let syn::ImplItem::Fn(m) = impl_item {
                        if !is_pub(&m.vis) && imp.trait_.is_none() {
                            // Skip private methods in inherent impls.
                            // Trait impl methods are always public.
                            continue;
                        }
                        let mut mi = MethodInfo {
                            name: m.sig.ident.to_string(),
                            line: line_of(m.sig.ident.span()),
                            is_async: m.sig.asyncness.is_some(),
                            ..Default::default()
                        };
                        if deep {
                            mi.docstring = extract_doc_comment(&m.attrs);
                            mi.params = extract_params(&m.sig);
                            mi.return_type = return_type_to_string(&m.sig.output);
                        }
                        methods.push(mi);
                    }
                }

                // Try same-file attachment first (deep mode).
                if deep {
                    if let Some(&idx) = class_index.get(&target_name) {
                        // Add trait to bases if this is a trait impl.
                        if let Some(ref tn) = trait_name {
                            if !entry.classes[idx].bases.contains(tn) {
                                entry.classes[idx].bases.push(tn.clone());
                            }
                        }
                        entry.classes[idx].methods.extend(methods.clone());
                        // Still record for cross-file if the methods might
                        // need to be merged, but the main attachment is done.
                        continue;
                    }
                }

                // Record for cross-file attachment or shallow-mode impl bases.
                if !deep {
                    // In shallow mode, just record trait as a base if type is in same file.
                    if let Some(ref tn) = trait_name {
                        if let Some(&idx) = class_index.get(&target_name) {
                            if !entry.classes[idx].bases.contains(tn) {
                                entry.classes[idx].bases.push(tn.clone());
                            }
                        }
                    }
                    // Shallow mode: methods as standalone functions with receiver.
                    for mi in &methods {
                        entry.functions.push(FunctionInfo {
                            name: mi.name.clone(),
                            line: mi.line,
                            is_async: mi.is_async,
                            receiver: target_name.clone(),
                            ..Default::default()
                        });
                    }
                } else {
                    // Deep mode but target not in same file — record for cross-file.
                    impls.push(ExtractedImpl {
                        target: target_name,
                        trait_name,
                        methods,
                    });
                }
            }

            syn::Item::Use(u) if deep => {
                extract_use_tree(&u.tree, &[], &mut entry.imports);
            }

            _ => {}
        }
    }

    Some((entry, impls))
}

/// Recursively extract use paths into ImportInfo entries.
fn extract_use_tree(tree: &syn::UseTree, prefix: &[String], out: &mut Vec<ImportInfo>) {
    match tree {
        syn::UseTree::Path(p) => {
            let mut new_prefix = prefix.to_vec();
            new_prefix.push(p.ident.to_string());
            extract_use_tree(&p.tree, &new_prefix, out);
        }
        syn::UseTree::Name(n) => {
            let name = n.ident.to_string();
            let mut parts = prefix.to_vec();
            parts.push(name.clone());
            out.push(ImportInfo {
                module: parts.join("::"),
                name,
                alias: None,
                import_type: "use".into(),
            });
        }
        syn::UseTree::Rename(r) => {
            let name = r.ident.to_string();
            let alias = r.rename.to_string();
            let mut parts = prefix.to_vec();
            parts.push(name.clone());
            out.push(ImportInfo {
                module: parts.join("::"),
                name,
                alias: Some(alias),
                import_type: "use".into(),
            });
        }
        syn::UseTree::Glob(_) => {
            let mut parts = prefix.to_vec();
            parts.push("*".into());
            out.push(ImportInfo {
                module: parts.join("::"),
                name: "*".into(),
                alias: None,
                import_type: "use".into(),
            });
        }
        syn::UseTree::Group(g) => {
            for tree in &g.items {
                extract_use_tree(tree, prefix, out);
            }
        }
    }
}

fn is_pub(vis: &syn::Visibility) -> bool {
    matches!(vis, syn::Visibility::Public(_))
}

// ── Arg parsing (manual, no clap needed) ──────────────────────────────────────

struct Args {
    src_dir: String,
    only_files: Option<Vec<String>>,
    deep: bool,
}

fn parse_args() -> Args {
    let args: Vec<String> = env::args().collect();
    let mut src_dir = ".".to_string();
    let mut only_files: Option<Vec<String>> = None;
    let mut deep = false;
    let mut i = 1;
    while i < args.len() {
        match args[i].as_str() {
            "--src-dir" => {
                i += 1;
                if i < args.len() {
                    src_dir = args[i].clone();
                }
            }
            "--only-files" => {
                i += 1;
                if i < args.len() {
                    only_files = Some(
                        args[i]
                            .split(',')
                            .map(|s| s.trim().to_string())
                            .filter(|s| !s.is_empty())
                            .collect(),
                    );
                }
            }
            "--deep" => {
                deep = true;
            }
            _ => {}
        }
        i += 1;
    }
    Args {
        src_dir,
        only_files,
        deep,
    }
}

// ── Main ──────────────────────────────────────────────────────────────────────

fn main() {
    let args = parse_args();
    let root = Path::new(&args.src_dir);

    // Collect files.
    let files: Vec<PathBuf> = if let Some(ref only) = args.only_files {
        let mut out = Vec::new();
        for f in only {
            let p = if Path::new(f).is_absolute() {
                PathBuf::from(f)
            } else {
                root.join(f)
            };
            if p.exists() && p.extension().map_or(false, |e| e == "rs") {
                out.push(p);
            }
        }
        out
    } else {
        collect_rs_files(root)
    };

    // Per-file extraction.
    let mut inventory: BTreeMap<String, FileEntry> = BTreeMap::new();
    let mut all_impls: Vec<(String, ExtractedImpl)> = Vec::new(); // (rel_path, impl)

    for file in &files {
        let (entry, impls) = match extract_file(file, args.deep) {
            Some(v) => v,
            None => continue,
        };
        let rel = match file.strip_prefix(root) {
            Ok(r) => r.to_string_lossy().to_string(),
            Err(_) => file.to_string_lossy().to_string(),
        };
        // Normalize path separators.
        let rel = rel.replace('\\', "/");
        for imp in impls {
            all_impls.push((rel.clone(), imp));
        }
        inventory.insert(rel, entry);
    }

    // ── Cross-file impl attachment (deep mode) ────────────────────────────────
    if args.deep {
        // Build: dir → type_name → (rel_path, class_idx)
        let mut dir_class_index: HashMap<String, HashMap<String, (String, usize)>> = HashMap::new();
        for (rel, entry) in &inventory {
            let dir = Path::new(rel)
                .parent()
                .map(|p| p.to_string_lossy().to_string())
                .unwrap_or_default();
            let map = dir_class_index.entry(dir).or_default();
            for (idx, cls) in entry.classes.iter().enumerate() {
                map.insert(cls.name.clone(), (rel.clone(), idx));
            }
        }

        for (impl_rel, ext_impl) in &all_impls {
            let dir = Path::new(impl_rel)
                .parent()
                .map(|p| p.to_string_lossy().to_string())
                .unwrap_or_default();
            if let Some(map) = dir_class_index.get(&dir) {
                if let Some((target_rel, target_idx)) = map.get(&ext_impl.target) {
                    if let Some(target_entry) = inventory.get_mut(target_rel) {
                        // Attach trait to bases.
                        if let Some(ref tn) = ext_impl.trait_name {
                            if !target_entry.classes[*target_idx].bases.contains(tn) {
                                target_entry.classes[*target_idx].bases.push(tn.clone());
                            }
                        }
                        // Attach methods.
                        target_entry.classes[*target_idx]
                            .methods
                            .extend(ext_impl.methods.clone());
                    }
                    continue;
                }
            }
            // Unresolvable — expose as standalone functions with receiver.
            if let Some(entry) = inventory.get_mut(impl_rel) {
                for mi in &ext_impl.methods {
                    entry.functions.push(FunctionInfo {
                        name: mi.name.clone(),
                        line: mi.line,
                        is_async: mi.is_async,
                        receiver: ext_impl.target.clone(),
                        docstring: mi.docstring.clone(),
                        decorators: mi.decorators.clone(),
                        params: mi.params.clone(),
                        return_type: mi.return_type.clone(),
                    });
                }
            }
        }
    }

    // Output JSON.
    let stdout = std::io::stdout();
    let mut handle = stdout.lock();
    if let Err(e) = serde_json::to_writer_pretty(&mut handle, &inventory) {
        eprintln!("Error encoding JSON: {}", e);
        std::process::exit(1);
    }
    let _ = writeln!(handle);
}
