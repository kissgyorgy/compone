import abc
import inspect
from contextvars import ContextVar
from functools import cached_property
from typing import Callable, Iterable, List, Protocol, Tuple, Type, TypeVar, Union

from .escape import escape, safe
from .utils import _is_iterable

last_parent = ContextVar("last_parent", default=None)

T = TypeVar("T")
CompSelf = TypeVar("CompSelf", bound="_ComponentBase")
ChildSelf = TypeVar("ChildSelf", bound="_ChildrenMixin")
StrType = Union[str, safe]
ContentType = Union[StrType, CompSelf]


class ComponentClass(Protocol):
    def render(self, children: safe) -> Union[ContentType, Iterable[ContentType]]:
        ...


class _ComponentBase:
    def __init__(self, **kwargs):
        self._kwargs = kwargs

    def replace(self, **kwargs) -> CompSelf:
        return self._merge(kwargs)

    def append(self, **kwargs) -> CompSelf:
        appended = {}
        for key, val in kwargs.items():
            if key in self._kwargs:
                val = self._kwargs[key] + val
            appended[key] = val
        return self._merge(appended)

    def __repr__(self):
        kwargs = ", ".join(f"{k}={v!r}" for k, v in self._kwargs.items())
        return f"<{self.__class__.__name__}({kwargs})>"

    def __mul__(self, other: int) -> CompSelf:
        if not isinstance(other, int):
            return NotImplemented

        # Every component is safe by default, so the result should be safe too
        Multiple = Component(lambda: safe(self) * other)
        Multiple.__name__ = "Multi" + self.__class__.__name__
        Multiple.__doc__ = "Multiple: " + (self.__doc__ or "")
        return Multiple()

    def _merge(self, kwargs) -> CompSelf:
        merged_kwargs = {**self._kwargs, **kwargs}
        return self.__class__(**merged_kwargs)

    def __call__(self, **kwargs) -> CompSelf:
        if overlapping := [key for key in kwargs if key in self._kwargs]:
            overlapping_keys = ", ".join(overlapping)
            raise KeyError(
                f"{overlapping_keys} already specified in {self!r}, "
                "use the replace method if you want to replace arguments"
            )
        return self._merge(kwargs)


class _ChildrenMixin(metaclass=abc.ABCMeta):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._children = []

    def __enter__(self) -> ChildSelf:
        self._parent = last_parent.get()
        last_parent.set(self)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._parent is not None:
            self._parent._children.append(self)
        last_parent.set(self._parent)

    def __iadd__(self, other) -> ChildSelf:
        self._children.append(other)
        return self

    def __class_getitem__(cls, key) -> ChildSelf:
        return cls()[key]

    def __getitem__(self, children) -> safe:
        if _is_iterable(children):
            # str is a special case, because it's an iterator too
            # _ChildrenMixins are also iterators because of this very method
            if isinstance(children, (str, safe, _ChildrenMixin)):
                children = (children,)
        else:
            children = (children,)

        escaped_children = self._escape(children)
        safe_children = safe("".join(escaped_children))
        return self._render(safe_children)

    def _escape(self, children) -> List[safe]:
        escaped_children = []
        for ch in children:
            is_component = isinstance(ch, _ComponentBase)
            safe_ch = safe(ch) if is_component else escape(ch)
            escaped_children.append(safe_ch)
        return escaped_children

    def __str__(self) -> safe:
        if not self._children:
            return self._render(safe(""))
        escaped_children = self._escape(self._children)
        safe_children = safe("".join(escaped_children))
        return self._render(safe_children)

    @abc.abstractmethod
    def _render(self, children: safe) -> safe:
        ...


class _ContentMixin(metaclass=abc.ABCMeta):
    def _render(self, children: safe) -> safe:
        content = self._get_content(children)

        if isinstance(content, safe):
            return content
        elif isinstance(content, _ComponentBase):
            return safe(content)
        elif isinstance(content, str):
            return escape(content)
        elif _is_iterable(content):
            escaped = self._escape(content)
            return safe("".join(escaped))
        else:
            return escape(content)

    @abc.abstractmethod
    def _get_content(self, children: safe) -> Union[ContentType, Iterable[ContentType]]:
        ...


