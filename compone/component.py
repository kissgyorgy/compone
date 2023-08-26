import inspect
from typing import Callable

from .escape import escape, safe


class _ChildrenMixin:

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
        return self.render(safe_children)

    def _escape(self, children):
        escaped_children = []
        for ch in children:
            is_component = isinstance(ch, (_ChildrenMixin, _HTMLComponentBase))
            safe_ch = safe(ch) if is_component else escape(ch)
            escaped_children.append(safe_ch)
        return escaped_children

    def __str__(self):
        # not called through __getitem__, so there is no children
        return self.render(None)

    def render(self, children) -> safe:
        raise


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

    def render(self, children) -> safe:
        # self.func is unbound
        func = self.__class__.func
        argspec = inspect.getfullargspec(func)
        if "children" in argspec.args or "children" in argspec.kwonlyargs:
            content = func(*self._args, **self._kwargs, children=children)
        else:
            content = func(*self._args, **self._kwargs)

        if isinstance(content, safe):
            return content
        elif isinstance(content, (_ChildrenMixin, _HTMLComponentBase)):
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


class _HTMLComponentBase:
    attributes = None
    html_tag = None

    def __init__(self, *args, **kwargs):
        super().__init__()
        self._args = args
        if self.attributes is not None:
            kwargs.update(self.attributes)
        self._kwargs = self._replace_keyword_attributes(kwargs)

    def _replace_keyword_attributes(self, kwargs):
        for keyword in {"class", "for", "is"}:
            if (underscored := keyword + "_") in kwargs:
                kwargs[keyword] = kwargs.pop(underscored)
        return kwargs

    def _get_attributes(self):
        conv = lambda s: escape(str(s).replace("_", "-"))
        args = " ".join(conv(a) for a in self._args)
        args = " " + args if args else ""
        kwargs = " ".join(
            safe(f'{conv(k)}="{escape(v)}"') for k, v in self._kwargs.items()
        )
        kwargs = " " + kwargs if kwargs else ""
        return args + kwargs


class _HTMLComponent(_HTMLComponentBase, _ChildrenMixin):
    def render(self, children):
        if not children:
            children = ""
        attributes = self._get_attributes()
        return safe(f"<{self.html_tag}{attributes}>{children}</{self.html_tag}>")


class _SelfClosingHTMLComponent(_HTMLComponentBase):
    def __str__(self):
        attributes = self._get_attributes()
        return safe(f"<{self.html_tag}{attributes} />")


def Component(func):
    return type(func.__name__, (_Component,), {"func": func})


def _Elem(html_tag):
    """Create Component from HTML element on the fly."""
    return type(html_tag.capitalize(), (_HTMLComponent,), {"html_tag": html_tag})


def _SelfElem(html_tag):
    return type(
        html_tag.capitalize(), (_SelfClosingHTMLComponent,), {"html_tag": html_tag}
    )
