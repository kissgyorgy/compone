use std::cell::RefCell;
use std::collections::hash_map::DefaultHasher;
use std::collections::{HashMap, HashSet};
use std::hash::{Hash, Hasher};
use std::rc::Rc;
use std::sync::Arc;

use pyo3::exceptions::{PyAssertionError, PyAttributeError, PySyntaxError, PyTypeError, PyValueError};
use pyo3::prelude::*;
use pyo3::types::{PyBool, PyDict, PyFloat, PyInt, PyIterator, PyList, PyString, PyTuple, PyType};

use crate::escape::{escape_to_string, is_safe_or_markup_value, safe_empty, safe_from_string};
use crate::html::{attrs_to_dict, parse_html_class, render_attributes_from_pairs};
use crate::utils::is_python_keyword;

const MAX_RENDER_CACHE_ENTRIES: usize = 4096;
const MAX_RENDER_CACHE_KEY_VALUES: usize = 512;
const MAX_RENDER_CACHE_KEY_DEPTH: usize = 16;

thread_local! {
    static PARENT_STACK: RefCell<Vec<Py<PyAny>>> = const { RefCell::new(Vec::new()) };
    static CLASS_CACHE: RefCell<HashMap<usize, Rc<ClassMetadata>>> = RefCell::new(HashMap::new());
    static RENDER_CACHE: RefCell<HashMap<RenderCacheKey, RenderedCacheEntry>> = RefCell::new(HashMap::new());
    static RENDER_CACHE_ADMISSIONS: RefCell<HashSet<u64>> = RefCell::new(HashSet::new());
}

pub fn init_context_var(_py: Python<'_>) -> PyResult<()> {
    PARENT_STACK.with(|stack| stack.borrow_mut().clear());
    CLASS_CACHE.with(|cache| cache.borrow_mut().clear());
    RENDER_CACHE.with(|cache| cache.borrow_mut().clear());
    RENDER_CACHE_ADMISSIONS.with(|cache| cache.borrow_mut().clear());
    Ok(())
}

#[derive(Clone, Copy, PartialEq, Eq)]
enum ComponentKind {
    Void,
    Element,
    Func,
    Class,
    Comment,
    Unknown,
}

impl ComponentKind {
    fn from_str(value: &str) -> Self {
        match value {
            "void" => Self::Void,
            "element" => Self::Element,
            "func" => Self::Func,
            "class" => Self::Class,
            "comment" => Self::Comment,
            _ => Self::Unknown,
        }
    }
}

#[pyclass(name = "_ComponentBase", subclass)]
pub struct RustComponent {
    bound_args: Option<Py<PyAny>>,
    args: Vec<Py<PyAny>>,
    kwargs: Vec<(String, Py<PyAny>)>,
    children: Vec<Py<PyAny>>,
    original_kwargs: Option<Vec<(String, Py<PyAny>)>>,
    parent: Option<Py<PyAny>>,
    user_instance: Option<Py<PyAny>>,
    kind: ComponentKind,
    name: Option<Arc<str>>,
    html: bool,
    list_only: bool,
    pass_children: bool,
    children_positional_index: Option<usize>,
    positional_args: Option<Arc<[String]>>,
    func: Option<Py<PyAny>>,
    user_class: Option<Py<PyAny>>,
}

