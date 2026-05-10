use pyo3::exceptions::PyTypeError;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyIterator};
use std::collections::HashSet;

pub fn is_python_str(value: &Bound<'_, PyAny>) -> PyResult<bool> {
    let py = value.py();
    let builtins = py.import("builtins")?;
    let str_type = builtins.getattr("str")?;
    value.is_instance(&str_type)
}

pub fn is_python_bool(value: &Bound<'_, PyAny>) -> PyResult<bool> {
    let py = value.py();
    let builtins = py.import("builtins")?;
    let bool_type = builtins.getattr("bool")?;
    value.is_instance(&bool_type)
}

#[pyfunction]
pub fn is_iterable(value: &Bound<'_, PyAny>) -> PyResult<bool> {
    is_iterable_value(value)
}

pub fn is_iterable_value(value: &Bound<'_, PyAny>) -> PyResult<bool> {
    if is_python_str(value)? {
        return Ok(false);
    }

    match PyIterator::from_object(value) {
        Ok(_) => Ok(true),
        Err(err) if err.is_instance_of::<PyTypeError>(value.py()) => Ok(false),
        Err(err) => Err(err),
    }
}

#[pyfunction]
pub fn snake_to_camel_case(name: &str) -> String {
    let mut words = name.split('_');
    let Some(first) = words.next() else {
        return String::new();
    };

    let mut output = String::from(first);
    for word in words {
        let mut chars = word.chars();
        if let Some(first_char) = chars.next() {
            output.extend(first_char.to_uppercase());
            for char_ in chars {
                output.extend(char_.to_lowercase());
            }
        }
    }
    output
}

#[pyfunction]
#[pyo3(signature = (*args))]
pub fn classes(args: &Bound<'_, pyo3::types::PyTuple>) -> PyResult<Vec<String>> {
    let mut output = Vec::new();
    let mut seen = HashSet::new();

    for arg in args.iter() {
        let pieces = make_class_list(&arg)?;
        for piece in pieces {
            let stripped = piece.trim().to_string();
            if !stripped.is_empty() && seen.insert(stripped.clone()) {
                output.push(stripped);
            }
        }
    }

    Ok(output)
}

pub fn make_class_list(arg: &Bound<'_, PyAny>) -> PyResult<Vec<String>> {
    if !arg.is_truthy()? {
        return Ok(Vec::new());
    }

    if is_python_str(arg)? {
        let value: String = arg.extract()?;
        return Ok(value.split_whitespace().map(ToOwned::to_owned).collect());
    }

    if let Ok(dict) = arg.downcast::<PyDict>() {
        let mut pieces = Vec::new();
        for (class_name, enabled) in dict.iter() {
            if enabled.is_truthy()? {
                pieces.push(class_name.extract()?);
            }
        }
        return Ok(pieces);
    }

    if is_iterable_value(arg)? {
        let mut pieces = Vec::new();
        for elem in PyIterator::from_object(arg)? {
            let elem = elem?;
            if elem.is_truthy()? {
                let split = elem.call_method0("split")?;
                for class_name in split.try_iter()? {
                    pieces.push(class_name?.extract()?);
                }
            }
        }
        return Ok(pieces);
    }

    let type_repr = arg.get_type().repr()?.extract::<String>()?;
    let arg_repr = arg.repr()?.extract::<String>()?;
    Err(PyTypeError::new_err(format!(
        "Invalid class type: {type_repr} for {arg_repr}"
    )))
}
