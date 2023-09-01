import abc
import inspect
from typing import Callable

from .escape import escape, safe


class _ComponentBase:
    def __init__(self, **kwargs):
        self._kwargs = kwargs

    def replace(self, **kwargs):
        return self._merge(kwargs)

    def append(self, **kwargs):
        appended = {}
        for key, val in kwargs.items():
            if key in self._kwargs:
                val = self._kwargs[key] + val
            appended[key] = val
        return self._merge(appended)

    def __repr__(self):
        kwargs = ", ".join(f"{k}={v!r}" for k, v in self._kwargs.items())
        return f"<{self.__class__.__name__}({kwargs})>"

    def __mul__(self, other):
        if not isinstance(other, int):
            return NotImplemented

        # Every component is safe by default, so the result should be safe too
        Multiple = Component(lambda: safe(self) * other)
        Multiple.__name__ = "Multi" + self.__class__.__name__
        Multiple.__doc__ = "Multiple: " + (self.__doc__ or "")
        return Multiple()

    def _merge(self, kwargs):
        merged_kwargs = {**self._kwargs, **kwargs}
        return self.__class__(**merged_kwargs)

    def __call__(self, **kwargs):
        if overlapping := [key for key in kwargs if key in self._kwargs]:
            overlapping_keys = ", ".join(overlapping)
            raise KeyError(
                f"{overlapping_keys} already specified in {self!r}, "
                "use the replace method if you want to replace arguments"
            )
        return self._merge(kwargs)


class _ChildrenMixin(metaclass=abc.ABCMeta):
    def __class_getitem__(cls, key):
        return cls()[key]

    def __getitem__(self, children):
        try:
            iter(children)
        except TypeError:
            children = (children,)
        else:
            # str is a special case, because it's an iterator too
            # _ChildrenMixins are also iterators because of this very method
            if isinstance(children, (str, safe, _ChildrenMixin)):
                children = (children,)

        escaped_children = self._escape(children)
        safe_children = safe("".join(escaped_children))
        return self._render(safe_children)

    def _escape(self, children):
        escaped_children = []
        for ch in children:
            is_component = isinstance(ch, _ComponentBase)
            safe_ch = safe(ch) if is_component else escape(ch)
            escaped_children.append(safe_ch)
        return escaped_children

    def __str__(self):
        # not called through __getitem__, so there is no children
        return self._render(None)

    @abc.abstractmethod
    def _render(self, children) -> safe:
        ...


class _Component(_ComponentBase, _ChildrenMixin):

        if self.pass_children:
            kwargs = {**self._kwargs, "children": children}
        else:
            # should be okay not to copy
            kwargs = self._kwargs

        # self.func is unbound
        content = self.__class__.func(**kwargs)
        content = self.get_content(children)

        if isinstance(content, safe):
            return content
        elif isinstance(content, _ComponentBase):
            return safe(content)
        elif isinstance(content, str):
            return escape(content)

        try:
            iter(content)
        except TypeError:
            return escape(content)
        else:
            # content is not str here
            return safe("\n".join(self._escape(content)))

    _func: Callable
    _pass_children: bool

class _HTMLComponentBase(_ComponentBase):
    _html_tag: str
    _attributes = None

    def __init__(self, **kwargs):
        if self._attributes is not None:
            kwargs.update(self._attributes)

        new_kwargs, self._keyval_args, self._bool_args = self._convert_kwargs(kwargs)
        super().__init__(**new_kwargs)

    def replace(self, **kwargs):
        converted, _, _ = self._convert_kwargs(kwargs)
        return super().replace(**converted)

    def append(self, **kwargs):
        converted, _, _ = self._convert_kwargs(kwargs)
        return super().append(**converted)

    def _convert_kwargs(self, kwargs):
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

    def _get_attributes(self):
        conv = lambda s: escape(str(s).replace("_", "-"))
        bool_args = " ".join(conv(a) for a in self._bool_args)
        bool_args = " " + bool_args if bool_args else ""
        kv_args = " ".join(
            safe(f'{conv(k)}="{escape(v)}"') for k, v in self._keyval_args.items()
        )
        kv_args = " " + kv_args if kv_args else ""
        return bool_args + kv_args


class _HTMLComponent(_HTMLComponentBase, _ChildrenMixin):
    def _render(self, children):
        if not children:
            children = ""
        attributes = self._get_attributes()
        return safe(f"<{self._html_tag}{attributes}>{children}</{self._html_tag}>")


class _SelfClosingHTMLComponent(_HTMLComponentBase):
    def __str__(self):
        attributes = self._get_attributes()
        return safe(f"<{self._html_tag}{attributes} />")


def Component(func):
    argspec = inspect.getfullargspec(func)
    if argspec.args:
        raise TypeError(
            "Components must only have keyword arguments!\n           "
            f"Found positional arguments: {argspec.args} in {func.__name__}"
        )

    pass_children = "children" in argspec.kwonlyargs
    return type(
        func.__name__,
        (_Component,),
        dict(
            _func=func,
            _pass_children=pass_children,
            __module__=func.__module__,
        ),
    )


def _HtmlElem(html_tag, parent_class):
    return type(
        html_tag.capitalize(),
        (parent_class,),
        dict(
            _html_tag=html_tag,
            __module__="compone.html",
        ),
    )


def _Elem(html_tag):
    """Create Component from HTML element on the fly."""
    return _HtmlElem(html_tag, _HTMLComponent)


def _SelfElem(html_tag):
    """Create Component from self-closing HTML element on the fly."""
    return _HtmlElem(html_tag, _SelfClosingHTMLComponent)