#[pymethods]
impl RustComponent {
    #[new]
    #[pyo3(signature = (*_args, **_kwargs))]
    fn new(_args: &Bound<'_, PyTuple>, _kwargs: Option<&Bound<'_, PyDict>>) -> Self {
        Self {
            bound_args: None,
            args: Vec::new(),
            kwargs: Vec::new(),
            children: Vec::new(),
            original_kwargs: None,
            parent: None,
            user_instance: None,
            kind: ComponentKind::Unknown,
            name: None,
            html: false,
            list_only: false,
            pass_children: false,
            children_positional_index: None,
            positional_args: None,
            func: None,
            user_class: None,
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
            Some(kwargs) => Ok(dict_from_string_items(py, kwargs)?.unbind().into_any()),
            None if matches!(borrowed.kind, ComponentKind::Element | ComponentKind::Void) => {
                Ok(dict_from_string_items(py, &borrowed.kwargs)?.unbind().into_any())
            }
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
        check_keywords_for_name(Some(kwargs), "compone", "replace")?;
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
        check_keywords_for_name(Some(&kwargs), "compone", "append")?;
        check_common_props(&slf, &kwargs)?;

        let props = build_props_dict(&slf)?;
        let appended = PyDict::new(py);
        for (key, value) in kwargs.iter() {
            let old_value = props.get_item(&key)?.ok_or_else(|| {
                PyTypeError::new_err("append expected an existing prop, but none was found")
            })?;
            let new_value = old_value.add(value)?;
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
        let current = slf.as_any().clone().unbind();
        let parent = PARENT_STACK.with(|stack| {
            let mut stack = stack.borrow_mut();
            let parent = stack.last().map(|item| item.clone_ref(py));
            stack.push(current.clone_ref(py));
            parent
        });
        slf.borrow_mut().parent = parent;
        Ok(current)
    }

    #[pyo3(signature = (_exc_type=None, _exc_val=None, _exc_tb=None))]
    fn __exit__(
        slf: Bound<'_, Self>,
        _exc_type: Option<&Bound<'_, PyAny>>,
        _exc_val: Option<&Bound<'_, PyAny>>,
        _exc_tb: Option<&Bound<'_, PyAny>>,
    ) -> PyResult<()> {
        let py = slf.py();
        PARENT_STACK.with(|stack| {
            let mut stack = stack.borrow_mut();
            let _ = stack.pop();
        });
        let parent = slf
            .borrow()
            .parent
            .as_ref()
            .map(|parent| parent.clone_ref(py));
        if let Some(parent) = parent {
            let parent = parent.bind(py).downcast::<RustComponent>()?;
            parent.borrow_mut().children.push(slf.as_any().clone().unbind());
        }
        Ok(())
    }

    fn __iadd__(slf: Bound<'_, Self>, other: &Bound<'_, PyAny>) -> PyResult<()> {
        slf.borrow_mut().children.push(other.clone().unbind());
        Ok(())
    }

    #[classmethod]
    fn __class_getitem__(cls: &Bound<'_, PyType>, key: &Bound<'_, PyAny>) -> PyResult<Py<PyAny>> {
        let instance = cls.call0()?;
        let instance = instance.downcast::<RustComponent>()?;
        RustComponent::__getitem__(instance.clone(), key)
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
        let new_component = new.bind(slf.py()).downcast::<RustComponent>()?;
        new_component.borrow_mut().children = child_items;
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

        let other_component = other.downcast::<RustComponent>()?;
        let result = if slf.borrow().kind == ComponentKind::Void
            && other_component.borrow().kind == ComponentKind::Void
        {
            let self_name = slf.borrow().name.clone();
            let other_name = other_component.borrow().name.clone();
            let self_kwargs = RustComponent::_original_kwargs(slf.clone())?
                .bind(other.py())
                .clone();
            let other_kwargs = RustComponent::_original_kwargs(other_component.clone())?;
            self_name == other_name && self_kwargs.eq(other_kwargs.bind(other.py()))?
        } else {
            let self_str = render_instance(&slf)?;
            let other_str = render_instance(other_component)?;
            self_str.bind(other.py()).eq(other_str.bind(other.py()))?
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
        rendered.mul(count).map(Bound::unbind)
    }
}

fn initialize_instance(
    slf: &Bound<'_, RustComponent>,
    args: &Bound<'_, PyTuple>,
    kwargs: Option<&Bound<'_, PyDict>>,
) -> PyResult<()> {
    let py = slf.py();
    let metadata = class_metadata(slf.as_any())?;
    let (args, kwargs, original_kwargs) = if can_bind_element_arguments_direct(&metadata, kwargs)? {
        bind_element_arguments_direct(py, &metadata, args, kwargs)?
    } else if kwargs.is_none() && matches!(metadata.kind, ComponentKind::Func | ComponentKind::Class) {
        if let Some(bound) = bind_arguments_exact_positionals(py, &metadata.signature, args) {
            bound
        } else {
            let (args, kwargs) = bind_arguments_without_kwargs(py, &metadata.signature, args)?;
            (args, kwargs, Some(Vec::new()))
        }
    } else if let Some(kwargs_dict) = kwargs {
        if let Some(bound) = bind_arguments_exact_keywords(py, &metadata.signature, args, kwargs_dict)? {
            bound
        } else {
            let prepared_kwargs = prepare_init_kwargs_for_metadata(py, kwargs, &metadata)?;
            if contains_python_keyword(&prepared_kwargs)? {
                let keyword_func = keyword_check_target(slf.as_any())?;
                check_keywords(&keyword_func, Some(&prepared_kwargs))?;
            }
            let (args, kwargs) =
                bind_arguments_rust(py, &metadata.signature, args, &prepared_kwargs)?;

            let original_kwargs = extract_string_dict_items(&prepared_kwargs)?;
            (args, kwargs, Some(original_kwargs))
        }
    } else {
        let prepared_kwargs = prepare_init_kwargs_for_metadata(py, kwargs, &metadata)?;
        let (args, kwargs) =
            bind_arguments_rust(py, &metadata.signature, args, &prepared_kwargs)?;
        let original_kwargs = extract_string_dict_items(&prepared_kwargs)?;
        (args, kwargs, Some(original_kwargs))
    };

    let mut borrowed = slf.borrow_mut();
    borrowed.bound_args = None;
    borrowed.args = args;
    borrowed.kwargs = kwargs;
    borrowed.children.clear();
    borrowed.original_kwargs = original_kwargs;
    borrowed.parent = None;
    borrowed.user_instance = None;
    borrowed.kind = metadata.kind;
    borrowed.name = Some(metadata.name.clone());
    borrowed.html = metadata.html;
    borrowed.list_only = metadata.list_only;
    borrowed.pass_children = metadata.pass_children;
    borrowed.children_positional_index = metadata.children_positional_index;
    borrowed.positional_args = Some(metadata.positional_args.clone());
    borrowed.func = metadata.func.as_ref().map(|func| func.clone_ref(py));
    borrowed.user_class = metadata
        .user_class
        .as_ref()
        .map(|user_class| user_class.clone_ref(py));
    Ok(())
}

fn can_bind_element_arguments_direct(
    metadata: &ClassMetadata,
    kwargs: Option<&Bound<'_, PyDict>>,
) -> PyResult<bool> {
    if !matches!(metadata.kind, ComponentKind::Element | ComponentKind::Void)
        || metadata.attributes.is_some()
    {
        return Ok(false);
    }

    let Some(kwargs) = kwargs else {
        return Ok(false);
    };

    if metadata.html {
        if let Some(class_value) = kwargs.get_item("class_")? {
            return Ok(can_parse_direct_html_class(&class_value));
        }
    }

    Ok(true)
}

fn bind_element_arguments_direct(
    py: Python<'_>,
    metadata: &ClassMetadata,
    args: &Bound<'_, PyTuple>,
    kwargs: Option<&Bound<'_, PyDict>>,
) -> PyResult<(
    Vec<Py<PyAny>>,
    Vec<(String, Py<PyAny>)>,
    Option<Vec<(String, Py<PyAny>)>>,
)> {
    if !args.is_empty() {
        return Err(PyTypeError::new_err("too many positional arguments"));
    }

    let mut attrs = Vec::with_capacity(kwargs.map_or(0, |kwargs| kwargs.len()));
    if let Some(kwargs) = kwargs {
        for (key, value) in kwargs.iter() {
            let key: String = key.extract()?;
            if is_python_keyword(&key) {
                return Err(PySyntaxError::new_err(format!(
                    "keyword: {key:?} cannot be used as argument name in compone.{}, use an underscore at the end instead",
                    metadata.name
                )));
            }

            let value = if metadata.html && key == "class_" {
                parse_direct_html_class(py, &value)?.unwrap_or_else(|| py.None())
            } else {
                value.unbind()
            };
            attrs.push((key, value));
        }
    }

    Ok((Vec::new(), attrs, None))
}

fn can_parse_direct_html_class(value: &Bound<'_, PyAny>) -> bool {
    if value.is_none() || value.downcast::<PyString>().is_ok() {
        return true;
    }

    if let Ok(tuple) = value.downcast::<PyTuple>() {
        return tuple.iter().all(|item| item.is_none() || item.downcast::<PyString>().is_ok());
    }

    if let Ok(list) = value.downcast::<PyList>() {
        return list.iter().all(|item| item.is_none() || item.downcast::<PyString>().is_ok());
    }

    if let Ok(dict) = value.downcast::<PyDict>() {
        return dict
            .iter()
            .all(|(key, _)| key.downcast::<PyString>().is_ok());
    }

    false
}

fn parse_direct_html_class(
    py: Python<'_>,
    value: &Bound<'_, PyAny>,
) -> PyResult<Option<Py<PyAny>>> {
    let mut parsed = Vec::new();
    let mut seen = HashSet::new();
    collect_direct_html_classes(value, &mut parsed, &mut seen)?;
    if parsed.is_empty() {
        return Ok(None);
    }
    Ok(Some(PyList::new(py, parsed)?.unbind().into_any()))
}

fn collect_direct_html_classes(
    value: &Bound<'_, PyAny>,
    parsed: &mut Vec<String>,
    seen: &mut HashSet<String>,
) -> PyResult<()> {
    if value.is_none() || !value.is_truthy()? {
        return Ok(());
    }

    if let Ok(string) = value.downcast::<PyString>() {
        push_class_pieces(&string.to_string_lossy(), parsed, seen);
        return Ok(());
    }

    if let Ok(tuple) = value.downcast::<PyTuple>() {
        for item in tuple.iter() {
            collect_direct_html_classes(&item, parsed, seen)?;
        }
        return Ok(());
    }

    if let Ok(list) = value.downcast::<PyList>() {
        for item in list.iter() {
            collect_direct_html_classes(&item, parsed, seen)?;
        }
        return Ok(());
    }

    if let Ok(dict) = value.downcast::<PyDict>() {
        for (class_name, enabled) in dict.iter() {
            if enabled.is_truthy()? {
                let class_name = class_name.downcast::<PyString>()?;
                let class_name = class_name.to_string_lossy().trim().to_string();
                if !class_name.is_empty() && seen.insert(class_name.clone()) {
                    parsed.push(class_name);
                }
            }
        }
    }

    Ok(())
}

fn push_class_pieces(value: &str, parsed: &mut Vec<String>, seen: &mut HashSet<String>) {
    for piece in value.split_whitespace() {
        let stripped = piece.trim();
        if !stripped.is_empty() && seen.insert(stripped.to_string()) {
            parsed.push(stripped.to_string());
        }
    }
}

fn prepare_init_kwargs_for_metadata<'py>(
    py: Python<'py>,
    kwargs: Option<&Bound<'py, PyDict>>,
    metadata: &ClassMetadata,
) -> PyResult<Bound<'py, PyDict>> {
    let prepared = PyDict::new(py);
    if let Some(kwargs) = kwargs {
        for (key, value) in kwargs.iter() {
            prepared.set_item(key, value)?;
        }
    }

    if matches!(metadata.kind, ComponentKind::Element | ComponentKind::Void) {
        if metadata.html {
            parse_html_class(&prepared)?;
        }
        if let Some(attrs) = &metadata.attributes {
            attrs_to_dict(attrs.bind(py), &prepared)?;
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
    let metadata = class_metadata(obj)?;
    if matches!(metadata.kind, ComponentKind::Element | ComponentKind::Void) && metadata.html {
        parse_html_class(&prepared)?;
    }
    Ok(prepared)
}

#[derive(Clone, Copy, PartialEq, Eq)]
enum ParamKind {
    PosOnly,
    PosOrKw,
    KwOnly,
    VarKw,
}

struct ParamSpec {
    name: String,
    kind: ParamKind,
    default: Option<Py<PyAny>>,
}

struct SignatureSpec {
    params: Vec<ParamSpec>,
    positional_args: Vec<String>,
    var_keyword: Option<String>,
}

struct ClassMetadata {
    kind: ComponentKind,
    name: Arc<str>,
    html: bool,
    list_only: bool,
    pass_children: bool,
    children_positional_index: Option<usize>,
    positional_args: Arc<[String]>,
    signature: SignatureSpec,
    func: Option<Py<PyAny>>,
    user_class: Option<Py<PyAny>>,
    attributes: Option<Py<PyAny>>,
}

struct RenderedCacheEntry {
    rendered: String,
    safe: Py<PyAny>,
}

#[derive(Hash, PartialEq, Eq)]
struct RenderCacheKey {
    type_ptr: usize,
    args: Vec<CacheValue>,
    kwargs: Vec<(String, CacheValue)>,
    children: Vec<CacheValue>,
}

enum CacheValue {
    None,
    Bool(bool),
    Int(String),
    Int64(i64),
    Float(String),
    Str(String),
    SafeStr(String),
    Identity { ptr: usize, _owner: Py<PyAny> },
    List(Vec<CacheValue>),
    Tuple(Vec<CacheValue>),
    Dict(Vec<(CacheValue, CacheValue)>),
    Component(Box<RenderCacheKey>),
}

impl PartialEq for CacheValue {
    fn eq(&self, other: &Self) -> bool {
        match (self, other) {
            (Self::None, Self::None) => true,
            (Self::Bool(left), Self::Bool(right)) => left == right,
            (Self::Int(left), Self::Int(right)) => left == right,
            (Self::Int64(left), Self::Int64(right)) => left == right,
            (Self::Float(left), Self::Float(right)) => left == right,
            (Self::Str(left), Self::Str(right)) => left == right,
            (Self::SafeStr(left), Self::SafeStr(right)) => left == right,
            (Self::Identity { ptr: left, .. }, Self::Identity { ptr: right, .. }) => left == right,
            (Self::List(left), Self::List(right)) => left == right,
            (Self::Tuple(left), Self::Tuple(right)) => left == right,
            (Self::Dict(left), Self::Dict(right)) => left == right,
            (Self::Component(left), Self::Component(right)) => left == right,
            _ => false,
        }
    }
}

impl Eq for CacheValue {}

impl Hash for CacheValue {
    fn hash<H: Hasher>(&self, state: &mut H) {
        match self {
            Self::None => 0_u8.hash(state),
            Self::Bool(value) => {
                1_u8.hash(state);
                value.hash(state);
            }
            Self::Int(value) => {
                2_u8.hash(state);
                value.hash(state);
            }
            Self::Int64(value) => {
                3_u8.hash(state);
                value.hash(state);
            }
            Self::Float(value) => {
                4_u8.hash(state);
                value.hash(state);
            }
            Self::Str(value) => {
                5_u8.hash(state);
                value.hash(state);
            }
            Self::SafeStr(value) => {
                6_u8.hash(state);
                value.hash(state);
            }
            Self::Identity { ptr, .. } => {
                7_u8.hash(state);
                ptr.hash(state);
            }
            Self::List(items) => {
                8_u8.hash(state);
                items.hash(state);
            }
            Self::Tuple(items) => {
                9_u8.hash(state);
                items.hash(state);
            }
            Self::Dict(items) => {
                10_u8.hash(state);
                items.hash(state);
            }
            Self::Component(key) => {
                11_u8.hash(state);
                key.hash(state);
            }
        }
    }
}

struct RenderCacheKeyBuilder {
    remaining_values: usize,
}

impl SignatureSpec {
    fn from_class(obj: &Bound<'_, PyAny>) -> PyResult<Self> {
        let py = obj.py();
        let cls = obj.get_type();
        let specs = cls.getattr("_param_specs")?;
        let mut params = Vec::new();
        let mut positional_args = Vec::new();
        let mut var_keyword = None;
        for item in specs.try_iter()? {
            let item = item?;
            let item = item.downcast::<PyTuple>()?;
            let name: String = item.get_item(0)?.extract()?;
            let kind_code: u8 = item.get_item(1)?.extract()?;
            let has_default: bool = item.get_item(2)?.extract()?;
            let default = if has_default {
                Some(item.get_item(3)?.clone().unbind())
            } else {
                None
            };
            let kind = match kind_code {
                0 => ParamKind::PosOnly,
                1 => ParamKind::PosOrKw,
                2 => ParamKind::KwOnly,
                _ => ParamKind::VarKw,
            };
            if matches!(kind, ParamKind::PosOnly | ParamKind::PosOrKw) {
                positional_args.push(name.clone());
            }
            if kind == ParamKind::VarKw {
                var_keyword = Some(name.clone());
            }
            params.push(ParamSpec {
                name,
                kind,
                default: default.map(|default| default.clone_ref(py)),
            });
        }
        Ok(Self {
            params,
            positional_args,
            var_keyword,
        })
    }
}

fn class_metadata(obj: &Bound<'_, PyAny>) -> PyResult<Rc<ClassMetadata>> {
    let key = obj.get_type().as_ptr() as usize;
    if let Some(metadata) = CLASS_CACHE.with(|cache| cache.borrow().get(&key).cloned()) {
        return Ok(metadata);
    }

    let metadata = Rc::new(ClassMetadata::from_class(obj)?);
    CLASS_CACHE.with(|cache| {
        cache.borrow_mut().insert(key, metadata.clone());
    });
    Ok(metadata)
}

impl ClassMetadata {
    fn from_class(obj: &Bound<'_, PyAny>) -> PyResult<Self> {
        let cls = obj.get_type();
        let kind_string: String = cls.getattr("_kind")?.extract()?;
        let kind = ComponentKind::from_str(&kind_string);
        let name = match cls.getattr("_name") {
            Ok(name) if !name.is_none() => Arc::from(name.extract::<String>()?),
            _ => Arc::from(""),
        };
        let html = match cls.getattr("_html") {
            Ok(value) => value.extract()?,
            Err(_) => false,
        };
        let list_only = match cls.getattr("_list_only") {
            Ok(value) => value.extract()?,
            Err(_) => false,
        };
        let pass_children = match cls.getattr("_pass_children") {
            Ok(value) => value.extract()?,
            Err(_) => false,
        };
        let children_positional_index = match cls.getattr("_children_positional_index") {
            Ok(value) if !value.is_none() => Some(value.extract()?),
            _ => None,
        };
        let signature = SignatureSpec::from_class(obj)?;
        let positional_args: Arc<[String]> = Arc::from(signature.positional_args.clone());
        let func = match cls.getattr("_func") {
            Ok(value) if !value.is_none() => Some(value.unbind()),
            _ => None,
        };
        let user_class = match cls.getattr("_user_class") {
            Ok(value) if !value.is_none() => Some(value.unbind()),
            _ => None,
        };
        let attributes = match cls.getattr("_attributes") {
            Ok(value) if !value.is_none() => Some(value.unbind()),
            _ => None,
        };
        Ok(Self {
            kind,
            name,
            html,
            list_only,
            pass_children,
            children_positional_index,
            positional_args,
            signature,
            func,
            user_class,
            attributes,
        })
    }
}

fn extract_string_dict_items(dict: &Bound<'_, PyDict>) -> PyResult<Vec<(String, Py<PyAny>)>> {
    let mut items = Vec::with_capacity(dict.len());
    for (key, value) in dict.iter() {
        items.push((key.extract()?, value.clone().unbind()));
    }
    Ok(items)
}

type BoundState = (Vec<Py<PyAny>>, Vec<(String, Py<PyAny>)>);

type InitBoundState = (
    Vec<Py<PyAny>>,
    Vec<(String, Py<PyAny>)>,
    Option<Vec<(String, Py<PyAny>)>>,
);

fn bind_arguments_exact_positionals(
    _py: Python<'_>,
    signature: &SignatureSpec,
    args: &Bound<'_, PyTuple>,
) -> Option<InitBoundState> {
    if args.len() != signature.params.len()
        || signature.params.iter().any(|param| {
            !matches!(param.kind, ParamKind::PosOnly | ParamKind::PosOrKw)
                || param.default.is_some()
        })
    {
        return None;
    }

    let bound_args = args.iter().map(Bound::unbind).collect();
    Some((bound_args, Vec::new(), Some(Vec::new())))
}

fn bind_arguments_exact_keywords(
    py: Python<'_>,
    signature: &SignatureSpec,
    args: &Bound<'_, PyTuple>,
    kwargs: &Bound<'_, PyDict>,
) -> PyResult<Option<InitBoundState>> {
    if !args.is_empty()
        || signature.var_keyword.is_some()
        || signature
            .params
            .iter()
            .any(|param| matches!(param.kind, ParamKind::PosOnly | ParamKind::VarKw))
    {
        return Ok(None);
    }

    let mut found = 0;
    let mut bound_args = Vec::new();
    let mut bound_kwargs = Vec::new();
    for param in &signature.params {
        let value = match kwargs.get_item(&param.name)? {
            Some(value) => {
                found += 1;
                value.unbind()
            }
            None => match &param.default {
                Some(default) => default.clone_ref(py),
                None => {
                    return Err(PyTypeError::new_err(format!(
                        "missing a required argument: '{}'",
                        param.name
                    )))
                }
            },
        };

        match param.kind {
            ParamKind::PosOrKw => bound_args.push(value),
            ParamKind::KwOnly => bound_kwargs.push((param.name.clone(), value)),
            ParamKind::PosOnly | ParamKind::VarKw => unreachable!(),
        }
    }

    if found != kwargs.len() {
        for key in kwargs.keys() {
            let key: String = key.extract()?;
            if is_python_keyword(&key) {
                return Err(PySyntaxError::new_err(format!(
                    "keyword: {key:?} cannot be used as argument name in compone, use an underscore at the end instead"
                )));
            }
            if !signature.params.iter().any(|param| param.name == key) {
                return Err(PyTypeError::new_err(format!(
                    "got an unexpected keyword argument '{key}'"
                )));
            }
        }
    }

    let original_kwargs = extract_string_dict_items(kwargs)?;
    Ok(Some((
        bound_args,
        bound_kwargs,
        Some(original_kwargs),
    )))
}

fn bind_arguments_without_kwargs(
    py: Python<'_>,
    signature: &SignatureSpec,
    args: &Bound<'_, PyTuple>,
) -> PyResult<BoundState> {
    let mut assigned: Vec<Option<Py<PyAny>>> = signature.params.iter().map(|_| None).collect();
    let positional_indices: Vec<usize> = signature
        .params
        .iter()
        .enumerate()
        .filter_map(|(index, param)| {
            matches!(param.kind, ParamKind::PosOnly | ParamKind::PosOrKw).then_some(index)
        })
        .collect();

    if args.len() > positional_indices.len() {
        return Err(PyTypeError::new_err("too many positional arguments"));
    }

    for (arg_index, value) in args.iter().enumerate() {
        assigned[positional_indices[arg_index]] = Some(value.clone().unbind());
    }

    for (index, param) in signature.params.iter().enumerate() {
        if param.kind == ParamKind::VarKw {
            continue;
        }

        if assigned[index].is_none() {
            if let Some(default) = &param.default {
                assigned[index] = Some(default.clone_ref(py));
            } else {
                return Err(PyTypeError::new_err(format!(
                    "missing a required argument: '{}'",
                    param.name
                )));
            }
        }
    }

    let mut bound_args = Vec::new();
    let mut bound_kwargs = Vec::new();

    for (index, param) in signature.params.iter().enumerate() {
        match param.kind {
            ParamKind::PosOnly | ParamKind::PosOrKw => {
                let value = assigned[index]
                    .take()
                    .expect("positional argument must be assigned");
                bound_args.push(value);
            }
            ParamKind::KwOnly => {
                let value = assigned[index]
                    .take()
                    .expect("keyword-only argument must be assigned");
                bound_kwargs.push((param.name.clone(), value));
            }
            ParamKind::VarKw => {}
        }
    }

    Ok((bound_args, bound_kwargs))
}

fn bind_arguments_rust(
    py: Python<'_>,
    signature: &SignatureSpec,
    args: &Bound<'_, PyTuple>,
    kwargs: &Bound<'_, PyDict>,
) -> PyResult<BoundState> {
    let mut remaining = extract_string_dict_items(kwargs)?;
    let mut assigned: Vec<Option<Py<PyAny>>> = signature.params.iter().map(|_| None).collect();
    let positional_indices: Vec<usize> = signature
        .params
        .iter()
        .enumerate()
        .filter_map(|(index, param)| {
            matches!(param.kind, ParamKind::PosOnly | ParamKind::PosOrKw).then_some(index)
        })
        .collect();

    if args.len() > positional_indices.len() {
        return Err(PyTypeError::new_err("too many positional arguments"));
    }

    for (arg_index, value) in args.iter().enumerate() {
        assigned[positional_indices[arg_index]] = Some(value.clone().unbind());
    }

    for (index, param) in signature.params.iter().enumerate() {
        if param.kind == ParamKind::VarKw {
            continue;
        }

        if param.kind != ParamKind::PosOnly {
            if let Some(position) = remaining.iter().position(|(key, _)| key == &param.name) {
                if assigned[index].is_some() {
                    return Err(PyTypeError::new_err(format!(
                        "multiple values for argument '{}'",
                        param.name
                    )));
                }
                assigned[index] = Some(remaining.remove(position).1);
            }
        }

        if assigned[index].is_none() {
            if let Some(default) = &param.default {
                assigned[index] = Some(default.clone_ref(py));
            } else {
                return Err(PyTypeError::new_err(format!(
                    "missing a required argument: '{}'",
                    param.name
                )));
            }
        }
    }

    if signature.var_keyword.is_none() && !remaining.is_empty() {
        return Err(PyTypeError::new_err(format!(
            "got an unexpected keyword argument '{}'",
            remaining[0].0
        )));
    }

    let mut bound_args = Vec::new();
    let mut bound_kwargs = Vec::new();

    for (index, param) in signature.params.iter().enumerate() {
        match param.kind {
            ParamKind::PosOnly | ParamKind::PosOrKw => {
                let value = assigned[index]
                    .take()
                    .expect("positional argument must be assigned");
                bound_args.push(value);
            }
            ParamKind::KwOnly => {
                let value = assigned[index]
                    .take()
                    .expect("keyword-only argument must be assigned");
                bound_kwargs.push((param.name.clone(), value));
            }
            ParamKind::VarKw => bound_kwargs.append(&mut remaining),
        }
    }

    Ok((bound_args, bound_kwargs))
}

fn clone_py_vec(py: Python<'_>, values: &[Py<PyAny>]) -> Vec<Py<PyAny>> {
    values.iter().map(|value| value.clone_ref(py)).collect()
}

fn clone_kwarg_vec(py: Python<'_>, values: &[(String, Py<PyAny>)]) -> Vec<(String, Py<PyAny>)> {
    values
        .iter()
        .map(|(key, value)| (key.clone(), value.clone_ref(py)))
        .collect()
}

fn copy_py_vec(
    py: Python<'_>,
    copy_module: &Bound<'_, PyModule>,
    values: &[Py<PyAny>],
) -> PyResult<Vec<Py<PyAny>>> {
    values
        .iter()
        .map(|value| copy_module.call_method1("copy", (value.bind(py),)).map(Bound::unbind))
        .collect()
}

fn copy_kwarg_vec(
    py: Python<'_>,
    copy_module: &Bound<'_, PyModule>,
    values: &[(String, Py<PyAny>)],
) -> PyResult<Vec<(String, Py<PyAny>)>> {
    values
        .iter()
        .map(|(key, value)| {
            Ok((
                key.clone(),
                copy_module.call_method1("copy", (value.bind(py),))?.unbind(),
            ))
        })
        .collect()
}

fn dict_from_string_items<'py>(
    py: Python<'py>,
    values: &[(String, Py<PyAny>)],
) -> PyResult<Bound<'py, PyDict>> {
    let dict = PyDict::new(py);
    for (key, value) in values {
        dict.set_item(key, value.bind(py))?;
    }
    Ok(dict)
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
    let kind = { slf.borrow().kind };
    if kind == ComponentKind::Func {
        if let Some(key) = render_cache_key(slf)? {
            if let Some(cached) = render_cache_get_safe(py, &key) {
                return Ok(cached);
            }

            let rendered = render_instance_to_string_uncached(slf, kind)?;
            let safe_rendered = safe_from_string(py, rendered.clone())?;
            if render_cache_should_store(&key) {
                render_cache_set(py, key, rendered, &safe_rendered);
            }
            return Ok(safe_rendered);
        }
    }

    let rendered = render_instance_to_string_uncached(slf, kind)?;
    safe_from_string(py, rendered)
}

fn render_instance_to_string(slf: &Bound<'_, RustComponent>) -> PyResult<String> {
    let py = slf.py();
    let kind = { slf.borrow().kind };
    if kind == ComponentKind::Func {
        if let Some(key) = render_cache_key(slf)? {
            if let Some(cached) = render_cache_get_string(&key) {
                return Ok(cached);
            }

            let rendered = render_instance_to_string_uncached(slf, kind)?;
            let safe_rendered = safe_from_string(py, rendered.clone())?;
            if render_cache_should_store(&key) {
                render_cache_set(py, key, rendered.clone(), &safe_rendered);
            }
            return Ok(rendered);
        }
    }

    render_instance_to_string_uncached(slf, kind)
}

fn render_instance_to_string_uncached(
    slf: &Bound<'_, RustComponent>,
    kind: ComponentKind,
) -> PyResult<String> {
    match kind {
        ComponentKind::Void => render_void_to_string(slf),
        ComponentKind::Element => render_element_to_string(slf),
        ComponentKind::Func => render_func_component_to_string(slf),
        ComponentKind::Class => render_class_component_to_string(slf),
        ComponentKind::Comment => render_comment_to_string(slf),
        ComponentKind::Unknown => Ok(String::new()),
    }
}

fn render_cache_get_safe(py: Python<'_>, key: &RenderCacheKey) -> Option<Py<PyAny>> {
    RENDER_CACHE.with(|cache| {
        cache
            .borrow()
            .get(key)
            .map(|entry| entry.safe.clone_ref(py))
    })
}

fn render_cache_get_string(key: &RenderCacheKey) -> Option<String> {
    RENDER_CACHE.with(|cache| cache.borrow().get(key).map(|entry| entry.rendered.clone()))
}

fn render_cache_should_store(key: &RenderCacheKey) -> bool {
    let mut hasher = DefaultHasher::new();
    key.hash(&mut hasher);
    let fingerprint = hasher.finish();
    RENDER_CACHE_ADMISSIONS.with(|admissions| {
        let mut admissions = admissions.borrow_mut();
        if admissions.contains(&fingerprint) {
            return true;
        }
        if admissions.len() >= MAX_RENDER_CACHE_ENTRIES * 2 {
            admissions.clear();
        }
        admissions.insert(fingerprint);
        false
    })
}

fn render_cache_set(
    py: Python<'_>,
    key: RenderCacheKey,
    rendered: String,
    safe: &Py<PyAny>,
) {
    RENDER_CACHE.with(|cache| {
        let mut cache = cache.borrow_mut();
        if cache.len() >= MAX_RENDER_CACHE_ENTRIES {
            cache.clear();
        }
        cache.insert(
            key,
            RenderedCacheEntry {
                rendered,
                safe: safe.clone_ref(py),
            },
        );
    });
}

fn render_cache_key(slf: &Bound<'_, RustComponent>) -> PyResult<Option<RenderCacheKey>> {
    let mut builder = RenderCacheKeyBuilder {
        remaining_values: MAX_RENDER_CACHE_KEY_VALUES,
    };
    component_cache_key(slf, &mut builder, MAX_RENDER_CACHE_KEY_DEPTH)
}

fn component_cache_key(
    slf: &Bound<'_, RustComponent>,
    builder: &mut RenderCacheKeyBuilder,
    depth: usize,
) -> PyResult<Option<RenderCacheKey>> {
    let py = slf.py();
    let borrowed = slf.borrow();
    let type_ptr = slf.as_any().get_type().as_ptr() as usize;

    let mut keyed_args = Vec::with_capacity(borrowed.args.len());
    for value in &borrowed.args {
        let Some(key) = builder.value_key(value.bind(py), depth)? else {
            return Ok(None);
        };
        keyed_args.push(key);
    }

    let mut keyed_kwargs = Vec::with_capacity(borrowed.kwargs.len());
    for (name, value) in &borrowed.kwargs {
        let Some(key) = builder.value_key(value.bind(py), depth)? else {
            return Ok(None);
        };
        keyed_kwargs.push((name.clone(), key));
    }

    let mut keyed_children = Vec::with_capacity(borrowed.children.len());
    for value in &borrowed.children {
        let Some(key) = builder.value_key(value.bind(py), depth)? else {
            return Ok(None);
        };
        keyed_children.push(key);
    }

    Ok(Some(RenderCacheKey {
        type_ptr,
        args: keyed_args,
        kwargs: keyed_kwargs,
        children: keyed_children,
    }))
}

impl RenderCacheKeyBuilder {
    fn spend_value(&mut self) -> Option<()> {
        if self.remaining_values == 0 {
            return None;
        }
        self.remaining_values -= 1;
        Some(())
    }

