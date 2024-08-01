class Event:
    """Events can be used to modify and enhance HTMX behavior."""

    ABORT = "htmx:abort"
    """send this event to an element to abort a request"""

    AFTER_ON_LOAD = "htmx:after-on-load"
    """triggered after an AJAX request has completed processing a successful response"""

    AFTER_PROCESS_NODE = "htmx:after-process-node"
    """triggered after htmx has initialized a node"""

    AFTER_REQUEST = "htmx:after-request"
    """triggered after an AJAX request has completed"""

    AFTER_SETTLE = "htmx:after-settle"
    """triggered after the DOM has settled"""

    AFTER_SWAP = "htmx:after-swap"
    """triggered after new content has been swapped in"""

    BEFORE_CLEANUP_ELEMENT = "htmx:before-cleanup-element"
    """triggered before htmx disables an element or removes it from the DOM"""

    BEFORE_ON_LOAD = "htmx:before-on-load"
    """triggered before any response processing occurs"""

    BEFORE_PROCESS_NODE = "htmx:before-process-node"
    """triggered before htmx initializes a node"""

    BEFORE_REQUEST = "htmx:before-request"
    """triggered before an AJAX request is made"""

    BEFORE_SWAP = "htmx:before-swap"
    """triggered before a swap is done, allows you to configure the swap"""

    BEFORE_SEND = "htmx:before-send"
    """triggered just before an ajax request is sent"""

    CONFIG_REQUEST = "htmx:config-request"
    """triggered before the request, allows you to customize parameters, headers"""

    CONFIRM = "htmx:confirm"
    """triggered after a trigger occurs on an element,
    allows you to cancel (or delay) issuing the AJAX request"""

    HISTORY_CACHE_ERROR = "htmx:history-cache-error"
    """triggered on an error during cache writing"""

    HISTORY_CACHE_MISS = "htmx:history-cache-miss"
    """triggered on a cache miss in the history subsystem"""

    HISTORY_CACHE_MISS_ERROR = "htmx:history-cache-miss-error"
    """triggered on a unsuccessful remote retrieval"""

    HISTORY_CACHE_MISS_LOAD = "htmx:history-cache-miss-load"
    """triggered on a successful remote retrieval"""

    HISTORY_RESTORE = "htmx:history-restore"
    """triggered when htmx handles a history restoration action"""

    BEFORE_HISTORY_SAVE = "htmx:before-history-save"
    """triggered before content is saved to the history cache"""

    LOAD = "htmx:load"
    """triggered when new content is added to the DOM"""

    NO_SSE_SOURCE_ERROR = "htmx:no-sse-source-error"
    """triggered when an element refers to a SSE event in its trigger,
       but no parent SSE source has been defined
    """

    ON_LOAD_ERROR = "htmx:on-load-error"
    """triggered when an exception occurs during the onLoad handling in htmx"""

    OOB_AFTER_SWAP = "htmx:oob-after-swap"
    """triggered after an out of band element as been swapped in"""

    OOB_BEFORE_SWAP = "htmx:oob-before-swap"
    """triggered before an out of band element swap is done,
       allows you to configure the swap
    """

    OOB_ERROR_NO_TARGET = "htmx:oob-error-no-target"
    """triggered when an out of band element does not have a matching ID
       in the current DOM
    """

    PROMPT = "htmx:prompt"
    """triggered after a prompt is shown"""

    PUSHED_INTO_HISTORY = "htmx:pushed-into-history"
    """triggered after an url is pushed into history"""

    RESPONSE_ERROR = "htmx:response-error"
    """triggered when an HTTP response error (non-200 or 300 response code) occurs"""

    SEND_ERROR = "htmx:send-error"
    """triggered when a network error prevents an HTTP request from happening"""

    SSE_ERROR = "htmx:sse-error"
    """triggered when an error occurs with a SSE source"""

    SSE_OPEN = "htmx:sse-open"
    """triggered when a SSE source is opened"""

    SWAP_ERROR = "htmx:swap-error"
    """triggered when an error occurs during the swap phase"""

    TARGET_ERROR = "htmx:target-error"
    """triggered when an invalid target is specified"""

    TIMEOUT = "htmx:timeout"
    """triggered when a request timeout occurs"""

    VALIDATION_VALIDATE = "htmx:validation:validate"
    """triggered before an element is validated"""

    VALIDATION_FAILED = "htmx:validation:failed"
    """triggered when an element fails validation"""

    VALIDATION_HALTED = "htmx:validation:halted"
    """triggered when a request is halted due to validation errors"""

    XHR_ABORT = "htmx:xhr:abort"
    """triggered when an ajax request aborts"""

    XHR_LOAD_END = "htmx:xhr:loadend"
    """triggered when an ajax request ends"""

    XHR_LOAD_START = "htmx:xhr:loadstart"
    """triggered when an ajax request starts"""

    XHR_PROGRESS = "htmx:xhr:progress"
    """triggered periodically during an ajax request that supports progress events"""


class Swap:
    """The hx-swap attribute allows you to specify how the response will be swapped
    in relative to the target of an AJAX request. If you do not specify the option,
    the default is htmx.config.defaultSwapStyle (innerHTML).
    See: https://htmx.org/attributes/hx-swap/
    """

    INNER_HTML = "innerHTML"
    OUTER_HTML = "outerHTML"
    BEFORE_BEGIN = "beforebegin"
    AFTER_BEGIN = "afterbegin"
    BEFORE_END = "beforeend"
    AFTER_END = "afterend"
    DELETE = "delete"
    NONE = "none"


class BinaryType:
    BLOB = "blob"
    ARRAYBUFFER = "arraybuffer"


class Scroll:
    AUTO = "auto"
    SMOOTH = "smooth"
