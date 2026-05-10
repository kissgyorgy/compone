use std::collections::HashSet;

use pyo3::exceptions::{PyAssertionError, PyAttributeError, PySyntaxError, PyTypeError, PyValueError};
use pyo3::prelude::*;
use pyo3::sync::GILOnceCell;
use pyo3::types::{PyDict, PyIterator, PyList, PyTuple, PyType};

use crate::escape::{escape_value, safe_empty, safe_from_string};
use crate::html::{attrs_to_dict, parse_html_class, render_attributes};
use crate::utils::is_iterable_value;

static LAST_PARENT: GILOnceCell<Py<PyAny>> = GILOnceCell::new();

pub fn init_context_var(py: Python<'_>) -> PyResult<()> {
    let contextvars = py.import("contextvars")?;
    let default = PyTuple::new(py, [py.None(), py.None()])?;
    let var = contextvars
        .getattr("ContextVar")?
        .call1(("last_parent",))?;
    var.call_method1("set", (default,))?;
    let _ = LAST_PARENT.set(py, var.unbind());
    Ok(())
}

fn last_parent(py: Python<'_>) -> PyResult<Bound<'_, PyAny>> {
    LAST_PARENT
        .get(py)
        .map(|var| var.bind(py).clone())
        .ok_or_else(|| PyAttributeError::new_err("last_parent is not initialized"))
}

#[pyclass(name = "_ComponentBase", subclass)]
pub struct RustComponent {
    bound_args: Option<Py<PyAny>>,
    children: Vec<Py<PyAny>>,
    original_kwargs: Option<Py<PyDict>>,
    parent_frame_id: Option<usize>,
    parent: Option<Py<PyAny>>,
    user_instance: Option<Py<PyAny>>,
}

#[pymethods]
impl RustComponent {
    #[new]
    #[pyo3(signature = (*_args, **_kwargs))]
    fn new(_args: &Bound<'_, PyTuple>, _kwargs: Option<&Bound<'_, PyDict>>) -> Self {
        Self {
            bound_args: None,
            children: Vec::new(),
            original_kwargs: None,
            parent_frame_id: None,
            parent: None,
            user_instance: None,
        }
    }

    #[pyo3(signature = (*args, **kwargs))]
    fn __init__(
        slf: Bound<'_, Self>,
        args: &Bound<'_, PyTuple>,
        kwargs: Option<&Bound<'_, PyDict>>,
    ) -> PyResult<()> {
        initialize_instance(&slf, args, kwargs)
    }

    #[getter]
    fn _bound_args(slf: Bound<'_, Self>) -> PyResult<Py<PyAny>> {
        get_bound_args_object(&slf)
    }

    #[getter]
    fn _children(slf: Bound<'_, Self>) -> PyResult<Py<PyAny>> {
        let py = slf.py();
        let borrowed = slf.borrow();
        let items: Vec<Bound<'_, PyAny>> = borrowed
            .children
            .iter()
            .map(|item| item.bind(py).clone())
            .collect();
        Ok(PyTuple::new(py, items)?.unbind().into_any())
    }

    #[setter]
    fn set__children(slf: Bound<'_, Self>, value: &Bound<'_, PyAny>) -> PyResult<()> {
        let children = children_from_value(value)?;
        slf.borrow_mut().children = children;
        Ok(())
    }

    #[getter]
    fn children(slf: Bound<'_, Self>) -> PyResult<Py<PyAny>> {
        RustComponent::_children(slf)
    }

    #[getter]
    fn props(slf: Bound<'_, Self>) -> PyResult<Py<PyAny>> {
        let props = build_props_dict(&slf)?;
        let py = slf.py();
        let types = py.import("types")?;
        let proxy = types.getattr("MappingProxyType")?.call1((props,))?;
        Ok(proxy.unbind())
    }

    #[getter]
    fn _original_kwargs(slf: Bound<'_, Self>) -> PyResult<Py<PyAny>> {
        let py = slf.py();
        let borrowed = slf.borrow();
        match &borrowed.original_kwargs {
            Some(kwargs) => Ok(kwargs.clone_ref(py).into_any()),
            None => Ok(py.None()),
        }
    }

    #[staticmethod]
    fn _check_keywords(func: &Bound<'_, PyAny>, kwargs: &Bound<'_, PyDict>) -> PyResult<()> {
        check_keywords(func, Some(kwargs))
    }

    #[pyo3(signature = (*args, **kwargs))]
    fn _bind_args(
        slf: Bound<'_, Self>,
        args: &Bound<'_, PyTuple>,
        kwargs: Option<&Bound<'_, PyDict>>,
    ) -> PyResult<Py<PyAny>> {
        Ok(bind_args(slf.as_any(), args, kwargs)?.unbind())
    }

    fn _check_common_props(slf: Bound<'_, Self>, kwargs: &Bound<'_, PyDict>) -> PyResult<()> {
        check_common_props(&slf, kwargs)
    }

    #[pyo3(signature = (**kwargs))]
    fn replace(slf: Bound<'_, Self>, kwargs: Option<&Bound<'_, PyDict>>) -> PyResult<Py<PyAny>> {
        let empty_kwargs;
        let kwargs = match kwargs {
            Some(kwargs) => kwargs,
            None => {
                empty_kwargs = PyDict::new(slf.py());
                &empty_kwargs
            }
        };
        let func = slf.as_any().getattr("replace")?;
        check_keywords(&func, Some(kwargs))?;
        check_common_props(&slf, kwargs)?;
        make_new(&slf, kwargs)
    }

    #[pyo3(signature = (**kwargs))]
    fn append(slf: Bound<'_, Self>, kwargs: Option<&Bound<'_, PyDict>>) -> PyResult<Py<PyAny>> {
        let py = slf.py();
        let empty_kwargs;
        let kwargs = match kwargs {
            Some(kwargs) => kwargs,
            None => {
                empty_kwargs = PyDict::new(py);
                &empty_kwargs
            }
        };
        let kwargs = prepare_append_kwargs(slf.as_any(), kwargs)?;
        let func = slf.as_any().getattr("append")?;
        check_keywords(&func, Some(&kwargs))?;
        check_common_props(&slf, &kwargs)?;

        let props = build_props_dict(&slf)?;
        let operator = py.import("operator")?;
        let appended = PyDict::new(py);
        for (key, value) in kwargs.iter() {
            let old_value = props.get_item(&key)?.ok_or_else(|| {
                PyTypeError::new_err("append expected an existing prop, but none was found")
            })?;
            let new_value = operator.call_method1("add", (old_value, value))?;
            appended.set_item(key, new_value)?;
        }
        make_new(&slf, &appended)
    }

    fn _make_new(
        slf: Bound<'_, Self>,
        new_arguments: &Bound<'_, PyDict>,
    ) -> PyResult<Py<PyAny>> {
        make_new(&slf, new_arguments)
    }

    fn __enter__(slf: Bound<'_, Self>) -> PyResult<Py<PyAny>> {
        let py = slf.py();
        let value = last_parent(py)?.call_method0("get")?;
        let pair = value.downcast::<PyTuple>()?;
        let frame_obj = pair.get_item(0)?;
        let parent_obj = pair.get_item(1)?;
        let parent_frame_id = if frame_obj.is_none() {
            None
        } else {
            Some(frame_obj.extract()?)
        };
        let parent = if parent_obj.is_none() {
            None
        } else {
            Some(parent_obj.unbind())
        };
        let current_frame_id = current_frame_id(py)?;

        {
            let mut borrowed = slf.borrow_mut();
            borrowed.parent_frame_id = parent_frame_id;
            borrowed.parent = parent;
        }

        let current = slf.as_any().clone().unbind();
        let state = PyTuple::new(py, [current_frame_id.into_py(py), current])?;
        last_parent(py)?.call_method1("set", (state,))?;
        Ok(slf.as_any().clone().unbind())
    }

    #[pyo3(signature = (_exc_type=None, _exc_val=None, _exc_tb=None))]
    fn __exit__(
        slf: Bound<'_, Self>,
        _exc_type: Option<&Bound<'_, PyAny>>,
        _exc_val: Option<&Bound<'_, PyAny>>,
        _exc_tb: Option<&Bound<'_, PyAny>>,
    ) -> PyResult<()> {
        let py = slf.py();
        let current_frame_id = current_frame_id(py)?;
        let (parent_frame_id, parent) = {
            let borrowed = slf.borrow();
            (
                borrowed.parent_frame_id,
                borrowed.parent.as_ref().map(|parent| parent.clone_ref(py)),
            )
        };

        if let (Some(expected), Some(parent)) = (parent_frame_id, &parent) {
            if expected == current_frame_id {
                parent.bind(py).call_method1("__iadd__", (slf.as_any(),))?;
            }
        }

        let frame_obj = match parent_frame_id {
            Some(frame_id) => frame_id.into_py(py),
            None => py.None(),
        };
        let parent_obj = parent.unwrap_or_else(|| py.None());
        let state = PyTuple::new(py, [frame_obj, parent_obj])?;
        last_parent(py)?.call_method1("set", (state,))?;
        Ok(())
    }

    fn __iadd__(slf: Bound<'_, Self>, other: &Bound<'_, PyAny>) -> PyResult<()> {
        slf.borrow_mut().children.push(other.clone().unbind());
        Ok(())
    }

    #[classmethod]
    fn __class_getitem__(cls: &Bound<'_, PyType>, key: &Bound<'_, PyAny>) -> PyResult<Py<PyAny>> {
        let instance = cls.call0()?;
        instance.call_method1("__getitem__", (key,)).map(Bound::unbind)
    }

    fn __getitem__(slf: Bound<'_, Self>, children: &Bound<'_, PyAny>) -> PyResult<Py<PyAny>> {
        if !slf.borrow().children.is_empty() {
            return Err(PyValueError::new_err(
                "Component already has children, use the += operator if you want to add more.",
            ));
        }

        let child_items = children_from_value(children)?;
        validate_list_children(slf.as_any(), &child_items)?;
        let new = make_new_with_same_arguments(&slf)?;
        let tuple = PyTuple::new(
            slf.py(),
            child_items.iter().map(|child| child.bind(slf.py()).clone()),
        )?;
        new.bind(slf.py()).call_method1("_replace_children", (tuple,))?;
        Ok(new)
    }

    fn _replace_children(&mut self, children: &Bound<'_, PyTuple>) -> PyResult<()> {
        self.children = children.iter().map(Bound::unbind).collect();
        Ok(())
    }

    fn __repr__(slf: Bound<'_, Self>) -> PyResult<String> {
        let props = build_props_dict(&slf)?;
        let proplist = if props.is_empty() {
            String::new()
        } else {
            let mut pieces = Vec::with_capacity(props.len());
            for (key, value) in props.iter() {
                let key_str: String = key.extract()?;
                let value_repr: String = value.repr()?.extract()?;
                pieces.push(format!("{key_str}={value_repr}"));
            }
            pieces.join(", ")
        };
        let class_name = slf.as_any().get_type().name()?;
        Ok(format!("<{class_name}({proplist})>"))
    }

    fn __iter__(slf: Bound<'_, Self>) -> PyResult<Py<PyAny>> {
        let class_name = slf.as_any().get_type().name()?;
        Err(PyTypeError::new_err(format!(
            "{class_name} object is not iterable"
        )))
    }

    fn __str__(slf: Bound<'_, Self>) -> PyResult<Py<PyAny>> {
        render_instance(&slf)
    }

    fn __eq__(slf: Bound<'_, Self>, other: &Bound<'_, PyAny>) -> PyResult<Py<PyAny>> {
        if !other.is_instance(&slf.py().get_type::<RustComponent>())? {
            return Ok(slf.py().NotImplemented());
        }

        let kind = class_kind(slf.as_any())?;
        let other_kind = class_kind(other)?;
        let result = if kind == "void" && other_kind == "void" {
            let self_name = class_string_attr(slf.as_any(), "_name")?;
            let other_name = class_string_attr(other, "_name")?;
            let self_kwargs = RustComponent::_original_kwargs(slf.clone())?
                .bind(other.py())
                .clone();
            let other_kwargs = other.getattr("_original_kwargs")?;
            self_name == other_name && self_kwargs.eq(&other_kwargs)?
        } else {
            let self_str = render_instance(&slf)?;
            let other_str = other.call_method0("__str__")?;
            self_str.bind(other.py()).eq(&other_str)?
        };
        Ok(result.into_py(slf.py()))
    }

    fn __mul__(slf: Bound<'_, Self>, other: &Bound<'_, PyAny>) -> PyResult<Py<PyAny>> {
        if !other.is_instance(&slf.py().get_type::<pyo3::types::PyInt>())? {
            return Ok(slf.py().NotImplemented());
        }
        let count: isize = other.extract()?;
        let rendered = render_instance(&slf)?;
        let rendered = rendered.bind(slf.py());
        let repeated = rendered.call_method1("__mul__", (count,))?;
        Ok(repeated.unbind())
    }
}

fn initialize_instance(
    slf: &Bound<'_, RustComponent>,
    args: &Bound<'_, PyTuple>,
    kwargs: Option<&Bound<'_, PyDict>>,
) -> PyResult<()> {
    let py = slf.py();
    let prepared_kwargs = prepare_init_kwargs(slf.as_any(), kwargs)?;
    let keyword_func = keyword_check_target(slf.as_any())?;
    check_keywords(&keyword_func, Some(&prepared_kwargs))?;
    let bound_args = bind_args(slf.as_any(), args, Some(&prepared_kwargs))?;

    let original_kwargs = PyDict::new(py);
    for (key, value) in prepared_kwargs.iter() {
        original_kwargs.set_item(key, value)?;
    }

    let mut borrowed = slf.borrow_mut();
    borrowed.bound_args = Some(bound_args.unbind());
    borrowed.children.clear();
    borrowed.original_kwargs = Some(original_kwargs.unbind());
    borrowed.parent_frame_id = None;
    borrowed.parent = None;
    borrowed.user_instance = None;
    Ok(())
}

fn prepare_init_kwargs<'py>(
    obj: &Bound<'py, PyAny>,
    kwargs: Option<&Bound<'py, PyDict>>,
) -> PyResult<Bound<'py, PyDict>> {
    let py = obj.py();
    let prepared = PyDict::new(py);
    if let Some(kwargs) = kwargs {
        for (key, value) in kwargs.iter() {
            prepared.set_item(key, value)?;
        }
    }

    let kind = class_kind(obj)?;
    if kind == "element" || kind == "void" {
        if class_bool_attr(obj, "_html")? {
            parse_html_class(&prepared)?;
        }
        if let Some(attrs) = class_optional_attr(obj, "_attributes")? {
            attrs_to_dict(&attrs.bind(py), &prepared)?;
        }
    }
    Ok(prepared)
}