    fn value_key(
        &mut self,
        value: &Bound<'_, PyAny>,
        depth: usize,
    ) -> PyResult<Option<CacheValue>> {
        if depth == 0 || self.spend_value().is_none() {
            return Ok(None);
        }

        let py = value.py();
        if value.is_none() {
            return Ok(Some(CacheValue::None));
        }

        if let Ok(value_bool) = value.downcast::<PyBool>() {
            return Ok(Some(CacheValue::Bool(value_bool.extract()?)));
        }

        let value_type = value.get_type().as_ptr();
        if value_type == py.get_type::<PyString>().as_ptr()
            || value_type == py.get_type::<PyInt>().as_ptr()
            || value_type == py.get_type::<PyFloat>().as_ptr()
        {
            return Ok(Some(CacheValue::Identity {
                ptr: value.as_ptr() as usize,
                _owner: value.clone().unbind(),
            }));
        }

        if let Ok(value_string) = value.downcast::<PyString>() {
            let string = value_string.to_string_lossy().into_owned();
            if is_safe_or_markup_value(py, value)? {
                return Ok(Some(CacheValue::SafeStr(string)));
            }
            return Ok(Some(CacheValue::Str(string)));
        }

        if let Ok(value_int) = value.downcast::<PyInt>() {
            if let Ok(value_i64) = value_int.extract::<i64>() {
                return Ok(Some(CacheValue::Int64(value_i64)));
            }
            return Ok(Some(CacheValue::Int(
                value.str()?.to_string_lossy().into_owned(),
            )));
        }

        if value.downcast::<PyFloat>().is_ok() {
            return Ok(Some(CacheValue::Float(
                value.repr()?.to_string_lossy().into_owned(),
            )));
        }

        if let Ok(component) = value.downcast::<RustComponent>() {
            let Some(key) = component_cache_key(component, self, depth - 1)? else {
                return Ok(None);
            };
            return Ok(Some(CacheValue::Component(Box::new(key))));
        }

        if let Ok(tuple) = value.downcast::<PyTuple>() {
            let Some(items) = self.sequence_key(tuple.iter(), depth)? else {
                return Ok(None);
            };
            return Ok(Some(CacheValue::Tuple(items)));
        }

        if let Ok(list) = value.downcast::<PyList>() {
            let Some(items) = self.sequence_key(list.iter(), depth)? else {
                return Ok(None);
            };
            return Ok(Some(CacheValue::List(items)));
        }

        if let Ok(dict) = value.downcast::<PyDict>() {
            let mut items = Vec::with_capacity(dict.len());
            for (key, item_value) in dict.iter() {
                let Some(key) = self.value_key(&key, depth - 1)? else {
                    return Ok(None);
                };
                let Some(item_value) = self.value_key(&item_value, depth - 1)? else {
                    return Ok(None);
                };
                items.push((key, item_value));
            }
            return Ok(Some(CacheValue::Dict(items)));
        }

        Ok(None)
    }

