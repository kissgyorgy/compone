import abc
import inspect
from typing import Callable

from .escape import escape, safe


class _ComponentBase:
    def __init__(self, **kwargs):
        self._kwargs = kwargs

    def __call__(self, **kwargs):
        merged_kwargs = {**self._kwargs, **kwargs}
        return self.__class__(**merged_kwargs)

    def __repr__(self):
        kwargs = ", ".join(f"{k}={v!r}" for k, v in self._kwargs.items())
        return f"<{self.func.__name__}({kwargs})>"


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
        return self.render(safe_children)

    def _escape(self, children):
        escaped_children = []
        for ch in children:
            is_component = isinstance(ch, _ComponentBase)
            safe_ch = safe(ch) if is_component else escape(ch)
            escaped_children.append(safe_ch)
        return escaped_children

    def __str__(self):
        # not called through __getitem__, so there is no children
        return self.render(None)

    @abc.abstractmethod
    def render(self, children) -> safe:
        ...


class _Component(_ComponentBase, _ChildrenMixin):
    func: Callable
    pass_children: bool

    def render(self, children) -> safe:
        if self.pass_children:
            kwargs = {**self._kwargs, "children": children}
        else:
            # should be okay not to copy
            kwargs = self._kwargs

        # self.func is unbound
        content = self.__class__.func(**kwargs)

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


class _HTMLComponentBase(_ComponentBase):
    html_tag: str
    attributes = None

    def __init__(self, **kwargs):
        if self.attributes is not None:
            kwargs.update(self.attributes)

        for key, val in kwargs.copy().items():
            if key in {"class_", "for_", "is_"}:
                no_underscore = key[:-1]
                kwargs[no_underscore] = val

        super().__init__(**kwargs)

    def _get_attributes(self):
        conv = lambda s: escape(str(s).replace("_", "-"))
        kwargs = " ".join(
            safe(f'{conv(k)}="{escape(v)}"') for k, v in self._kwargs.items()
        )
        kwargs = " " + kwargs if kwargs else ""
        return kwargs


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
    argspec = inspect.getfullargspec(func)
    if argspec.args:
        raise TypeError(
            "Components must only have keyword arguments!\n           "
            f"Found positional arguments: {argspec.args} in {func.__name__}"
        )

    pass_children = "children" in argspec.kwonlyargs
    return type(
        func.__name__, (_Component,), {"func": func, "pass_children": pass_children}
    )


def _Elem(html_tag):
    """Create Component from HTML element on the fly."""
    return type(html_tag.capitalize(), (_HTMLComponent,), {"html_tag": html_tag})


def _SelfElem(html_tag):
    return type(
        html_tag.capitalize(), (_SelfClosingHTMLComponent,), {"html_tag": html_tag}
    )