fn prepare_append_kwargs<'py>(
    obj: &Bound<'py, PyAny>,
    kwargs: &Bound<'py, PyDict>,
) -> PyResult<Bound<'py, PyDict>> {
    let py = obj.py();
    let prepared = PyDict::new(py);
    for (key, value) in kwargs.iter() {
        prepared.set_item(key, value)?;
    }
    let kind = class_kind(obj)?;
    if (kind == "element" || kind == "void") && class_bool_attr(obj, "_html")? {
        parse_html_class(&prepared)?;
    }
    Ok(prepared)
}

fn keyword_check_target<'py>(obj: &Bound<'py, PyAny>) -> PyResult<Bound<'py, PyAny>> {
    let cls = obj.get_type();
    match class_kind(obj)?.as_str() {
        "func" => cls.getattr("_func"),
        "class" => cls.getattr("_render_func"),
        _ => Ok(cls.into_any()),
    }
}

fn render_instance(slf: &Bound<'_, RustComponent>) -> PyResult<Py<PyAny>> {
    let py = slf.py();
    let kind = class_kind(slf.as_any())?;
    match kind.as_str() {
        "void" => render_void(slf),
        "element" => render_element(slf),
        "func" => render_func_component(slf),
        "class" => render_class_component(slf),
        "comment" => render_comment(slf),
        _ => safe_empty(py),
    }
}