    fn sequence_key<'py>(
        &mut self,
        iter: impl Iterator<Item = Bound<'py, PyAny>>,
        depth: usize,
    ) -> PyResult<Option<Vec<CacheValue>>> {
        let mut items = Vec::new();
        for item in iter {
            let Some(key) = self.value_key(&item, depth - 1)? else {
                return Ok(None);
            };
            items.push(key);
        }
        Ok(Some(items))
    }
}

fn render_children(slf: &Bound<'_, RustComponent>) -> PyResult<Py<PyAny>> {
    let py = slf.py();
    let rendered = render_children_to_string(slf)?;
    if rendered.is_empty() {
        return safe_empty(py);
    }
    safe_from_string(py, rendered)
}

fn render_children_to_string(slf: &Bound<'_, RustComponent>) -> PyResult<String> {
    let py = slf.py();
    let children = {
        let borrowed = slf.borrow();
        if borrowed.children.is_empty() {
            return Ok(String::new());
        }
        clone_py_vec(py, &borrowed.children)
    };
    let mut rendered = String::new();
    for child in children {
        rendered.push_str(&render_value_to_string(child.bind(py))?);
    }
    Ok(rendered)
}

fn render_value_to_string(value: &Bound<'_, PyAny>) -> PyResult<String> {
    if let Ok(component) = value.downcast::<RustComponent>() {
        return render_instance_to_string(component);
    }
    escape_to_string(value)
}

