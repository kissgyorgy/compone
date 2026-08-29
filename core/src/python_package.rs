use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList, PyModule};

use crate::component::RustComponent;
use crate::html::{
    html_element, html_element_with_attributes, list_html_element, void_html_element,
};

#[derive(Clone, Copy)]
enum HTMLElementKind {
    Element,
    Void,
    List,
}

#[derive(Clone, Copy)]
struct HTMLElementDefinition {
    export: &'static str,
    tag: &'static str,
    category: &'static str,
    kind: HTMLElementKind,
}

static HTML_ELEMENTS: [HTMLElementDefinition; 113] = [
    element("Address", "address", "content_sectioning"),
    element("Article", "article", "content_sectioning"),
    element("Aside", "aside", "content_sectioning"),
    element("Footer", "footer", "content_sectioning"),
    element("Header", "header", "content_sectioning"),
    element("H1", "h1", "content_sectioning"),
    element("H2", "h2", "content_sectioning"),
    element("H3", "h3", "content_sectioning"),
    element("H4", "h4", "content_sectioning"),
    element("H5", "h5", "content_sectioning"),
    element("H6", "h6", "content_sectioning"),
    element("Main", "main", "content_sectioning"),
    element("Nav", "nav", "content_sectioning"),
    element("Section", "section", "content_sectioning"),
    void("Embed", "embed", "embedded"),
    element("Iframe", "iframe", "embedded"),
    element("Object", "object", "embedded"),
    element("Picture", "picture", "embedded"),
    element("Portal", "portal", "embedded"),
    void("Source", "source", "embedded"),
    element("Datalist", "datalist", "forms"),
    element("Fieldset", "fieldset", "forms"),
    element("Button", "button", "forms"),
    element("Form", "form", "forms"),
    void("Input", "input", "forms"),
    element("Label", "label", "forms"),
    element("Legend", "legend", "forms"),
    element("Meter", "meter", "forms"),
    element("Optgroup", "optgroup", "forms"),
    element("Option", "option", "forms"),
    element("Output", "output", "forms"),
    element("Progress", "progress", "forms"),
    element("Select", "select", "forms"),
    element("Textarea", "textarea", "forms"),
    element("A", "a", "inline_text"),
    element("Abbr", "abbr", "inline_text"),
    element("B", "b", "inline_text"),
    element("Bdi", "bdi", "inline_text"),
    element("Bdo", "bdo", "inline_text"),
    void("Br", "br", "inline_text"),
    element("Cite", "cite", "inline_text"),
    element("Code", "code", "inline_text"),
    element("Data", "data", "inline_text"),
    element("Del", "del", "inline_text"),
    element("Dfn", "dfn", "inline_text"),
    element("Em", "em", "inline_text"),
    element("I", "i", "inline_text"),
    element("Ins", "ins", "inline_text"),
    element("Kbd", "kbd", "inline_text"),
    element("Mark", "mark", "inline_text"),
    element("Q", "q", "inline_text"),
    element("Rp", "rp", "inline_text"),
    element("Rt", "rt", "inline_text"),
    element("Ruby", "ruby", "inline_text"),
    element("S", "s", "inline_text"),
    element("Samp", "samp", "inline_text"),
    element("Small", "small", "inline_text"),
    element("Span", "span", "inline_text"),
    element("Strong", "strong", "inline_text"),
    element("Sub", "sub", "inline_text"),
    element("Sup", "sup", "inline_text"),
    element("Time", "time", "inline_text"),
    element("U", "u", "inline_text"),
    element("Var", "var", "inline_text"),
    void("Wbr", "wbr", "inline_text"),
    element("Details", "details", "interactive"),
    element("Dialog", "dialog", "interactive"),
    element("Summary", "summary", "interactive"),
    element("Html", "html", "main"),
    element("Body", "body", "main"),
    element("Base", "base", "metadata"),
    element("Head", "head", "metadata"),
    void("Link", "link", "metadata"),
    void("Meta", "meta", "metadata"),
    element("Style", "style", "metadata"),
    element("Title", "title", "metadata"),
    void("Area", "area", "multimedia"),
    element("Audio", "audio", "multimedia"),
    void("Img", "img", "multimedia"),
    element("Map", "map", "multimedia"),
    void("Track", "track", "multimedia"),
    element("Video", "video", "multimedia"),
    element("Svg", "svg", "other"),
    element("Math", "math", "other"),
    element("Canvas", "canvas", "scripting"),
    element("Noscript", "noscript", "scripting"),
    element("Script", "script", "scripting"),
    element("Caption", "caption", "table"),
    element("Col", "col", "table"),
    element("Colgroup", "colgroup", "table"),
    element("Table", "table", "table"),
    element("Tbody", "tbody", "table"),
    element("Td", "td", "table"),
    element("Tfoot", "tfoot", "table"),
    element("Th", "th", "table"),
    element("Thead", "thead", "table"),
    element("Tr", "tr", "table"),
    element("Blockquote", "blockquote", "text_content"),
    element("Dd", "dd", "text_content"),
    element("Dl", "dl", "text_content"),
    element("Dt", "dt", "text_content"),
    element("Div", "div", "text_content"),
    element("Figcaption", "figcaption", "text_content"),
    element("Figure", "figure", "text_content"),
    void("Hr", "hr", "text_content"),
    element("Menu", "menu", "text_content"),
    element("P", "p", "text_content"),
    element("Pre", "pre", "text_content"),
    element("Li", "li", "text_content"),
    list("Ul", "ul", "text_content"),
    list("Ol", "ol", "text_content"),
    element("Slot", "slot", "web_components"),
    element("Template", "template", "web_components"),
];

