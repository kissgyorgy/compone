import abc
from functools import cached_property
from textwrap import dedent
from typing import Tuple


class Component(abc.ABC):
    def __init__(self):
        self._children = []

    def __getitem__(self, children):
        if not isinstance(children, Tuple):
            children = (children,)
        self._children = children
        return self

    @cached_property
    def children(self):
        content = "\n".join(dedent(str(c)) for c in self._children)
        return dedent(content)

    def __str__(self):
        return self.render(self.children)

    @abc.abstractmethod
    def render(self, children):
        ...


class make_component(Component):
    def __init__(self, func=None):
        super().__init__()
        self._func = func

    def __call__(self, *args, **kwargs):
        self._args = args
        self._kwargs = kwargs
        return self

    def render(self, children):
        content = self._func(*self._args, **self._kwargs, children=children)
        return dedent(content)