fn render_element_to_string(slf: &Bound<'_, RustComponent>) -> PyResult<String> {
    let py = slf.py();
    let (name, attributes) = {
        let borrowed = slf.borrow();
        let name = borrowed
            .name
            .clone()
            .expect("initialized element must have a name");
        if simple_attribute_values(py, &borrowed.kwargs) {
            let attributes = render_attributes_from_pairs(py, &borrowed.kwargs)?;
            (name, attributes)
        } else {
            let kwargs = clone_kwarg_vec(py, &borrowed.kwargs);
            drop(borrowed);
            let attributes = render_attributes_from_pairs(py, &kwargs)?;
            let children = render_children_to_string(slf)?;
            return Ok(render_element_string(&name, &attributes, &children));
        }
    };
    let children = render_children_to_string(slf)?;
    Ok(render_element_string(&name, &attributes, &children))
}

fn render_void_to_string(slf: &Bound<'_, RustComponent>) -> PyResult<String> {
    let py = slf.py();
    let (name, attributes) = {
        let borrowed = slf.borrow();
        let name = borrowed
            .name
            .clone()
            .expect("initialized void element must have a name");
        if simple_attribute_values(py, &borrowed.kwargs) {
            let attributes = render_attributes_from_pairs(py, &borrowed.kwargs)?;
            (name, attributes)
        } else {
            let kwargs = clone_kwarg_vec(py, &borrowed.kwargs);
            drop(borrowed);
            let attributes = render_attributes_from_pairs(py, &kwargs)?;
            return Ok(render_void_string(&name, &attributes));
        }
    };
    Ok(render_void_string(&name, &attributes))
}

