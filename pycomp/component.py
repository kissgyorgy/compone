class Component:
    def __init__(self, func=None):
        self._func = func

    def __getitem__(self, children):
        if isinstance(children, str):
            children = (children,)
        self._children = [str(c) for c in children]
        return str(self)

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