static HTML_CATEGORIES: [&str; 13] = [
    "content_sectioning",
    "embedded",
    "forms",
    "inline_text",
    "interactive",
    "main",
    "metadata",
    "multimedia",
    "other",
    "scripting",
    "table",
    "text_content",
    "web_components",
];

const fn element(
    export: &'static str,
    tag: &'static str,
    category: &'static str,
) -> HTMLElementDefinition {
    HTMLElementDefinition {
        export,
        tag,
        category,
        kind: HTMLElementKind::Element,
    }
}

const fn void(
    export: &'static str,
    tag: &'static str,
    category: &'static str,
) -> HTMLElementDefinition {
    HTMLElementDefinition {
        export,
        tag,
        category,
        kind: HTMLElementKind::Void,
    }
}

const fn list(
    export: &'static str,
    tag: &'static str,
    category: &'static str,
) -> HTMLElementDefinition {
    HTMLElementDefinition {
        export,
        tag,
        category,
        kind: HTMLElementKind::List,
    }
}

pub fn initialize_submodules(py: Python<'_>, root: &Bound<'_, PyModule>) -> PyResult<()> {
    root.add("__path__", PyList::empty(py))?;

    let html = make_package(py, "compone.html")?;
    add_aliases(
        &html,
        root,
        &["CustomHTMLElement", "MetaCharset", "classes"],
    )?;
    add_html_elements(py, &html)?;
    register_child(py, root, "html", &html)?;
    add_html_submodules(py, &html)?;

    let component = PyModule::new(py, "compone.component")?;
    add_aliases(&component, root, &["Component"])?;
    component.add("CompSelf", py.get_type::<RustComponent>())?;
    component.add("ChildSelf", py.get_type::<RustComponent>())?;
    register_child(py, root, "component", &component)?;

    let elements = PyModule::new(py, "compone.elements")?;
    add_aliases(&elements, root, &["Element", "VoidElement"])?;
    register_child(py, root, "elements", &elements)?;

    let utils = PyModule::new(py, "compone.utils")?;
    add_aliases(
        &utils,
        root,
        &["classes", "is_iterable", "snake_to_camel_case"],
    )?;
    register_child(py, root, "utils", &utils)?;

    let xml = PyModule::new(py, "compone.xml")?;
    add_aliases(&xml, root, &["XML_10", "XML_11", "Comment"])?;
    register_child(py, root, "xml", &xml)?;

    crate::htmx::add_module(py, root)?;
    crate::robots::add_module(py, root)?;
    Ok(())
}

fn add_html_elements(py: Python<'_>, html: &Bound<'_, PyModule>) -> PyResult<()> {
    for definition in &HTML_ELEMENTS {
        let class = match definition.kind {
            HTMLElementKind::Element => html_element(py, definition.tag)?,
            HTMLElementKind::Void => void_html_element(py, definition.tag)?,
            HTMLElementKind::List => list_html_element(py, definition.tag)?,
        };
        html.add(definition.export, class)?;
    }

    for (export, button_type) in [
        ("ButtonButton", "button"),
        ("ResetButton", "reset"),
        ("SubmitButton", "submit"),
    ] {
        let attrs = PyDict::new(py);
        attrs.set_item("type", button_type)?;
        html.add(
            export,
            html_element_with_attributes(py, "button", export, &attrs)?,
        )?;
    }
    Ok(())
}

fn add_html_submodules(py: Python<'_>, html: &Bound<'_, PyModule>) -> PyResult<()> {
    let elements = make_package(py, "compone.html.elements")?;
    register_child(py, html, "elements", &elements)?;

    for category in &HTML_CATEGORIES {
        let full_name = format!("compone.html.elements.{category}");
        let module = PyModule::new(py, &full_name)?;
        for definition in HTML_ELEMENTS
            .iter()
            .filter(|definition| definition.category == *category)
        {
            module.add(definition.export, html.getattr(definition.export)?)?;
        }
        if *category == "forms" {
            add_aliases(
                &module,
                html,
                &["ButtonButton", "ResetButton", "SubmitButton"],
            )?;
        } else if *category == "metadata" {
            add_aliases(&module, html, &["MetaCharset"])?;
        }
        register_child(py, &elements, category, &module)?;
    }

    let helpers = PyModule::new(py, "compone.html.helpers")?;
    add_aliases(&helpers, html, &["classes"])?;
    register_child(py, html, "helpers", &helpers)?;

    let html_elements = PyModule::new(py, "compone.html.html_elements")?;
    add_aliases(&html_elements, html, &["CustomHTMLElement"])?;
    register_child(py, html, "html_elements", &html_elements)?;
    Ok(())
}

pub(crate) fn make_package<'py>(
    py: Python<'py>,
    name: &str,
) -> PyResult<Bound<'py, PyModule>> {
    let module = PyModule::new(py, name)?;
    module.add("__path__", PyList::empty(py))?;
    Ok(module)
}

pub(crate) fn register_child(
    py: Python<'_>,
    parent: &Bound<'_, PyModule>,
    short_name: &str,
    child: &Bound<'_, PyModule>,
) -> PyResult<()> {
    let full_name = child.name()?;
    register_alias(py, full_name.to_str()?, child)?;
    parent.add(short_name, child)?;
    Ok(())
}

fn register_alias(py: Python<'_>, name: &str, module: &Bound<'_, PyModule>) -> PyResult<()> {
    py.import("sys")?
        .getattr("modules")?
        .set_item(name, module)?;
    Ok(())
}

pub(crate) fn add_aliases(
    target: &Bound<'_, PyModule>,
    source: &Bound<'_, PyModule>,
    names: &[&str],
) -> PyResult<()> {
    for name in names {
        target.add(*name, source.getattr(*name)?)?;
    }
    Ok(())
}