fn render_children(slf: &Bound<'_, RustComponent>) -> PyResult<Py<PyAny>> {
    let py = slf.py();
    if slf.borrow().children.is_empty() {
        return safe_empty(py);
    }
    let tuple = PyTuple::new(
        py,
        slf.borrow().children.iter().map(|child| child.bind(py).clone()),
    )?;
    escape_value(&tuple.into_any())
}

fn render_element(slf: &Bound<'_, RustComponent>) -> PyResult<Py<PyAny>> {
    let name = class_string_attr(slf.as_any(), "_name")?;
    let props = build_props_dict(slf)?;
    let attributes = render_attributes(&props)?;
    let children = render_children(slf)?;
    safe_from_string(
        slf.py(),
        format!(
            "<{name}{attributes}>{}</{name}>",
            children.bind(slf.py()).str()?
        ),
    )
}

fn render_void(slf: &Bound<'_, RustComponent>) -> PyResult<Py<PyAny>> {
    let name = class_string_attr(slf.as_any(), "_name")?;
    let props = build_props_dict(slf)?;
    let attributes = render_attributes(&props)?;
    safe_from_string(slf.py(), format!("<{name}{attributes} />"))
}

fn render_func_component(slf: &Bound<'_, RustComponent>) -> PyResult<Py<PyAny>> {
    let py = slf.py();
    let cls = slf.as_any().get_type();
    let func = cls.getattr("_func")?;
    let pass_children = class_bool_attr(slf.as_any(), "_pass_children")?;
    let bound_args_obj = get_bound_args_object(slf)?;
    let bound_args = bound_args_obj.bind(py);
    let args = bound_args.getattr("args")?;
    let args = args.downcast::<PyTuple>()?;
    let kwargs = bound_args.getattr("kwargs")?;
    let kwargs = kwargs.downcast::<PyDict>()?;
    let call_kwargs = PyDict::new(py);
    for (key, value) in kwargs.iter() {
        call_kwargs.set_item(key, value)?;
    }
    if pass_children {
        call_kwargs.set_item("children", render_children(slf)?)?;
    }
    let content = func.call(args, Some(&call_kwargs))?;
    escape_value(&content)
}

