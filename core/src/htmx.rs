use pyo3::prelude::*;
use pyo3::types::{PyDict, PyModule, PyTuple};

use crate::component::make_func_component;
use crate::escape::safe_from_string;
use crate::python_package::{add_aliases, make_package, register_child};
use crate::utils::snake_to_camel_case;

const EVENTS: &[(&str, &str)] = &[
    ("ABORT", "htmx:abort"),
    ("AFTER_ON_LOAD", "htmx:after-on-load"),
    ("AFTER_PROCESS_NODE", "htmx:after-process-node"),
    ("AFTER_REQUEST", "htmx:after-request"),
    ("AFTER_SETTLE", "htmx:after-settle"),
    ("AFTER_SWAP", "htmx:after-swap"),
    ("BEFORE_CLEANUP_ELEMENT", "htmx:before-cleanup-element"),
    ("BEFORE_ON_LOAD", "htmx:before-on-load"),
    ("BEFORE_PROCESS_NODE", "htmx:before-process-node"),
    ("BEFORE_REQUEST", "htmx:before-request"),
    ("BEFORE_SWAP", "htmx:before-swap"),
    ("BEFORE_SEND", "htmx:before-send"),
    ("CONFIG_REQUEST", "htmx:config-request"),
    ("CONFIRM", "htmx:confirm"),
    ("HISTORY_CACHE_ERROR", "htmx:history-cache-error"),
    ("HISTORY_CACHE_MISS", "htmx:history-cache-miss"),
    ("HISTORY_CACHE_MISS_ERROR", "htmx:history-cache-miss-error"),
    ("HISTORY_CACHE_MISS_LOAD", "htmx:history-cache-miss-load"),
    ("HISTORY_RESTORE", "htmx:history-restore"),
    ("BEFORE_HISTORY_SAVE", "htmx:before-history-save"),
    ("LOAD", "htmx:load"),
    ("NO_SSE_SOURCE_ERROR", "htmx:no-sse-source-error"),
    ("ON_LOAD_ERROR", "htmx:on-load-error"),
    ("OOB_AFTER_SWAP", "htmx:oob-after-swap"),
    ("OOB_BEFORE_SWAP", "htmx:oob-before-swap"),
    ("OOB_ERROR_NO_TARGET", "htmx:oob-error-no-target"),
    ("PROMPT", "htmx:prompt"),
    ("PUSHED_INTO_HISTORY", "htmx:pushed-into-history"),
    ("RESPONSE_ERROR", "htmx:response-error"),
    ("SEND_ERROR", "htmx:send-error"),
    ("SSE_ERROR", "htmx:sse-error"),
    ("SSE_OPEN", "htmx:sse-open"),
    ("SWAP_ERROR", "htmx:swap-error"),
    ("TARGET_ERROR", "htmx:target-error"),
    ("TIMEOUT", "htmx:timeout"),
    ("VALIDATION_VALIDATE", "htmx:validation:validate"),
    ("VALIDATION_FAILED", "htmx:validation:failed"),
    ("VALIDATION_HALTED", "htmx:validation:halted"),
    ("XHR_ABORT", "htmx:xhr:abort"),
    ("XHR_LOAD_END", "htmx:xhr:loadend"),
    ("XHR_LOAD_START", "htmx:xhr:loadstart"),
    ("XHR_PROGRESS", "htmx:xhr:progress"),
];

const SWAPS: &[(&str, &str)] = &[
    ("INNER_HTML", "innerHTML"),
    ("OUTER_HTML", "outerHTML"),
    ("BEFORE_BEGIN", "beforebegin"),
    ("AFTER_BEGIN", "afterbegin"),
    ("BEFORE_END", "beforeend"),
    ("AFTER_END", "afterend"),
    ("DELETE", "delete"),
    ("NONE", "none"),
];

pub fn add_module(py: Python<'_>, root: &Bound<'_, PyModule>) -> PyResult<()> {
    let htmx = make_package(py, "compone.htmx")?;

    let constants = PyModule::new(py, "compone.htmx.constants")?;
    constants.add("Event", make_constant_class(py, "Event", EVENTS)?)?;
    constants.add("Swap", make_constant_class(py, "Swap", SWAPS)?)?;
    constants.add(
        "BinaryType",
        make_constant_class(py, "BinaryType", &[("BLOB", "blob"), ("ARRAYBUFFER", "arraybuffer")])?,
    )?;
    constants.add(
        "Scroll",
        make_constant_class(py, "Scroll", &[("AUTO", "auto"), ("SMOOTH", "smooth")])?,
    )?;
    register_child(py, &htmx, "constants", &constants)?;

    let config_module = PyModule::new(py, "compone.htmx.config")?;
    let config_function = wrap_pyfunction!(render_config, &config_module)?;
    let config = make_func_component(&config_function)?;
    config_module.add("Config", config)?;
    register_child(py, &htmx, "config", &config_module)?;

    add_aliases(
        &htmx,
        &constants,
        &["BinaryType", "Event", "Scroll", "Swap"],
    )?;
    add_aliases(&htmx, &config_module, &["Config"])?;
    register_child(py, root, "htmx", &htmx)
}

