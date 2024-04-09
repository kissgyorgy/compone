import copy
import inspect
import keyword
from contextvars import ContextVar
from functools import cached_property
from types import MappingProxyType
from typing import Callable, Iterable, Optional, Protocol, Tuple, Type, TypeVar, Union

from .escape import escape, safe
from .utils import _is_iterable

# previous frame id (frame.f_back), parent object
last_parent = ContextVar("last_parent", default=(None, None))

T = TypeVar("T")
CompSelf = TypeVar("CompSelf", bound="_ComponentBase")
ChildSelf = TypeVar("ChildSelf", bound="_ChildrenBase")
StrType = Union[str, safe]
ContentType = Union[StrType, CompSelf]


class ComponentClass(Protocol):
    def render(self, children: safe) -> Union[ContentType, Iterable[ContentType]]:
        ...


class _ComponentBase:
    _sig: inspect.Signature
    _positional_args: set[str]
    _defaults: Optional[dict] = None

    def __init__(self, *args, **kwargs):
        self._bound_args = self._sig.bind(*args, **kwargs)
        self._bound_args.apply_defaults()

    @property
    def props(self) -> dict:
        return MappingProxyType(
            {k: v for k, v in self._bound_args.arguments.items() if v is not None}
        )

    def replace(self, **kwargs) -> CompSelf:
        return self._merge(kwargs)

    def append(self, **kwargs) -> CompSelf:
        appended = {}
        for key, val in kwargs.items():
            if key in self.props:
                val = self.props[key] + val
            appended[key] = val
        return self._merge(appended)

    def merge(self, **kwargs) -> CompSelf:
        if overlapping := [key for key in kwargs if key in self.props]:
            overlapping_keys = ", ".join(overlapping)
            raise KeyError(
                f"{overlapping_keys} already specified in {self!r}, "
                "use the replace method if you want to replace arguments"
            )
        return self._merge(kwargs)

    def copy(self) -> CompSelf:
        return self._merge({})

    def __repr__(self):
        if self.props:
            proplist = ", ".join(f"{k}={v!r}" for k, v in self.props.items())
        else:
            proplist = ""
        return f"<{self.__class__.__name__}({proplist})>"

    def __mul__(self, other: int) -> CompSelf:
        if not isinstance(other, int):
            return NotImplemented

        # Every component is safe by default, so the result should be safe too
        Multiple = Component(lambda: safe(self) * other)
        Multiple.__name__ = "Multi" + self.__class__.__name__
        Multiple.__doc__ = "Multiple: " + (self.__doc__ or "")
        return Multiple()

    def _merge(self, kwargs) -> CompSelf:
        bound_copy = copy.deepcopy(self._bound_args)
        # This will ignore any extra args not in the signature
        # but include any extra kwargs, leaving kwargs empty...
        bound_copy.arguments.update(kwargs)
        extra_kwargs = {
            k: v
            for k, v in kwargs.items()
            if k not in bound_copy.kwargs and k not in self._positional_args
        }
        new_kwargs = {**bound_copy.kwargs, **extra_kwargs}
        new_bound = self._sig.bind(*bound_copy.args, **new_kwargs)
        new_bound.apply_defaults()
        return self.__class__(*new_bound.args, **new_bound.kwargs)


