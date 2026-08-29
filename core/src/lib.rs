#![allow(deprecated)]
#![allow(non_snake_case)]

mod component;
mod escape;
mod html;
mod htmx;
mod python_package;
mod robots;
mod utils;

use pyo3::prelude::*;
use pyo3::types::PyModule;

use component::{init_context_var, Component};
use escape::{escape as rust_escape, make_safe_class, safe_from_string, set_safe_class};
use html::{add_html_exports, make_xml_comment_class, CustomHTMLElement, Element, VoidElement};
use python_package::initialize_submodules;
use utils::{classes, is_iterable, snake_to_camel_case};

#[pymodule]
fn compone(m: &Bound<'_, PyModule>) -> PyResult<()> {
    let py = m.py();
    init_context_var(py)?;

    let safe_class = make_safe_class(py)?;
    set_safe_class(py, safe_class.clone_ref(py))?;

    m.add("safe", safe_class.clone_ref(py))?;
    m.add_function(wrap_pyfunction!(Component, m)?)?;
    m.add_function(wrap_pyfunction!(Element, m)?)?;
    m.add_function(wrap_pyfunction!(VoidElement, m)?)?;
    m.add_function(wrap_pyfunction!(CustomHTMLElement, m)?)?;
    m.add_function(wrap_pyfunction!(rust_escape, m)?)?;
    m.add_function(wrap_pyfunction!(is_iterable, m)?)?;
    m.add_function(wrap_pyfunction!(snake_to_camel_case, m)?)?;
    m.add_function(wrap_pyfunction!(classes, m)?)?;

    add_html_exports(py, m)?;
    m.add(
        "XML_10",
        safe_from_string(py, "<?xml version=\"1.0\" encoding=\"UTF-8\"?>")?,
    )?;
    m.add(
        "XML_11",
        safe_from_string(py, "<?xml version=\"1.1\" encoding=\"UTF-8\"?>")?,
    )?;
    m.add("Comment", make_xml_comment_class(py)?)?;

    initialize_submodules(py, m)?;
    m.add(
        "__all__",
        [
            "Component",
            "Element",
            "VoidElement",
            "escape",
            "safe",
            "html",
        ],
    )?;
    Ok(())
}