fn render_element_string(name: &str, attributes: &str, children: &str) -> String {
    let mut rendered = String::with_capacity(name.len() * 2 + attributes.len() + children.len() + 5);
    rendered.push('<');
    rendered.push_str(name);
    rendered.push_str(attributes);
    rendered.push('>');
    rendered.push_str(children);
    rendered.push_str("</");
    rendered.push_str(name);
    rendered.push('>');
    rendered
}

fn render_void_string(name: &str, attributes: &str) -> String {
    let mut rendered = String::with_capacity(name.len() + attributes.len() + 4);
    rendered.push('<');
    rendered.push_str(name);
    rendered.push_str(attributes);
    rendered.push_str(" />");
    rendered
}

fn simple_attribute_values(py: Python<'_>, values: &[(String, Py<PyAny>)]) -> bool {
    values
        .iter()
        .all(|(_, value)| simple_attribute_value(py, value.bind(py), 8))
}

fn simple_attribute_value(py: Python<'_>, value: &Bound<'_, PyAny>, depth: usize) -> bool {
    if depth == 0 {
        return false;
    }

    if value.is_none()
        || value.downcast::<PyBool>().is_ok()
        || value.downcast::<PyInt>().is_ok()
        || value.downcast::<PyFloat>().is_ok()
        || value.get_type().as_ptr() == py.get_type::<PyString>().as_ptr()
    {
        return true;
    }

    if let Ok(tuple) = value.downcast::<PyTuple>() {
        return tuple
            .iter()
            .all(|item| simple_attribute_value(py, &item, depth - 1));
    }

    if let Ok(list) = value.downcast::<PyList>() {
        return list
            .iter()
            .all(|item| simple_attribute_value(py, &item, depth - 1));
    }

    false
}

fn call_func_component(slf: &Bound<'_, RustComponent>) -> PyResult<Py<PyAny>> {
    let py = slf.py();
    {
        let borrowed = slf.borrow();
        if !borrowed.pass_children && borrowed.kwargs.is_empty() {
            let func = borrowed.func.as_ref().map(|func| func.clone_ref(py)).ok_or_else(|| {
                PyAttributeError::new_err("function component has no callable")
            })?;
            let args = PyTuple::new(py, borrowed.args.iter().map(|arg| arg.bind(py).clone()))?;
            drop(borrowed);
            return func.bind(py).call(&args, None).map(Bound::unbind);
        }
    }

    let (func, pass_children, children_positional_index, mut args, kwargs) = {
        let borrowed = slf.borrow();
        (
            borrowed.func.as_ref().map(|func| func.clone_ref(py)).ok_or_else(|| {
                PyAttributeError::new_err("function component has no callable")
            })?,
            borrowed.pass_children,
            borrowed.children_positional_index,
            clone_py_vec(py, &borrowed.args),
            clone_kwarg_vec(py, &borrowed.kwargs),
        )
    };

    let children = if pass_children {
        Some(render_children(slf)?)
    } else {
        None
    };
    if let (Some(index), Some(children)) = (children_positional_index, &children) {
        args.insert(index, children.clone_ref(py));
    }
    let args = PyTuple::new(py, args)?;

    if kwargs.is_empty() && (!pass_children || children_positional_index.is_some()) {
        return func.bind(py).call(&args, None).map(Bound::unbind);
    }

    let call_kwargs = dict_from_string_items(py, &kwargs)?;
    if pass_children && children_positional_index.is_none() {
        call_kwargs.set_item(
            "children",
            children
                .as_ref()
                .expect("children must be rendered when pass_children is true"),
        )?;
    }
    func.bind(py).call(&args, Some(&call_kwargs)).map(Bound::unbind)
}