class _ChildrenBase(_ComponentBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._children = []

    def __enter__(self) -> ChildSelf:
        parent_frame_id, parent = last_parent.get()
        self._parent_frame_id = parent_frame_id
        self._parent = parent
        current_frame_id = id(inspect.currentframe().f_back)
        last_parent.set((current_frame_id, self))
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        current_frame_id = id(inspect.currentframe().f_back)
        if self._parent is not None and current_frame_id == self._parent_frame_id:
            self._parent._children.append(self)
        last_parent.set((self._parent_frame_id, self._parent))

    def __iadd__(self, other) -> ChildSelf:
        self._children.append(other)
        return self

    def __class_getitem__(cls, key) -> ChildSelf:
        return cls()[key]

    def __getitem__(self, children) -> safe:
        if self._children:
            # Not AttributeError because it would be confusing, for ex. when using hasattr.
            # Also this is like a function call, so a ValueError makes sense
            raise ValueError(
                "Component already has children, "
                "use the += operator if you want to add more."
            )

        if _is_iterable(children):
            # str is a special case, because it's an iterator too.
            # _ChildrenBase are also iterators because of this very method
            if isinstance(children, (str, safe, _ChildrenBase)):
                children = (children,)
        else:
            children = (children,)

        new = self.copy()
        new._children = children
        return new

    def __str__(self) -> safe:
        if not self._children:
            safe_children = safe("")
        else:
            escaped_children = [self._escape(ch) for ch in self._children]
            safe_children = safe("".join(escaped_children))
        content = self._render(safe_children)
        return self._escape(content)

    @classmethod
    def _escape(cls, item) -> safe:
        if isinstance(item, safe):
            return item
        elif isinstance(item, _ComponentBase):
            return safe(item)
        elif isinstance(item, str):
            return escape(item)
        elif _is_iterable(item):
            escaped = [cls._escape(e) for e in item]
            return safe("".join(escaped))
        else:
            return escape(item)


class _FuncComponent(_ChildrenBase):
    _func: Callable
    _pass_children: bool

    def _render(self, children: safe) -> Union[ContentType, Iterable[ContentType]]:
        kwargs = self._bound_args.kwargs

        if self._pass_children:
            kwargs["children"] = children

        # self.func is unbound
        content = self.__class__._func(*self._bound_args.args, **kwargs)
        return content


class _ClassComponent(_ChildrenBase):
    _pass_children: bool
    _user_class: ComponentClass

    @cached_property
    def _user_instance(self) -> ComponentClass:
        return self._user_class(*self._bound_args.args, **self._bound_args.kwargs)

    def _render(self, children: safe):
        if self._pass_children:
            return self._user_instance.render(children)
        else:
            return self._user_instance.render()


class _HTMLComponentBase(_ComponentBase):
    _html_tag: str
    _attributes = None
    _sig = inspect.signature(lambda **kwargs: None)
    _positional_args = set()

    def __init__(self, **kwargs):
        if self._attributes is not None:
            kwargs.update(self._attributes)
        self._original_kwargs = kwargs

        new_kwargs, self._keyval_args, self._bool_args = self._convert_kwargs(kwargs)
        super().__init__(**new_kwargs)

    def replace(self, **kwargs) -> CompSelf:
        converted, _, _ = self._convert_kwargs(kwargs)
        return super().replace(**converted)

    def append(self, **kwargs) -> CompSelf:
        converted, _, _ = self._convert_kwargs(kwargs)
        return super().append(**converted)

    def merge(self, **kwargs) -> CompSelf:
        converted, _, _ = self._convert_kwargs(kwargs)
        return super().merge(**converted)

    def _convert_kwargs(self, kwargs) -> Tuple[dict, dict, list]:
        new_kwargs = {}
        keyval_args = {}
        bool_args = []

        for key, val in kwargs.items():
            if isinstance(val, str) and '"' in val and "'" in val:
                raise ValueError("Both single and double quotes in attribute value")
            elif keyword.iskeyword(no_underscore := key[:-1]):
                new_kwargs[no_underscore] = val
                keyval_args[no_underscore] = val
            elif isinstance(val, bool):
                if val:
                    bool_args.append(key)
                else:
                    # must not include in the output
                    continue
            else:
                new_kwargs[key] = val
                keyval_args[key] = val

        return new_kwargs, keyval_args, bool_args

    def _get_attributes(self) -> str:
        conv = lambda s: escape(str(s).replace("_", "-"))
        bool_args = " ".join(conv(a) for a in self._bool_args)
        bool_args = " " + bool_args if bool_args else ""
        kv_args = []
        for k, v in self._keyval_args.items():
            if v is None:
                continue
            html_key = conv(k)
            html_val = escape(v)
            if '"' in html_val:
                html_attr = f"{html_key}='{html_val}'"
            else:
                html_attr = f'{html_key}="{html_val}"'
            kv_args.append(html_attr)
        kv_args = " ".join(kv_args)
        kv_args = " " + kv_args if kv_args else ""
        return bool_args + kv_args


class _HTMLComponent(_HTMLComponentBase, _ChildrenBase):
    def _render(self, children: safe) -> safe:
        attributes = self._get_attributes()
        return safe(f"<{self._html_tag}{attributes}>{children}</{self._html_tag}>")


class _SelfClosingHTMLComponent(_HTMLComponentBase):
    def __str__(self) -> safe:
        attributes = self._get_attributes()
        return safe(f"<{self._html_tag}{attributes} />")


def Component(
    func_or_class: Union[ComponentClass, Callable],
) -> Union[Type[_ClassComponent], Type[_FuncComponent]]:
    if inspect.isfunction(func_or_class):
        return _make_func_component(func_or_class)
    elif inspect.isclass(func_or_class):
        return _make_class_component(func_or_class)
    else:
        raise TypeError("Components can only be classes or functions")


def _make_sig(func):
    sig = inspect.signature(func)
    # This is only for caching in the class
    positional_args = {
        name
        for name, param in sig.parameters.items()
        if param.kind in {param.POSITIONAL_ONLY, param.POSITIONAL_OR_KEYWORD}
    }
    return sig, positional_args


def _make_class_component(user_class: ComponentClass) -> Type[_ClassComponent]:
    if not hasattr(user_class, "render"):
        raise TypeError(f"{user_class.__name__} doesn't have a .render() method.")

    orig_sig, positional_args = _make_sig(user_class.__init__)
    withour_passed = [
        param
        for key, param in orig_sig.parameters.items()
        if key not in {"self", "children"}
    ]
    sig = inspect.Signature(parameters=withour_passed)
    render_sig = inspect.signature(user_class.render)
    pass_children = "children" in render_sig.parameters
    return type(
        user_class.__name__,
        (_ClassComponent,),
        dict(
            _user_class=user_class,
            _sig=sig,
            _positional_args=positional_args,
            _pass_children=pass_children,
            __module__=user_class.__module__,
        ),
    )


def _make_func_component(func: Callable) -> Type[_FuncComponent]:
    orig_sig, positional_args = _make_sig(func)
    without_children = [
        param for key, param in orig_sig.parameters.items() if key != "children"
    ]
    sig = inspect.Signature(parameters=without_children)
    pass_children = "children" in orig_sig.parameters
    return type(
        func.__name__,
        (_FuncComponent,),
        dict(
            _func=func,
            _sig=sig,
            _positional_args=positional_args,
            _pass_children=pass_children,
            __module__=func.__module__,
        ),
    )


def _HtmlElem(html_tag: str, parent_class: T) -> T:
    return type(
        html_tag.capitalize(),
        (parent_class,),
        dict(
            _html_tag=html_tag,
            __module__="compone.html",
        ),
    )


def _Elem(html_tag: str) -> Type[_HTMLComponent]:
    """Create Component from HTML element on the fly."""
    return _HtmlElem(html_tag, _HTMLComponent)


def _SelfElem(html_tag: str) -> Type[_SelfClosingHTMLComponent]:
    """Create Component from self-closing HTML element on the fly."""
    return _HtmlElem(html_tag, _SelfClosingHTMLComponent)
