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
        return f"<{self.__class__.__name__}({kwargs})>"

    def __mul__(self, other):
        if not isinstance(other, int):
            return NotImplemented

        # Every component is safe by default, so the result should be safe too
        Multiple = Component(lambda: safe(self) * other)
        Multiple.__name__ = "Multi" + self.__class__.__name__
        Multiple.__doc__ = "Multiple: " + (self.__doc__ or "")
        return Multiple()


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

        self._keyval_args = {}
        self._bool_args = []

        for key, val in kwargs.copy().items():
            if key in {"class_", "for_", "is_"}:
                no_underscore = key[:-1]
                kwargs[no_underscore] = val
                self._keyval_args[no_underscore] = val
            elif isinstance(val, bool):
                if val:
                    self._bool_args.append(key)
                else:
                    # must not include in the output
                    continue
            else:
                self._keyval_args[key] = val

        super().__init__(**kwargs)

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
    def render(self, children):
        if not children:
            children = ""
        attributes = self._get_attributes()
        return safe(f"<{self.html_tag}{attributes}>{children}</{self.html_tag}>")


class _SelfClosingHTMLComponent(_HTMLComponentBase):
    def __str__(self):
        attributes = self._get_attributes()
        return safe(f"<{self.html_tag}{attributes} />")


class _SimpleHTMLComponent(_HTMLComponentBase):
    def __str__(self):
        attributes = self._get_attributes()
        return safe(f"<{self.html_tag}{attributes}>")


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
        dict(func=func, pass_children=pass_children, __module__=func.__module__),
    )


def _HtmlElem(html_tag, parent_class):
    return type(
        html_tag.capitalize(),
        (parent_class,),
        dict(html_tag=html_tag, __module__="compone.html"),
    )


def _Elem(html_tag):
    """Create Component from HTML element on the fly."""
    return _HtmlElem(html_tag, _HTMLComponent)


def _SelfElem(html_tag):
    """Create Component from self-closing HTML element on the fly."""
    return _HtmlElem(html_tag, _SelfClosingHTMLComponent)
