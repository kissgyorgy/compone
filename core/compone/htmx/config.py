import enum
import json
from typing import List, Optional

from .. import html
from ..component import Component
from ..escape import safe
from ..utils import snake_to_camel_case
from . import constants


@Component
def Config(
    *,
    history_enabled: Optional[bool] = None,
    history_cache_size: Optional[int] = None,
    refresh_on_history_miss: Optional[bool] = None,
    default_swap_style: Optional[constants.Swap] = None,
    default_swap_delay: Optional[int] = None,
    default_settle_delay: Optional[int] = None,
    include_indicator_styles: Optional[bool] = None,
    indicator_class: Optional[str] = None,
    request_class: Optional[str] = None,
    added_class: Optional[str] = None,
    settling_class: Optional[str] = None,
    swapping_class: Optional[str] = None,
    allow_eval: Optional[bool] = None,
    allow_script_tags: Optional[bool] = None,
    inline_script_nonce: Optional[str] = None,
    attributes_to_settle: Optional[List[str]] = None,
    use_template_fragments: Optional[bool] = None,
    ws_reconnect_delay: Optional[int] = None,
    ws_binary_type: Optional[constants.BinaryType] = None,
    disable_selector: Optional[str] = None,
    with_credentials: Optional[bool] = None,
    timeout: Optional[int] = None,
    scroll_behavior: Optional[constants.Scroll] = None,
    default_focus_scroll: Optional[bool] = None,
    get_cache_buster_param: Optional[bool] = None,
    global_view_transitions: Optional[bool] = None,
    methods_that_use_url_params: Optional[str] = None,
    self_requests_only: Optional[bool] = None,
    ignore_title: Optional[bool] = None,
    scroll_into_view_on_boost: Optional[bool] = None,
    trigger_specs_cache: Optional[str] = None,
):
    values = {}

    for key, value in locals().items():
        if value is None or key in ("self", "values"):
            continue
        if isinstance(value, enum.Enum):
            value = value.value

        camel_key = snake_to_camel_case(key)
        values[camel_key] = value

    if not values:
        return None

    json_values = json.dumps(values)
    return html.Meta(name="htmx-config", content=safe(json_values))
