from functools import cached_property
from textwrap import dedent
from typing import Tuple


class Component:
    def __init__(self, func=None):
        self._func = func

    def __getitem__(self, children):
        if not isinstance(children, Tuple):
            children = (children,)
        self._children = children
        return self

    @cached_property
    def children(self):
        content = "\n".join(dedent(str(c)) for c in self._children)
        return dedent(content)

    def __call__(self, *args, **kwargs):
        self._args = args
        self._kwargs = kwargs
        return self

    def __str__(self):
        content = self._func(*self._args, **self._kwargs, children=self.children)
        return dedent(content)