fn render_class_component(slf: &Bound<'_, RustComponent>) -> PyResult<Py<PyAny>> {
    let py = slf.py();
    let pass_children = class_bool_attr(slf.as_any(), "_pass_children")?;
    let user_instance = get_or_create_user_instance(slf)?;
    let content = if pass_children {
        user_instance
            .bind(py)
            .call_method1("render", (render_children(slf)?,))?
    } else {
        user_instance.bind(py).call_method0("render")?
    };
    escape_value(&content)
}

fn render_comment(slf: &Bound<'_, RustComponent>) -> PyResult<Py<PyAny>> {
    let py = slf.py();
    let mut content = String::new();
    for child in &slf.borrow().children {
        content.push_str(&child.bind(py).str()?.to_string_lossy());
    }
    safe_from_string(py, format!("<-- {content} -->"))
}

fn get_or_create_user_instance(slf: &Bound<'_, RustComponent>) -> PyResult<Py<PyAny>> {
    let py = slf.py();
    if let Some(instance) = &slf.borrow().user_instance {
        return Ok(instance.clone_ref(py));
    }

    let cls = slf.as_any().get_type();
    let user_class = cls.getattr("_user_class")?;
    let bound_args_obj = get_bound_args_object(slf)?;
    let bound_args = bound_args_obj.bind(py);
    let args = bound_args.getattr("args")?;
    let args = args.downcast::<PyTuple>()?;
    let kwargs = bound_args.getattr("kwargs")?;
    let kwargs = kwargs.downcast::<PyDict>()?;
    let instance = user_class.call(args, Some(kwargs))?.unbind();
    slf.borrow_mut().user_instance = Some(instance.clone_ref(py));
    Ok(instance)
}