fn render_func_component_to_string(slf: &Bound<'_, RustComponent>) -> PyResult<String> {
    let py = slf.py();
    let content = call_func_component(slf)?;
    render_value_to_string(content.bind(py))
}

fn render_class_component_to_string(slf: &Bound<'_, RustComponent>) -> PyResult<String> {
    let py = slf.py();
    let pass_children = { slf.borrow().pass_children };
    let user_instance = get_or_create_user_instance(slf)?;
    let content = if pass_children {
        user_instance
            .bind(py)
            .call_method1("render", (render_children(slf)?,))?
    } else {
        user_instance.bind(py).call_method0("render")?
    };
    render_value_to_string(&content)
}

fn render_comment_to_string(slf: &Bound<'_, RustComponent>) -> PyResult<String> {
    let py = slf.py();
    let mut content = String::new();
    for child in &slf.borrow().children {
        content.push_str(&child.bind(py).str()?.to_string_lossy());
    }
    Ok(format!("<-- {content} -->"))
}

fn get_or_create_user_instance(slf: &Bound<'_, RustComponent>) -> PyResult<Py<PyAny>> {
    let py = slf.py();
    {
        let borrowed = slf.borrow();
        if let Some(instance) = &borrowed.user_instance {
            return Ok(instance.clone_ref(py));
        }
    }

    let (user_class, args, kwargs) = {
        let borrowed = slf.borrow();
        (
            borrowed
                .user_class
                .as_ref()
                .map(|user_class| user_class.clone_ref(py))
                .ok_or_else(|| PyAttributeError::new_err("class component has no class"))?,
            clone_py_vec(py, &borrowed.args),
            clone_kwarg_vec(py, &borrowed.kwargs),
        )
    };
    let args = PyTuple::new(py, args)?;
    let kwargs = dict_from_string_items(py, &kwargs)?;
    let instance = user_class.bind(py).call(&args, Some(&kwargs))?.unbind();
    slf.borrow_mut().user_instance = Some(instance.clone_ref(py));
    Ok(instance)
}

