use pyo3::exceptions::{PyAttributeError, PyValueError};
use pyo3::prelude::*;
use pyo3::sync::GILOnceCell;
use pyo3::types::{PyIterator, PyString, PyType};

use crate::utils::is_iterable_value;

static SAFE_CLASS: GILOnceCell<Py<PyAny>> = GILOnceCell::new();
static MARKUP_CLASS: GILOnceCell<Py<PyAny>> = GILOnceCell::new();

pub fn set_safe_class(py: Python<'_>, safe_class: Py<PyAny>) -> PyResult<()> {
    let _ = SAFE_CLASS.set(py, safe_class);
    Ok(())
}

pub fn safe_class(py: Python<'_>) -> PyResult<Bound<'_, PyAny>> {
    SAFE_CLASS
        .get(py)
        .map(|class| class.bind(py).clone())
        .ok_or_else(|| PyAttributeError::new_err("compone.safe is not initialized"))
}

pub fn make_safe_class(py: Python<'_>) -> PyResult<Py<PyAny>> {
    let markupsafe = py.import("markupsafe")?;
    let markup = markupsafe.getattr("Markup")?;
    let _ = MARKUP_CLASS.set(py, markup.clone().unbind());
    let builtins = py.import("builtins")?;
    let type_ = builtins.getattr("type")?;
    let attrs = pyo3::types::PyDict::new(py);
    attrs.set_item("__module__", "compone")?;
    attrs.set_item("__doc__", "Exclude a string from autoescaping using Markupsafe.")?;
    attrs.set_item("__repr__", wrap_pyfunction!(safe_repr, py)?)?;
    attrs.set_item("__html__", wrap_pyfunction!(safe_html, py)?)?;
    let bases = pyo3::types::PyTuple::new(py, [markup])?;
    type_.call1(("safe", bases, attrs)).map(Bound::unbind)
}

#[pyfunction]
fn safe_repr(value: &Bound<'_, PyAny>) -> PyResult<String> {
    let py = value.py();
    let builtins = py.import("builtins")?;
    let str_type = builtins.getattr("str")?;
    let str_repr = str_type.getattr("__repr__")?.call1((value,))?;
    let class_name = value.get_type().name()?;
    Ok(format!("{class_name}({})", str_repr.str()?))
}

#[pyfunction]
fn safe_html(value: &Bound<'_, PyAny>) -> PyResult<Py<PyAny>> {
    let class_name = value.get_type().name()?;
    Err(PyAttributeError::new_err(format!(
        "'{class_name}' object has no attribute '__html__'"
    )))
}

#[pyfunction]
pub fn escape(value: &Bound<'_, PyAny>) -> PyResult<Py<PyAny>> {
    escape_value(value)
}

pub fn safe_empty(py: Python<'_>) -> PyResult<Py<PyAny>> {
    safe_class(py)?.call0().map(Bound::unbind)
}

pub fn safe_from_string(py: Python<'_>, value: impl Into<String>) -> PyResult<Py<PyAny>> {
    safe_class(py)?.call1((value.into(),)).map(Bound::unbind)
}

pub fn escape_to_string(value: &Bound<'_, PyAny>) -> PyResult<String> {
    let escaped = escape_value(value)?;
    Ok(escaped.bind(value.py()).str()?.to_string_lossy().into_owned())
}

pub fn escape_value(value: &Bound<'_, PyAny>) -> PyResult<Py<PyAny>> {
    let py = value.py();
    let safe = safe_class(py)?;
    if value.is_instance(&safe)? {
        return Ok(value.clone().unbind());
    }
    if is_markup_value(py, value)? {
        return safe.call1((value,)).map(Bound::unbind);
    }

    if value.is_none() {
        return safe.call0().map(Bound::unbind);
    }

    if value.downcast::<PyType>().is_ok() {
        return Err(PyValueError::new_err(
            "Cannot escape classes. Instantiate the class first!",
        ));
    }

    if is_iterable_value(value)? {
        let mut escaped = String::new();
        for item in PyIterator::from_object(value)? {
            let item = item?;
            let escaped_item = escape_value(&item)?;
            escaped.push_str(&escaped_item.bind(py).str()?.to_string_lossy());
        }
        return safe.call1((escaped,)).map(Bound::unbind);
    }

    if let Ok(string) = value.downcast::<PyString>() {
        return safe.call1((escape_str(&string.to_string_lossy()),)).map(Bound::unbind);
    }

    let stringified = value.call_method0("__str__")?;
    if stringified.is_instance(&safe)? {
        return Ok(stringified.unbind());
    }
    if is_markup_value(py, &stringified)? {
        return safe.call1((stringified,)).map(Bound::unbind);
    }
    let string = stringified.str()?.to_string_lossy().into_owned();
    safe.call1((escape_str(&string),)).map(Bound::unbind)
}

fn is_markup_value(py: Python<'_>, value: &Bound<'_, PyAny>) -> PyResult<bool> {
    match MARKUP_CLASS.get(py) {
        Some(markup) => value.is_instance(markup.bind(py)),
        None => Ok(false),
    }
}

fn escape_str(value: &str) -> String {
    let mut escaped = String::with_capacity(value.len());
    for char_ in value.chars() {
        match char_ {
            '&' => escaped.push_str("&amp;"),
            '<' => escaped.push_str("&lt;"),
            '>' => escaped.push_str("&gt;"),
            '"' => escaped.push_str("&#34;"),
            '\'' => escaped.push_str("&#39;"),
            _ => escaped.push(char_),
        }
    }
    escaped
}