fn validate_list_children(obj: &Bound<'_, PyAny>, children: &[Py<PyAny>]) -> PyResult<()> {
    if !class_bool_attr(obj, "_list_only")? {
        return Ok(());
    }

    let py = obj.py();
    let error_message = "List element children must be <li>";
    for child in children {
        let rendered = child.bind(py).str()?.to_string_lossy().trim().to_string();
        if !(rendered.starts_with("<li") && rendered.ends_with("</li>")) {
            return Err(PyAssertionError::new_err(error_message));
        }
    }
    Ok(())
}

fn children_from_value(value: &Bound<'_, PyAny>) -> PyResult<Vec<Py<PyAny>>> {
    if !is_iterable_value(value)? {
        return Ok(vec![value.clone().unbind()]);
    }

    let mut children = Vec::new();
    for child in PyIterator::from_object(value)? {
        children.push(child?.unbind());
    }
    Ok(children)
}

fn current_frame_id(py: Python<'_>) -> PyResult<usize> {
    let sys = py.import("sys")?;
    let builtins = py.import("builtins")?;
    let frame = sys.call_method1("_getframe", (0,))?;
    builtins.getattr("id")?.call1((frame,))?.extract()
}

pub fn get_bound_args_object(slf: &Bound<'_, RustComponent>) -> PyResult<Py<PyAny>> {
    let py = slf.py();
    let borrowed = slf.borrow();
    borrowed
        .bound_args
        .as_ref()
        .map(|obj| obj.clone_ref(py))
        .ok_or_else(|| {
            PyAttributeError::new_err("'_ComponentBase' object has no attribute '_bound_args'")
        })
}

fn bind_args<'py>(
    obj: &Bound<'py, PyAny>,
    args: &Bound<'py, PyTuple>,
    kwargs: Option<&Bound<'py, PyDict>>,
) -> PyResult<Bound<'py, PyAny>> {
    let sig = obj.get_type().getattr("_sig")?;
    let bound = sig.call_method("bind", args, kwargs)?;
    bound.call_method0("apply_defaults")?;
    Ok(bound)
}

pub fn check_keywords(func: &Bound<'_, PyAny>, kwargs: Option<&Bound<'_, PyDict>>) -> PyResult<()> {
    let Some(kwargs) = kwargs else {
        return Ok(());
    };
    if kwargs.is_empty() {
        return Ok(());
    }

    let py = kwargs.py();
    let keyword = py.import("keyword")?;
    let is_keyword = keyword.getattr("iskeyword")?;

    for key in kwargs.keys() {
        let name: String = key.extract()?;
        let keyword_result: bool = is_keyword.call1((&name,))?.extract()?;
        if keyword_result {
            let func_name = match func.getattr("__qualname__") {
                Ok(value) if !value.is_none() => value.extract()?,
                _ => match func.getattr("__name__") {
                    Ok(value) if !value.is_none() => value.extract()?,
                    _ => String::from("<unknown>"),
                },
            };
            let module_name = match func.getattr("__module__") {
                Ok(value) if !value.is_none() => value.extract()?,
                _ => String::from("compone"),
            };
            return Err(PySyntaxError::new_err(format!(
                "keyword: {name:?} cannot be used as argument name in {module_name}.{func_name}, use an underscore at the end instead"
            )));
        }
    }

    Ok(())
}