class _FuncComponent(_ContentMixin, _ChildrenMixin, _ComponentBase):
    _func: Callable
    _pass_children: bool

    def _get_content(self, children: safe) -> Union[ContentType, Iterable[ContentType]]:
        if self._pass_children:
            kwargs = {**self._kwargs, "children": children}
        else:
            # should be okay not to copy
            kwargs = self._kwargs

        # self.func is unbound
        content = self.__class__._func(**kwargs)
        return content


class _ClassComponent(_ContentMixin, _ChildrenMixin, _ComponentBase):
    _pass_children: bool
    _user_class: ComponentClass

    @cached_property
    def _user_instance(self) -> ComponentClass:
        return self._user_class(**self._kwargs)

    def _get_content(self, children: safe):
        if self._pass_children:
            return self._user_instance.render(children)
        else:
            return self._user_instance.render()


class _HTMLComponentBase(_ComponentBase):
    _html_tag: str
    _attributes = None

    def __init__(self, **kwargs):
        if self._attributes is not None:
            kwargs.update(self._attributes)

        new_kwargs, self._keyval_args, self._bool_args = self._convert_kwargs(kwargs)
        super().__init__(**new_kwargs)

    def replace(self, **kwargs) -> CompSelf:
        converted, _, _ = self._convert_kwargs(kwargs)
        return super().replace(**converted)

    def append(self, **kwargs) -> CompSelf:
        converted, _, _ = self._convert_kwargs(kwargs)
        return super().append(**converted)

    def _convert_kwargs(self, kwargs) -> Tuple[dict, dict, list]:
        new_kwargs = {}
        keyval_args = {}
        bool_args = []

        for key, val in kwargs.items():
            if key in {"class_", "for_", "is_"}:
                no_underscore = key[:-1]
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
        kv_args = " ".join(
            f'{conv(k)}="{escape(v)}"' for k, v in self._keyval_args.items()
        )
        kv_args = " " + kv_args if kv_args else ""
        return bool_args + kv_args


class _HTMLComponent(_ChildrenMixin, _HTMLComponentBase):
    def _render(self, children: safe) -> safe:
        attributes = self._get_attributes()
        return safe(f"<{self._html_tag}{attributes}>{children}</{self._html_tag}>")


class _SelfClosingHTMLComponent(_HTMLComponentBase):
    def __str__(self) -> safe:
        attributes = self._get_attributes()
        return safe(f"<{self._html_tag}{attributes} />")


def Component(
    func_or_class: Union[ComponentClass, Callable]
) -> Union[Type[_ClassComponent], Type[_FuncComponent]]:
    if inspect.isfunction(func_or_class):
        return _make_func_component(func_or_class)
    elif inspect.isclass(func_or_class):
        return _make_class_component(func_or_class)
    else:
        raise TypeError("Components can only be classes or functions")


def _make_class_component(user_class: ComponentClass) -> Type[_ClassComponent]:
    if not hasattr(user_class, "render"):
        raise TypeError(f"{user_class.__name__} doesn't have a .render() method.")

    init_argspec = inspect.getfullargspec(user_class.__init__)
    init_argspec.args.remove("self")
    _check_argspec(init_argspec, user_class.__name__)
    render_argspec = inspect.getfullargspec(user_class.render)
    pass_children = "children" in (render_argspec.args + render_argspec.kwonlyargs)
    return type(
        user_class.__name__,
        (_ClassComponent,),
        dict(
            _user_class=user_class,
            _pass_children=pass_children,
            __module__=user_class.__module__,
        ),
    )


def _make_func_component(func: Callable) -> Type[_FuncComponent]:
    argspec = inspect.getfullargspec(func)
    _check_argspec(argspec, func.__name__)
    pass_children = "children" in argspec.kwonlyargs
    return type(
        func.__name__,
        (_FuncComponent,),
        dict(
            _func=func,
            _pass_children=pass_children,
            __module__=func.__module__,
        ),
    )


def _check_argspec(argspec: inspect.FullArgSpec, name: str):
    if argspec.args:
        arglist = ", ".join(argspec.args)
        raise TypeError(
            "Components must only have keyword arguments!\n"
            "           Found positional arguments: "
            f"{arglist} in {name}.__init__"
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
