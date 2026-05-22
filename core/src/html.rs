use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList, PyString, PyTuple};

use crate::component::{empty_param_specs, empty_signature, make_dynamic_class};
use crate::escape::{escape_to_string, safe_from_string};
use crate::utils::{classes, is_python_bool, is_python_keyword, is_python_str};

pub fn attrs_to_dict(attrs: &Bound<'_, PyAny>, target: &Bound<'_, PyDict>) -> PyResult<()> {
    for item in attrs.call_method0("items")?.try_iter()? {
        let item = item?;
        let pair = item.downcast::<PyTuple>()?;
        target.set_item(pair.get_item(0)?, pair.get_item(1)?)?;
    }
    Ok(())
}

pub fn parse_html_class(kwargs: &Bound<'_, PyDict>) -> PyResult<()> {
    let Some(class_value) = kwargs.get_item("class_")? else {
        return Ok(());
    };
    let args = PyTuple::new(kwargs.py(), [class_value])?;
    let parsed = classes(&args)?;
    if !parsed.is_empty() {
        kwargs.set_item("class_", parsed)?;
    }
    Ok(())
}

pub fn render_attributes(props: &Bound<'_, PyDict>) -> PyResult<String> {
    let py = props.py();
    let mut bool_args = Vec::new();
    let mut keyval_args = Vec::new();

    for (raw_key, raw_value) in props.iter() {
        let mut key: String = raw_key.extract()?;
        let mut value = raw_value;

        if is_python_str(&value)? {
            let value_string = value.str()?.to_string_lossy().into_owned();
            if value_string.contains('"') && value_string.contains('\'') {
                return Err(PyValueError::new_err(
                    "Both single and double quotes in attribute value",
                ));
            }
        }

        if let Some(no_underscore) = key.strip_suffix('_') {
            if is_python_keyword(no_underscore) {
                key = no_underscore.to_string();
            }
        }

        if value.downcast::<PyTuple>().is_ok() || value.downcast::<PyList>().is_ok() {
            let mut pieces = Vec::new();
            for elem in value.try_iter()? {
                pieces.push(elem?.str()?.to_string_lossy().into_owned());
            }
            let joined = pieces.join(" ");
            value = PyString::new(py, &joined).into_any();
        }

        let escaped_key = escape_to_string(&PyString::new(py, &key.replace('_', "-")).into_any())?;

        if is_python_bool(&value)? {
            let value_bool: bool = value.extract()?;
            if !value_bool {
                continue;
            }
            bool_args.push(escaped_key);
        } else {
            let escaped_value = escape_to_string(&value)?;
            let attr = if escaped_value.contains('"') {
                format!("{escaped_key}='{escaped_value}'")
            } else {
                format!("{escaped_key}=\"{escaped_value}\"")
            };
            keyval_args.push(attr);
        }
    }

    let bool_prefix = if bool_args.is_empty() { "" } else { " " };
    let bool_arguments = bool_args.join(" ");
    let keyval_prefix = if keyval_args.is_empty() { "" } else { " " };
    let keyval_arguments = keyval_args.join(" ");

    Ok(format!(
        "{bool_prefix}{bool_arguments}{keyval_prefix}{keyval_arguments}"
    ))
}

#[pyfunction]
#[allow(non_snake_case)]
pub fn Element(py: Python<'_>, name: &str) -> PyResult<Py<PyAny>> {
    make_element_class(py, name, &capitalize(name), "element", false, false, None, "compone.elements")
}

#[pyfunction]
#[allow(non_snake_case)]
pub fn VoidElement(py: Python<'_>, name: &str) -> PyResult<Py<PyAny>> {
    make_element_class(py, name, &capitalize(name), "void", false, false, None, "compone.elements")
}

#[pyfunction]
#[allow(non_snake_case)]
pub fn CustomHTMLElement(
    py: Python<'_>,
    name: &str,
    class_: &Bound<'_, PyAny>,
) -> PyResult<Py<PyAny>> {
    let builtins = py.import("builtins")?;
    let type_ = builtins.getattr("type")?;
    let attrs = PyDict::new(py);
    attrs.set_item("_name", name)?;
    let module: String = class_.getattr("__module__")?.extract()?;
    attrs.set_item("__module__", module)?;
    let bases = PyTuple::new(py, [class_])?;
    type_.call1((capitalize(name), bases, attrs)).map(Bound::unbind)
}