pub fn build_props_dict<'py>(slf: &Bound<'py, RustComponent>) -> PyResult<Bound<'py, PyDict>> {
    let py = slf.py();
    let bound_args_obj = get_bound_args_object(slf)?;
    let bound_args = bound_args_obj.bind(py);
    let bound_kwargs = bound_args.getattr("kwargs")?;
    let bound_kwargs = bound_kwargs.downcast::<PyDict>()?;
    let bound_arguments = bound_args.getattr("arguments")?;
    let bound_arguments = bound_arguments.downcast::<PyDict>()?;

    let kwargs = PyDict::new(py);
    for (key, value) in bound_kwargs.iter() {
        if !value.is_none() {
            kwargs.set_item(key, value)?;
        }
    }

    let args = PyDict::new(py);
    for (key, value) in bound_arguments.iter() {
        if !kwargs.contains(&key)? && !value.is_none() {
            args.set_item(key, value)?;
        }
    }

    let var_keyword = class_optional_string_attr(slf.as_any(), "_var_keyword")?;
    if let Some(var_keyword) = var_keyword {
        if args.contains(&var_keyword)? {
            args.del_item(var_keyword)?;
        }
    }

    let props = PyDict::new(py);
    for (key, value) in args.iter() {
        props.set_item(key, value)?;
    }
    for (key, value) in kwargs.iter() {
        props.set_item(key, value)?;
    }
    Ok(props)
}

fn check_common_props(slf: &Bound<'_, RustComponent>, kwargs: &Bound<'_, PyDict>) -> PyResult<()> {
    let props = build_props_dict(slf)?;
    let mut has_common = false;
    for key in kwargs.keys() {
        if props.contains(&key)? {
            has_common = true;
            break;
        }
    }

    if has_common {
        return Ok(());
    }

    let mut kwargs_list = Vec::with_capacity(kwargs.len());
    for key in kwargs.keys() {
        kwargs_list.push(key.repr()?.extract::<String>()?);
    }
    let repr = slf.as_any().repr()?.extract::<String>()?;
    Err(PyTypeError::new_err(format!(
        "{repr} has no existing props for {}",
        kwargs_list.join(", ")
    )))
}

fn make_new(slf: &Bound<'_, RustComponent>, new_arguments: &Bound<'_, PyDict>) -> PyResult<Py<PyAny>> {
    let py = slf.py();
    let copy_module = py.import("copy")?;
    let inspect = py.import("inspect")?;
    let sig = slf.as_any().get_type().getattr("_sig")?;
    let bound_args_obj = get_bound_args_object(slf)?;
    let bound_args = bound_args_obj.bind(py);
    let original_arguments = bound_args.getattr("arguments")?;
    let original_arguments = original_arguments.downcast::<PyDict>()?;

    let arguments_copy = PyDict::new(py);
    for (key, value) in original_arguments.iter() {
        let copied = copy_module.call_method1("copy", (value,))?;
        arguments_copy.set_item(key, copied)?;
    }

    let bound_arguments_cls = inspect.getattr("BoundArguments")?;
    let bound_copy = bound_arguments_cls.call1((sig, arguments_copy))?;
    let bound_copy_arguments = bound_copy.getattr("arguments")?;
    let bound_copy_arguments = bound_copy_arguments.downcast::<PyDict>()?;

    let var_keyword = class_optional_string_attr(slf.as_any(), "_var_keyword")?;
    if let Some(var_keyword) = var_keyword {
        let old_star_arguments = bound_copy_arguments.get_item(&var_keyword)?.ok_or_else(|| {
            PyAttributeError::new_err(format!(
                "Bound arguments have no variable keyword entry {var_keyword:?}"
            ))
        })?;
        let old_star_arguments = old_star_arguments.downcast::<PyDict>()?;
        let new_star_arguments = PyDict::new(py);
        for (key, value) in new_arguments.iter() {
            if old_star_arguments.contains(&key)? {
                new_star_arguments.set_item(key, value)?;
            }
        }
        old_star_arguments.call_method1("update", (&new_star_arguments,))?;

        let other_arguments = PyDict::new(py);
        for (key, value) in new_arguments.iter() {
            if !new_star_arguments.contains(&key)? {
                other_arguments.set_item(key, value)?;
            }
        }
        bound_copy_arguments.call_method1("update", (&other_arguments,))?;
    } else {
        bound_copy_arguments.call_method1("update", (new_arguments,))?;
    }

    let bound_copy_kwargs = bound_copy.getattr("kwargs")?;
    let bound_copy_kwargs = bound_copy_kwargs.downcast::<PyDict>()?;
    let positional_args = get_positional_args(slf.as_any())?;
    let extra_kwargs = PyDict::new(py);
    for (key, value) in new_arguments.iter() {
        let key_string: String = key.extract()?;
        if !bound_copy_kwargs.contains(&key)? && !positional_args.contains(&key_string) {
            extra_kwargs.set_item(key, value)?;
        }
    }

    let new_kwargs = PyDict::new(py);
    for (key, value) in bound_copy_kwargs.iter() {
        new_kwargs.set_item(key, value)?;
    }
    for (key, value) in extra_kwargs.iter() {
        new_kwargs.set_item(key, value)?;
    }

    let bound_copy_args = bound_copy.getattr("args")?;
    let bound_copy_args = bound_copy_args.downcast::<PyTuple>()?;
    let new_bound = bind_args(slf.as_any(), bound_copy_args, Some(&new_kwargs))?;
    let new_bound_args = new_bound.getattr("args")?;
    let new_bound_args = new_bound_args.downcast::<PyTuple>()?;
    let new_bound_kwargs = new_bound.getattr("kwargs")?;
    let new_bound_kwargs = new_bound_kwargs.downcast::<PyDict>()?;

    let cls = slf.as_any().get_type();
    let new_instance = cls.call(new_bound_args, Some(new_bound_kwargs))?;
    Ok(new_instance.unbind())
}

