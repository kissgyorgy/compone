import inspect

from .escape import _SafeStr, escape


class _ComponentBase:
    def __init__(self, func=None):
        self._func = func
        self._args = tuple()
        self._kwargs = {}
        self._children = []

    def __call__(self, *args, **kwargs):
        self._args = args
        self._kwargs = kwargs
        return self

    def __repr__(self):
        args = ", ".join(repr(a) for a in self._args)
        kwargs = ", ".join(f"{k}={v!r}" for k, v in self._kwargs.items())
        params = f"{args}, {kwargs}" if args and kwargs else args + kwargs
        return f"<{self._func.__name__}({params})>"


class Component(_ComponentBase):
    def __getitem__(self, children):
        try:
            iter(children)
        except TypeError:
            children = (children,)
        else:
            # str is a special case, because it's an iterator too
            if isinstance(children, (str, _SafeStr)):
                children = (children,)

        self._children = [escape(ch) for ch in children]
        return _SafeStr(self)

    def __class_getitem__(cls, key):
        return cls()[key]

    @property
    def children(self):
        # Already escaped in __getitem__
        return _SafeStr("\n".join(self._children))

    def __str__(self):
        argspec = inspect.getfullargspec(self._func)
        if "children" in argspec.args or "children" in argspec.kwonlyargs:
            content = self._func(*self._args, **self._kwargs, children=self.children)
        else:
            content = self._func(*self._args, **self._kwargs)

        if isinstance(content, _SafeStr):
            return content
        elif isinstance(content, str):
            return escape(content)

        try:
            iter(content)
        except TypeError:
            return escape(str(content))
        else:
            return "\n".join(escape(e) for e in content)


class _HTMLComponentMixin:
    def __init__(self):
        super().__init__()
        self._name = self.__class__.__name__.lower()


class _HTMLComponent(_HTMLComponentMixin, Component):
    def __str__(self):
        return _SafeStr(f"<{self._name}>{self.children}</{self._name}>")


class _SelfClosingHTMLComponent(_HTMLComponentMixin, _ComponentBase):
    def __str__(self):
        return _SafeStr(f"<{self._name} />")


def Elem(name):
    """Create Component from HTML element on the fly."""
    return type(name, (_HTMLComponent,), {})


def SelfElem(name):
    return type(name, (_SelfClosingHTMLComponent,), {})