fn make_constant_class(
    py: Python<'_>,
    name: &str,
    values: &[(&str, &str)],
) -> PyResult<Py<PyAny>> {
    let attrs = PyDict::new(py);
    attrs.set_item("__module__", "compone.htmx.constants")?;
    for (key, value) in values {
        attrs.set_item(*key, *value)?;
    }
    py.import("builtins")?
        .getattr("type")?
        .call1((name, PyTuple::empty(py), attrs))
        .map(Bound::unbind)
}

#[pyfunction(
    name = "Config",
    signature = (
        *,
        history_enabled=None,
        history_cache_size=None,
        refresh_on_history_miss=None,
        default_swap_style=None,
        default_swap_delay=None,
        default_settle_delay=None,
        include_indicator_styles=None,
        indicator_class=None,
        request_class=None,
        added_class=None,
        settling_class=None,
        swapping_class=None,
        allow_eval=None,
        allow_script_tags=None,
        inline_script_nonce=None,
        attributes_to_settle=None,
        use_template_fragments=None,
        ws_reconnect_delay=None,
        ws_binary_type=None,
        disable_selector=None,
        with_credentials=None,
        timeout=None,
        scroll_behavior=None,
        default_focus_scroll=None,
        get_cache_buster_param=None,
        global_view_transitions=None,
        methods_that_use_url_params=None,
        self_requests_only=None,
        ignore_title=None,
        scroll_into_view_on_boost=None,
        trigger_specs_cache=None
    )
)]
#[allow(clippy::too_many_arguments)]
fn render_config(
    py: Python<'_>,
    history_enabled: Option<Py<PyAny>>,
    history_cache_size: Option<Py<PyAny>>,
    refresh_on_history_miss: Option<Py<PyAny>>,
    default_swap_style: Option<Py<PyAny>>,
    default_swap_delay: Option<Py<PyAny>>,
    default_settle_delay: Option<Py<PyAny>>,
    include_indicator_styles: Option<Py<PyAny>>,
    indicator_class: Option<Py<PyAny>>,
    request_class: Option<Py<PyAny>>,
    added_class: Option<Py<PyAny>>,
    settling_class: Option<Py<PyAny>>,
    swapping_class: Option<Py<PyAny>>,
    allow_eval: Option<Py<PyAny>>,
    allow_script_tags: Option<Py<PyAny>>,
    inline_script_nonce: Option<Py<PyAny>>,
    attributes_to_settle: Option<Py<PyAny>>,
    use_template_fragments: Option<Py<PyAny>>,
    ws_reconnect_delay: Option<Py<PyAny>>,
    ws_binary_type: Option<Py<PyAny>>,
    disable_selector: Option<Py<PyAny>>,
    with_credentials: Option<Py<PyAny>>,
    timeout: Option<Py<PyAny>>,
    scroll_behavior: Option<Py<PyAny>>,
    default_focus_scroll: Option<Py<PyAny>>,
    get_cache_buster_param: Option<Py<PyAny>>,
    global_view_transitions: Option<Py<PyAny>>,
    methods_that_use_url_params: Option<Py<PyAny>>,
    self_requests_only: Option<Py<PyAny>>,
    ignore_title: Option<Py<PyAny>>,
    scroll_into_view_on_boost: Option<Py<PyAny>>,
    trigger_specs_cache: Option<Py<PyAny>>,
) -> PyResult<Py<PyAny>> {
    let values = PyDict::new(py);

    macro_rules! add_value {
        ($value:ident) => {
            if let Some(value) = $value {
                values.set_item(snake_to_camel_case(stringify!($value)), value)?;
            }
        };
    }

    add_value!(history_enabled);
    add_value!(history_cache_size);
    add_value!(refresh_on_history_miss);
    add_value!(default_swap_style);
    add_value!(default_swap_delay);
    add_value!(default_settle_delay);
    add_value!(include_indicator_styles);
    add_value!(indicator_class);
    add_value!(request_class);
    add_value!(added_class);
    add_value!(settling_class);
    add_value!(swapping_class);
    add_value!(allow_eval);
    add_value!(allow_script_tags);
    add_value!(inline_script_nonce);
    add_value!(attributes_to_settle);
    add_value!(use_template_fragments);
    add_value!(ws_reconnect_delay);
    add_value!(ws_binary_type);
    add_value!(disable_selector);
    add_value!(with_credentials);
    add_value!(timeout);
    add_value!(scroll_behavior);
    add_value!(default_focus_scroll);
    add_value!(get_cache_buster_param);
    add_value!(global_view_transitions);
    add_value!(methods_that_use_url_params);
    add_value!(self_requests_only);
    add_value!(ignore_title);
    add_value!(scroll_into_view_on_boost);
    add_value!(trigger_specs_cache);

    if values.is_empty() {
        return Ok(py.None());
    }

    let json: String = py
        .import("json")?
        .getattr("dumps")?
        .call1((&values,))?
        .extract()?;
    let kwargs = PyDict::new(py);
    kwargs.set_item("name", "htmx-config")?;
    kwargs.set_item("content", safe_from_string(py, json)?)?;
    py.import("compone")?
        .getattr("html")?
        .getattr("Meta")?
        .call((), Some(&kwargs))
        .map(Bound::unbind)
}
