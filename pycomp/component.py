class Component:
    def __init__(self, func=None):
        self._func = func
        self._args = tuple()
        self._kwargs = {}
        self._children = []

    def __getitem__(self, children):
        try:
            iter(children)
        except TypeError:
            children = (children,)
        else:
            # str is a special case, because it's an iterator too
            if isinstance(children, str):
                children = (children,)

        self._children = [str(c) for c in children]
        return str(self)

    def __class_getitem__(cls, key):
        return cls()[key]

    @property
    def children(self):
        return "\n".join(self._children)

    def __call__(self, *args, **kwargs):
        self._args = args
        self._kwargs = kwargs
        return self

    def __repr__(self):
        args = ", ".join(repr(a) for a in self._args)
        kwargs = ", ".join(f"{k}={v!r}" for k, v in self._kwargs.items())
        params = f"{args}, {kwargs}" if args and kwargs else args + kwargs
        return f"<{self._func.__name__}({params})>"

    def __str__(self):
        return self._func(*self._args, **self._kwargs, children=self.children)


class _HTMLComponent(Component):
    def __init__(self):
        super().__init__()
        self._name = self.__class__.__name__.lower()

    def __str__(self):
        return f"<{self._name}>{self.children}</{self._name}>"


def Elem(name):
    """Create Component from HTML element on the fly."""
    return type(name, (_HTMLComponent,), {})