#[pyfunction]
#[allow(non_snake_case)]
pub fn MetaCharset(py: Python<'_>) -> PyResult<Py<PyAny>> {
    safe_from_string(py, "<meta charset=\"utf-8\">")
}

#[pyfunction(name = "_HTMLElement")]
pub fn html_element(py: Python<'_>, name: &str) -> PyResult<Py<PyAny>> {
    make_element_class(
        py,
        name,
        &capitalize(name),
        "element",
        true,
        false,
        None,
        "compone.html",
    )
}

#[pyfunction(name = "_VoidHTMLElement")]
pub fn void_html_element(py: Python<'_>, name: &str) -> PyResult<Py<PyAny>> {
    make_element_class(
        py,
        name,
        &capitalize(name),
        "void",
        true,
        false,
        None,
        "compone.html",
    )
}

pub fn make_element_class(
    py: Python<'_>,
    name: &str,
    class_name: &str,
    kind: &str,
    html: bool,
    list_only: bool,
    default_attrs: Option<&Bound<'_, PyDict>>,
    module: &str,
) -> PyResult<Py<PyAny>> {
    let attrs = PyDict::new(py);
    attrs.set_item("_kind", kind)?;
    attrs.set_item("_name", name)?;
    attrs.set_item("_html", html)?;
    attrs.set_item("_list_only", list_only)?;
    attrs.set_item("_sig", empty_signature(py)?)?;
    attrs.set_item("_param_specs", empty_param_specs(py)?)?;
    attrs.set_item("_positional_args", Vec::<String>::new())?;
    attrs.set_item("_var_keyword", "kwargs")?;
    match default_attrs {
        Some(default_attrs) => attrs.set_item("_attributes", default_attrs)?,
        None => attrs.set_item("_attributes", py.None())?,
    }
    make_dynamic_class(py, class_name, module, &attrs)
}

pub fn make_xml_comment_class(py: Python<'_>) -> PyResult<Py<PyAny>> {
    let attrs = PyDict::new(py);
    attrs.set_item("_kind", "comment")?;
    attrs.set_item("_name", "Comment")?;
    attrs.set_item("_html", false)?;
    attrs.set_item("_list_only", false)?;
    attrs.set_item("_sig", empty_signature(py)?)?;
    attrs.set_item("_param_specs", empty_param_specs(py)?)?;
    attrs.set_item("_positional_args", Vec::<String>::new())?;
    attrs.set_item("_var_keyword", "kwargs")?;
    attrs.set_item("_attributes", py.None())?;
    make_dynamic_class(py, "Comment", "compone.xml", &attrs)
}

fn capitalize(name: &str) -> String {
    let mut chars = name.chars();
    let Some(first) = chars.next() else {
        return String::new();
    };
    let mut output = String::new();
    output.extend(first.to_uppercase());
    output.push_str(&chars.as_str().to_lowercase());
    output
}

pub fn add_html_exports(_py: Python<'_>, module: &Bound<'_, PyModule>) -> PyResult<()> {
    module.add_function(wrap_pyfunction!(classes, module)?)?;
    module.add_function(wrap_pyfunction!(CustomHTMLElement, module)?)?;
    module.add_function(wrap_pyfunction!(MetaCharset, module)?)?;
    module.add_function(wrap_pyfunction!(html_element, module)?)?;
    module.add_function(wrap_pyfunction!(void_html_element, module)?)?;
    module.add_function(wrap_pyfunction!(list_html_element, module)?)?;
    module.add_function(wrap_pyfunction!(html_element_with_attributes, module)?)?;
    Ok(())
}

#[pyfunction(name = "_ListHTMLElement")]
pub fn list_html_element(py: Python<'_>, name: &str) -> PyResult<Py<PyAny>> {
    make_element_class(
        py,
        name,
        &capitalize(name),
        "element",
        true,
        true,
        None,
        "compone.html",
    )
}

#[pyfunction(name = "_HTMLElementWithAttributes")]
pub fn html_element_with_attributes(
    py: Python<'_>,
    name: &str,
    attrs: &Bound<'_, PyDict>,
) -> PyResult<Py<PyAny>> {
    make_element_class(
        py,
        name,
        &capitalize(name),
        "element",
        true,
        false,
        Some(attrs),
        "compone.html",
    )
}