fn validate_list_children(obj: &Bound<'_, PyAny>, children: &[Py<PyAny>]) -> PyResult<()> {
    let list_only = obj.downcast::<RustComponent>()?.borrow().list_only;
    if !list_only {
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
    if value.downcast::<PyString>().is_ok() {
        return Ok(vec![value.clone().unbind()]);
    }

    let iterator = match PyIterator::from_object(value) {
        Ok(iterator) => iterator,
        Err(error) if error.is_instance_of::<PyTypeError>(value.py()) => {
            return Ok(vec![value.clone().unbind()]);
        }
        Err(error) => return Err(error),
    };
    let mut children = Vec::with_capacity(iterator.size_hint().0);
    for child in iterator {
        children.push(child?.unbind());
    }
    Ok(children)
}

pub fn get_bound_args_object(slf: &Bound<'_, RustComponent>) -> PyResult<Py<PyAny>> {
    let py = slf.py();
    {
        let borrowed = slf.borrow();
        if let Some(bound_args) = &borrowed.bound_args {
            return Ok(bound_args.clone_ref(py));
        }
    }

    let (args, kwargs) = {
        let borrowed = slf.borrow();
        (
            clone_py_vec(py, &borrowed.args),
            clone_kwarg_vec(py, &borrowed.kwargs),
        )
    };
    let args = PyTuple::new(py, args)?;
    let kwargs = dict_from_string_items(py, &kwargs)?;
    let bound_args = bind_args(slf.as_any(), &args, Some(&kwargs))?.unbind();
    slf.borrow_mut().bound_args = Some(bound_args.clone_ref(py));
    Ok(bound_args)
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

fn contains_python_keyword(kwargs: &Bound<'_, PyDict>) -> PyResult<bool> {
    for key in kwargs.keys() {
        let name: String = key.extract()?;
        if is_python_keyword(&name) {
            return Ok(true);
        }
    }
    Ok(false)
}

pub fn check_keywords(func: &Bound<'_, PyAny>, kwargs: Option<&Bound<'_, PyDict>>) -> PyResult<()> {
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
    check_keywords_for_name(kwargs, &module_name, &func_name)
}

fn check_keywords_for_name(
    kwargs: Option<&Bound<'_, PyDict>>,
    module_name: &str,
    func_name: &str,
) -> PyResult<()> {
    let Some(kwargs) = kwargs else {
        return Ok(());
    };
    if kwargs.is_empty() {
        return Ok(());
    }

    for key in kwargs.keys() {
        let name: String = key.extract()?;
        if is_python_keyword(&name) {
            return Err(PySyntaxError::new_err(format!(
                "keyword: {name:?} cannot be used as argument name in {module_name}.{func_name}, use an underscore at the end instead"
            )));
        }
    }

    Ok(())
}

pub fn build_props_dict<'py>(slf: &Bound<'py, RustComponent>) -> PyResult<Bound<'py, PyDict>> {
    let py = slf.py();
    let props = PyDict::new(py);
    let borrowed = slf.borrow();
    if let Some(positional_args) = &borrowed.positional_args {
        for (key, value) in positional_args.iter().zip(&borrowed.args) {
            if !value.bind(py).is_none() {
                props.set_item(key, value.bind(py))?;
            }
        }
    }

    for (key, value) in &borrowed.kwargs {
        if !value.bind(py).is_none() {
            props.set_item(key, value.bind(py))?;
        }
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
    let (mut args, mut kwargs, positional_args) = {
        let borrowed = slf.borrow();
        (
            copy_py_vec(py, &copy_module, &borrowed.args)?,
            copy_kwarg_vec(py, &copy_module, &borrowed.kwargs)?,
            borrowed.positional_args.clone(),
        )
    };

    for (key, value) in new_arguments.iter() {
        let key: String = key.extract()?;
        let mut handled = false;
        if let Some(index) = positional_args
            .as_deref()
            .and_then(|names| names.iter().position(|name| name == &key))
        {
            args[index] = value.clone().unbind();
            handled = true;
        }
        if let Some((_, existing)) = kwargs.iter_mut().find(|(name, _)| name == &key) {
            *existing = value.clone().unbind();
            handled = true;
        }
        if !handled
            && !positional_args
                .as_deref()
                .is_some_and(|names| names.contains(&key))
        {
            kwargs.push((key, value.clone().unbind()));
        }
    }

    let args = PyTuple::new(py, args.iter().map(|arg| arg.bind(py).clone()))?;
    let kwargs = dict_from_string_items(py, &kwargs)?;
    slf.as_any().get_type().call(&args, Some(&kwargs)).map(Bound::unbind)
}

fn make_new_with_same_arguments(slf: &Bound<'_, RustComponent>) -> PyResult<Py<PyAny>> {
    clone_component(slf)
}

fn clone_component(slf: &Bound<'_, RustComponent>) -> PyResult<Py<PyAny>> {
    let py = slf.py();
    let cls = slf.as_any().get_type();
    let new = cls.getattr("__new__")?.call1((cls,))?;
    let new_component = new.downcast::<RustComponent>()?;

    let borrowed = slf.borrow();
    let mut target = new_component.borrow_mut();
    target.bound_args = None;
    target.args = clone_py_vec(py, &borrowed.args);
    target.kwargs = clone_kwarg_vec(py, &borrowed.kwargs);
    target.children.clear();
    target.original_kwargs = borrowed
        .original_kwargs
        .as_ref()
        .map(|kwargs| clone_kwarg_vec(py, kwargs));
    target.parent = None;
    target.user_instance = None;
    target.kind = borrowed.kind;
    target.name = borrowed.name.clone();
    target.html = borrowed.html;
    target.list_only = borrowed.list_only;
    target.pass_children = borrowed.pass_children;
    target.children_positional_index = borrowed.children_positional_index;
    target.positional_args = borrowed.positional_args.clone();
    target.func = borrowed.func.as_ref().map(|func| func.clone_ref(py));
    target.user_class = borrowed
        .user_class
        .as_ref()
        .map(|user_class| user_class.clone_ref(py));
    drop(target);
    drop(borrowed);

    Ok(new.unbind())
}

pub fn class_kind(obj: &Bound<'_, PyAny>) -> PyResult<String> {
    class_string_attr(obj, "_kind")
}

pub fn class_string_attr(obj: &Bound<'_, PyAny>, attr: &str) -> PyResult<String> {
    obj.get_type().getattr(attr)?.extract()
}

pub fn empty_signature(py: Python<'_>) -> PyResult<Py<PyAny>> {
    let inspect = py.import("inspect")?;
    let parameter_cls = inspect.getattr("Parameter")?;
    let var_keyword = parameter_cls.getattr("VAR_KEYWORD")?;
    let param = parameter_cls.call1(("kwargs", var_keyword))?;
    let params = PyList::new(py, [param])?;
    inspect.getattr("Signature")?.call1((params,)).map(Bound::unbind)
}

pub fn empty_param_specs(py: Python<'_>) -> PyResult<Py<PyAny>> {
    let specs = PyList::empty(py);
    let spec = PyTuple::new(
        py,
        [
            "kwargs".into_pyobject(py)?.into_any().unbind(),
            3_u8.into_pyobject(py)?.into_any().unbind(),
            PyBool::new(py, false).to_owned().into_any().unbind(),
            py.None(),
        ],
    )?;
    specs.append(spec)?;
    Ok(specs.unbind().into_any())
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
    let (parameters, pass_children, children_positional_index, var_keyword) = filter_signature(
        &orig_sig,
        |name| name != "children",
        true,
    )?;
    let param_specs = build_param_specs(parameters.bind(py))?;
    let sig = py
        .import("inspect")?
        .getattr("Signature")?
        .call1((parameters.bind(py),))?;
    let attrs = PyDict::new(py);
    attrs.set_item("_kind", "func")?;
    attrs.set_item("_func", func)?;
    attrs.set_item("_sig", sig)?;
    attrs.set_item("_param_specs", param_specs)?;
    attrs.set_item("_positional_args", positional_args)?;
    attrs.set_item("_var_keyword", var_keyword)?;
    attrs.set_item("_pass_children", pass_children)?;
    attrs.set_item("_children_positional_index", children_positional_index)?;
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
    let (parameters, _, _, var_keyword) = filter_signature(
        &orig_sig,
        |name| name != "self" && name != "children",
        false,
    )?;
    let param_specs = build_param_specs(parameters.bind(py))?;
    let sig = py
        .import("inspect")?
        .getattr("Signature")?
        .call1((parameters.bind(py),))?;
    let render = user_class.getattr("render")?;
    let render_sig = py.import("inspect")?.getattr("signature")?.call1((&render,))?;
    let pass_children = signature_has_parameter(&render_sig, "children")?;
    let attrs = PyDict::new(py);
    attrs.set_item("_kind", "class")?;
    attrs.set_item("_user_class", user_class)?;
    attrs.set_item("_render_func", render)?;
    attrs.set_item("_sig", sig)?;
    attrs.set_item("_param_specs", param_specs)?;
    attrs.set_item("_positional_args", positional_args)?;
    attrs.set_item("_var_keyword", var_keyword)?;
    attrs.set_item("_pass_children", pass_children)?;
    attrs.set_item("_children_positional_index", py.None())?;
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
) -> PyResult<(Py<PyAny>, bool, Option<usize>, Option<String>)>
where
    F: Fn(&str) -> bool,
{
    let py = sig.py();
    let parameter_cls = py.import("inspect")?.getattr("Parameter")?;
    let pos_only_kind = parameter_cls.getattr("POSITIONAL_ONLY")?;
    let pos_or_kw_kind = parameter_cls.getattr("POSITIONAL_OR_KEYWORD")?;
    let var_keyword_kind = parameter_cls.getattr("VAR_KEYWORD")?;
    let parameters = PyList::empty(py);
    let mut pass_children = false;
    let mut children_positional_index = None;
    let mut positional_index = 0_usize;
    let mut var_keyword = None;
    let parameters_mapping = sig.getattr("parameters")?;
    for item in parameters_mapping.call_method0("items")?.try_iter()? {
        let item = item?;
        let pair = item.downcast::<PyTuple>()?;
        let name: String = pair.get_item(0)?.extract()?;
        let param = pair.get_item(1)?;
        let kind = param.getattr("kind")?;
        let positional = kind.eq(&pos_only_kind)? || kind.eq(&pos_or_kw_kind)?;
        if track_children && name == "children" {
            pass_children = true;
            if positional {
                children_positional_index = Some(positional_index);
            }
        }
        if kind.eq(&var_keyword_kind)? {
            var_keyword = Some(name.clone());
        }
        if include(&name) {
            parameters.append(param)?;
            if positional {
                positional_index += 1;
            }
        }
    }
    Ok((
        parameters.unbind().into_any(),
        pass_children,
        children_positional_index,
        var_keyword,
    ))
}

fn build_param_specs(parameters: &Bound<'_, PyAny>) -> PyResult<Py<PyAny>> {
    let py = parameters.py();
    let parameter_cls = py.import("inspect")?.getattr("Parameter")?;
    let pos_only = parameter_cls.getattr("POSITIONAL_ONLY")?;
    let pos_or_kw = parameter_cls.getattr("POSITIONAL_OR_KEYWORD")?;
    let kw_only = parameter_cls.getattr("KEYWORD_ONLY")?;
    let var_kw = parameter_cls.getattr("VAR_KEYWORD")?;
    let empty = parameter_cls.getattr("empty")?;
    let specs = PyList::empty(py);

    for param in parameters.try_iter()? {
        let param = param?;
        let name: String = param.getattr("name")?.extract()?;
        let kind = param.getattr("kind")?;
        let kind_code = if kind.eq(&pos_only)? {
            0_u8
        } else if kind.eq(&pos_or_kw)? {
            1_u8
        } else if kind.eq(&kw_only)? {
            2_u8
        } else if kind.eq(&var_kw)? {
            3_u8
        } else {
            continue;
        };
        let default = param.getattr("default")?;
        let has_default = !default.eq(&empty)?;
        let spec = PyTuple::new(
            py,
            [
                name.into_pyobject(py)?.into_any().unbind(),
                kind_code.into_pyobject(py)?.into_any().unbind(),
                PyBool::new(py, has_default).to_owned().into_any().unbind(),
                default.unbind(),
            ],
        )?;
        specs.append(spec)?;
    }

    Ok(specs.unbind().into_any())
}

fn signature_has_parameter(sig: &Bound<'_, PyAny>, name: &str) -> PyResult<bool> {
    sig.getattr("parameters")?.contains(name)
}
