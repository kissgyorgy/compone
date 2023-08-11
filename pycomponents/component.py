import functools
import inspect
from typing import Callable

from .escape import escape, safe


class _ChildrenMixin:
    def __init__(self):
        self._children = []

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

        self._children = [escape(ch) for ch in children]
        return safe(self)

    @property
    def children(self):
        # Already escaped in __getitem__
        return safe("\n".join(self._children))


class _Component(_ChildrenMixin):
    func: Callable

    def __init__(self, *args, **kwargs):
        super().__init__()
        self._args = args
        self._kwargs = kwargs

    def __repr__(self):
        args = ", ".join(repr(a) for a in self._args)
        kwargs = ", ".join(f"{k}={v!r}" for k, v in self._kwargs.items())
        params = f"{args}, {kwargs}" if args and kwargs else args + kwargs
        return f"<{self.func.__name__}({params})>"

    def __str__(self):
        # self.func is unbound
        func = self.__class__.func
        argspec = inspect.getfullargspec(func)
        if "children" in argspec.args or "children" in argspec.kwonlyargs:
            content = func(*self._args, **self._kwargs, children=self.children)
        else:
            content = func(*self._args, **self._kwargs)

        if isinstance(content, safe):
            return content
        elif isinstance(content, str):
            return escape(content)

        try:
            iter(content)
        except TypeError:
            return escape(content)
        else:
            return safe("\n".join(escape(e) for e in content))


class _HTMLComponentBase:
    attributes = None
    html_tag = None

    def __init__(self, *args, **kwargs):
        super().__init__()
        self._args = args
        if self.attributes is not None:
            kwargs.update(self.attributes)
        self._kwargs = kwargs

    def _get_attributes(self):
        conv = lambda s: escape(str(s).replace("_", "-"))
        args = [conv(a) for a in self._args]
        kwargs = [safe(f'{conv(k)}="{escape(v)}"') for k, v in self._kwargs.items()]
        params = " ".join(args) + " ".join(kwargs)
        return " " + params if params else ""


class _HTMLComponent(_HTMLComponentBase, _ChildrenMixin):
    def __str__(self):
        return safe(
            f"<{self.html_tag}{self._get_attributes()}>{self.children}</{self.html_tag}>"
        )


class _SelfClosingHTMLComponent(_HTMLComponentBase):
    def __str__(self):
        return safe(f"<{self.html_tag}{self._get_attributes()} />")


def Component(func):
    return type(func.__name__, (_Component,), {"func": func})


def _Elem(html_tag):
    """Create Component from HTML element on the fly."""
    return type(html_tag.capitalize(), (_HTMLComponent,), {"html_tag": html_tag})


def _SelfElem(html_tag):
    return type(
        html_tag.capitalize(), (_SelfClosingHTMLComponent,), {"html_tag": html_tag}
    )
