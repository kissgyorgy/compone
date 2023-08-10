import inspect

from .escape import escape, safe


class _ChildrenMixin:
    def __init__(self):
        self._children = []
        self._args = tuple()
        self._kwargs = {}

    def __class_getitem__(cls, key):
        return cls()[key]

    def __getitem__(self, children):
        try:
            iter(children)
        except TypeError:
            children = (children,)
        else:
            # str is a special case, because it's an iterator too
            if isinstance(children, (str, safe)):
                children = (children,)

        self._children = [escape(ch) for ch in children]
        return safe(self)

    @property
    def children(self):
        # Already escaped in __getitem__
        return safe("\n".join(self._children))

    def __call__(self, *args, **kwargs):
        self._args = args
        self._kwargs = kwargs
        return self


class Component(_ChildrenMixin):
    def __init__(self, func=None):
        super().__init__()
        self._func = func

    def __repr__(self):
        args = ", ".join(repr(a) for a in self._args)
        kwargs = ", ".join(f"{k}={v!r}" for k, v in self._kwargs.items())
        params = f"{args}, {kwargs}" if args and kwargs else args + kwargs
        return f"<{self._func.__name__}({params})>"

    def __str__(self):
        argspec = inspect.getfullargspec(self._func)
        if "children" in argspec.args or "children" in argspec.kwonlyargs:
            content = self._func(*self._args, **self._kwargs, children=self.children)
        else:
            content = self._func(*self._args, **self._kwargs)

        if isinstance(content, safe):
            return content
        elif isinstance(content, str):
            return escape(content)

        try:
            iter(content)
        except TypeError:
            return escape(str(content))
        else:
            return "\n".join(escape(e) for e in content)


class _HTMLComponentBase:
    def __init__(self, *args, **kwargs):
        super().__init__()
        self._name = self.__class__.__name__.lower()
        self._args = args
        self._kwargs = kwargs

    def _attributes(self):
        conv = lambda s: escape(str(s).replace("_", "-"))
        args = [conv(a) for a in self._args]
        kwargs = [safe(f'{conv(k)}="{escape(v)}"') for k, v in self._kwargs.items()]
        params = args + kwargs
        res = " " + " ".join(params) if params else ""
        return res


class _HTMLComponent(_HTMLComponentBase, _ChildrenMixin):
    def __str__(self):
        return safe(f"<{self._name}{self._attributes()}>{self.children}</{self._name}>")


class _SelfClosingHTMLComponent(_HTMLComponentBase):
    def __str__(self):
        return safe(f"<{self._name}{self._attributes()} />")


def Elem(name):
    """Create Component from HTML element on the fly."""
    return type(name, (_HTMLComponent,), {})


def SelfElem(name):
    return type(name, (_SelfClosingHTMLComponent,), {})
