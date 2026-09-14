//! Independent syntax-only observations; no macro expansion or target builds.
use proc_macro2::{TokenStream, TokenTree};
use quote::{quote, ToTokens};
use serde::Deserialize;
use serde_json::{json, Value};
use std::io::{self, Read};
use syn::spanned::Spanned;
use syn::visit_mut::{self, VisitMut};

#[derive(Deserialize)]
struct Job { mode: String, text: String }
struct Unparen;
impl VisitMut for Unparen {
    fn visit_type_mut(&mut self, node: &mut syn::Type) {
        visit_mut::visit_type_mut(self,node);
        if let syn::Type::Paren(inner)=node { *node=(*inner.elem).clone(); }
        if let syn::Type::Group(inner)=node { *node=(*inner.elem).clone(); }
    }
}
fn tokens(stream:TokenStream)->Value {
    Value::Array(stream.into_iter().map(|token|match token {
        TokenTree::Group(g)=>json!([format!("{:?}",g.delimiter()),tokens(g.stream())]),
        TokenTree::Ident(i)=>json!(["identifier",i.to_string()]),
        TokenTree::Punct(p)=>json!(["punct",p.as_char().to_string()]),
        TokenTree::Literal(l)=>json!(["literal",l.to_string()]),
    }).collect())
}
fn text<T:ToTokens>(value:&T)->String{ value.to_token_stream().to_string() }
fn params(sig:&syn::Signature)->Vec<Value>{
    sig.inputs.iter().map(|arg|match arg{
        syn::FnArg::Receiver(r)=>json!({"name":"self","type":text(&r.ty),"receiver":text(r)}),
        syn::FnArg::Typed(t)=>json!({"name":text(&t.pat),"type":text(&t.ty)}),
    }).collect()
}
fn function(sig:&syn::Signature,owner:&str)->Value{
    let ret=match &sig.output {syn::ReturnType::Default=>String::new(),syn::ReturnType::Type(_,t)=>text(t)};
    json!({"kind":if owner.is_empty(){"function"}else{"method"},"name":sig.ident.to_string(),"owner":owner,"line":sig.fn_token.span.start().line,"params":params(sig),"return_type":ret,"type_parameters":text(&sig.generics),"is_async":sig.asyncness.is_some()})
}
fn observe(raw:&str)->Result<Value,String>{
    let file=syn::parse_file(raw).map_err(|e|e.to_string())?;
    let mut records=vec![];let mut imports=vec![];
    for item in file.items{
        match item{
            syn::Item::Struct(s)=>{
                let name=s.ident.to_string();records.push(json!({"kind":"class","declaration_kind":"struct","name":name,"owner":"","line":s.ident.span().start().line}));
                for field in s.fields{if let Some(id)=field.ident{records.push(json!({"kind":"attribute","name":id.to_string(),"owner":name,"line":id.span().start().line,"type":text(&field.ty)}));}}
            },
            syn::Item::Enum(e)=>records.push(json!({"kind":"class","declaration_kind":"enum","name":e.ident.to_string(),"owner":"","line":e.ident.span().start().line})),
            syn::Item::Trait(t)=>{
                let name=t.ident.to_string();records.push(json!({"kind":"class","declaration_kind":"trait","name":name,"owner":"","line":t.ident.span().start().line}));
                for item in t.items{if let syn::TraitItem::Fn(f)=item{records.push(function(&f.sig,&name));}}
            },
            syn::Item::Type(t)=>records.push(json!({"kind":"class","declaration_kind":"type_alias","name":t.ident.to_string(),"owner":"","line":t.ident.span().start().line,"type":text(&t.ty)})),
            syn::Item::Fn(f)=>records.push(function(&f.sig,"")),
            syn::Item::Impl(i)=>{
                let owner=match &*i.self_ty{syn::Type::Path(p)=>p.path.segments.last().map(|s|s.ident.to_string()).unwrap_or_default(),_=>text(&i.self_ty)};
                for item in i.items{if let syn::ImplItem::Fn(f)=item{records.push(function(&f.sig,&owner));}}
            },
            syn::Item::Use(u)=>imports.push(json!({"module":text(&u.tree),"line":u.span().start().line})),
            _=>{},
        }
    }
    Ok(json!({"declarations":records,"imports":imports}))
}
fn run(job:Job)->Result<Value,String>{
    match job.mode.as_str(){
        "source"=>observe(&job.text),
        "type"=>{let mut ty:syn::Type=syn::parse_str(&job.text).map_err(|e|e.to_string())?;Unparen.visit_type_mut(&mut ty);Ok(tokens(quote!(#ty)))},
        "expr"=>{let expr:syn::Expr=syn::parse_str(&job.text).map_err(|e|e.to_string())?;Ok(tokens(quote!(#expr)))},
        _=>Err("unknown mode".to_owned()),
    }
}
fn main(){
    let mut raw=String::new();io::stdin().read_to_string(&mut raw).unwrap();
    let result=serde_json::from_str::<Vec<Job>>(&raw).map_err(|e|e.to_string()).and_then(|jobs|jobs.into_iter().map(run).collect::<Result<Vec<_>,_>>());
    match result{Ok(values)=>println!("{}",serde_json::to_string(&values).unwrap()),Err(e)=>{eprintln!("{e}");std::process::exit(2)}}
}