fn make_new_with_same_arguments(slf: &Bound<'_, RustComponent>) -> PyResult<Py<PyAny>> {
    let py = slf.py();
    let bound_args_obj = get_bound_args_object(slf)?;
    let bound_args = bound_args_obj.bind(py);
    let args = bound_args.getattr("args")?;
    let args = args.downcast::<PyTuple>()?;
    let kwargs = bound_args.getattr("kwargs")?;
    let kwargs = kwargs.downcast::<PyDict>()?;
    slf.as_any().get_type().call(args, Some(kwargs)).map(Bound::unbind)
}

fn get_positional_args(obj: &Bound<'_, PyAny>) -> PyResult<HashSet<String>> {
    let attr = obj.get_type().getattr("_positional_args")?;
    let mut positional = HashSet::new();
    for item in attr.try_iter()? {
        positional.insert(item?.extract()?);
    }
    Ok(positional)
}

pub fn class_kind(obj: &Bound<'_, PyAny>) -> PyResult<String> {
    class_string_attr(obj, "_kind")
}

pub fn class_string_attr(obj: &Bound<'_, PyAny>, attr: &str) -> PyResult<String> {
    obj.get_type().getattr(attr)?.extract()
}

pub fn class_optional_string_attr(obj: &Bound<'_, PyAny>, attr: &str) -> PyResult<Option<String>> {
    let value = obj.get_type().getattr(attr)?;
    if value.is_none() {
        Ok(None)
    } else {
        Ok(Some(value.extract()?))
    }
}

pub fn class_bool_attr(obj: &Bound<'_, PyAny>, attr: &str) -> PyResult<bool> {
    match obj.get_type().getattr(attr) {
        Ok(value) => value.extract(),
        Err(_) => Ok(false),
    }
}

pub fn class_optional_attr(obj: &Bound<'_, PyAny>, attr: &str) -> PyResult<Option<Py<PyAny>>> {
    let value = obj.get_type().getattr(attr)?;
    if value.is_none() {
        Ok(None)
    } else {
        Ok(Some(value.unbind()))
    }
}

pub fn empty_signature(py: Python<'_>) -> PyResult<Py<PyAny>> {
    let inspect = py.import("inspect")?;
    let parameter_cls = inspect.getattr("Parameter")?;
    let var_keyword = parameter_cls.getattr("VAR_KEYWORD")?;
    let param = parameter_cls.call1(("kwargs", var_keyword))?;
    let params = PyList::new(py, [param])?;
    inspect.getattr("Signature")?.call1((params,)).map(Bound::unbind)
}

pub fn make_dynamic_class(
    py: Python<'_>,
    name: &str,
    module: &str,
    attrs: &Bound<'_, PyDict>,
) -> PyResult<Py<PyAny>> {
    let builtins = py.import("builtins")?;
    let type_ = builtins.getattr("type")?;
    let base = py.get_type::<RustComponent>();
    let bases = PyTuple::new(py, [base])?;
    attrs.set_item("__module__", module)?;
    type_.call1((name, bases, attrs)).map(Bound::unbind)
}

#[pyfunction]
pub fn Component(func_or_class: &Bound<'_, PyAny>) -> PyResult<Py<PyAny>> {
    let py = func_or_class.py();
    let inspect = py.import("inspect")?;
    let functools = py.import("functools")?;
    let is_function: bool = inspect.getattr("isfunction")?.call1((func_or_class,))?.extract()?;
    let lru_wrapper = functools.getattr("_lru_cache_wrapper")?;
    let is_lru: bool = func_or_class.is_instance(&lru_wrapper)?;

    if is_function || is_lru {
        make_func_component(func_or_class)
    } else {
        let is_class: bool = inspect.getattr("isclass")?.call1((func_or_class,))?.extract()?;
        if is_class {
            make_class_component(func_or_class)
        } else {
            Err(PyTypeError::new_err("Components can only be classes or functions"))
        }
    }
}

fn make_func_component(func: &Bound<'_, PyAny>) -> PyResult<Py<PyAny>> {
    let py = func.py();
    let (orig_sig, positional_args) = make_sig(func)?;
    let (parameters, pass_children, var_keyword) = filter_signature(
        &orig_sig,
        |name| name != "children",
        true,
    )?;
    let sig = py.import("inspect")?.getattr("Signature")?.call1((parameters,))?;
    let attrs = PyDict::new(py);
    attrs.set_item("_kind", "func")?;
    attrs.set_item("_func", func)?;
    attrs.set_item("_sig", sig)?;
    attrs.set_item("_positional_args", positional_args)?;
    attrs.set_item("_var_keyword", var_keyword)?;
    attrs.set_item("_pass_children", pass_children)?;
    let name: String = func.getattr("__name__")?.extract()?;
    let module: String = func.getattr("__module__")?.extract()?;
    make_dynamic_class(py, &name, &module, &attrs)
}

fn make_class_component(user_class: &Bound<'_, PyAny>) -> PyResult<Py<PyAny>> {
    if !user_class.hasattr("render")? {
        let name: String = user_class.getattr("__name__")?.extract()?;
        return Err(PyTypeError::new_err(format!(
            "{name} doesn't have a .render() method."
        )));
    }

    let py = user_class.py();
    let init = user_class.getattr("__init__")?;
    let (orig_sig, positional_args) = make_sig(&init)?;
    let (parameters, _, var_keyword) = filter_signature(
        &orig_sig,
        |name| name != "self" && name != "children",
        false,
    )?;
    let sig = py.import("inspect")?.getattr("Signature")?.call1((parameters,))?;
    let render = user_class.getattr("render")?;
    let render_sig = py.import("inspect")?.getattr("signature")?.call1((&render,))?;
    let pass_children = signature_has_parameter(&render_sig, "children")?;
    let attrs = PyDict::new(py);
    attrs.set_item("_kind", "class")?;
    attrs.set_item("_user_class", user_class)?;
    attrs.set_item("_render_func", render)?;
    attrs.set_item("_sig", sig)?;
    attrs.set_item("_positional_args", positional_args)?;
    attrs.set_item("_var_keyword", var_keyword)?;
    attrs.set_item("_pass_children", pass_children)?;
    let name: String = user_class.getattr("__name__")?.extract()?;
    let module: String = user_class.getattr("__module__")?.extract()?;
    make_dynamic_class(py, &name, &module, &attrs)
}

fn make_sig<'py>(func: &Bound<'py, PyAny>) -> PyResult<(Bound<'py, PyAny>, Vec<String>)> {
    let py = func.py();
    let sig = py.import("inspect")?.getattr("signature")?.call1((func,))?;
    let positional_args = positional_args_from_signature(&sig)?;
    Ok((sig, positional_args))
}

fn positional_args_from_signature(sig: &Bound<'_, PyAny>) -> PyResult<Vec<String>> {
    let py = sig.py();
    let parameter_cls = py.import("inspect")?.getattr("Parameter")?;
    let pos_only = parameter_cls.getattr("POSITIONAL_ONLY")?;
    let pos_or_kw = parameter_cls.getattr("POSITIONAL_OR_KEYWORD")?;
    let mut positional = Vec::new();
    let parameters = sig.getattr("parameters")?;
    for item in parameters.call_method0("items")?.try_iter()? {
        let item = item?;
        let pair = item.downcast::<PyTuple>()?;
        let name: String = pair.get_item(0)?.extract()?;
        let param = pair.get_item(1)?;
        let kind = param.getattr("kind")?;
        if kind.eq(&pos_only)? || kind.eq(&pos_or_kw)? {
            positional.push(name);
        }
    }
    Ok(positional)
}

fn filter_signature<F>(
    sig: &Bound<'_, PyAny>,
    include: F,
    track_children: bool,
) -> PyResult<(Py<PyAny>, bool, Option<String>)>
where
    F: Fn(&str) -> bool,
{
    let py = sig.py();
    let parameter_cls = py.import("inspect")?.getattr("Parameter")?;
    let var_keyword_kind = parameter_cls.getattr("VAR_KEYWORD")?;
    let parameters = PyList::empty(py);
    let mut pass_children = false;
    let mut var_keyword = None;
    let parameters_mapping = sig.getattr("parameters")?;
    for item in parameters_mapping.call_method0("items")?.try_iter()? {
        let item = item?;
        let pair = item.downcast::<PyTuple>()?;
        let name: String = pair.get_item(0)?.extract()?;
        let param = pair.get_item(1)?;
        if track_children && name == "children" {
            pass_children = true;
        }
        let kind = param.getattr("kind")?;
        if kind.eq(&var_keyword_kind)? {
            var_keyword = Some(name.clone());
        }
        if include(&name) {
            parameters.append(param)?;
        }
    }
    Ok((parameters.unbind().into_any(), pass_children, var_keyword))
}

fn signature_has_parameter(sig: &Bound<'_, PyAny>, name: &str) -> PyResult<bool> {
    sig.getattr("parameters")?.contains(name)
}
