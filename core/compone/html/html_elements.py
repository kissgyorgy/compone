from typing import Type, TypeVar

from ..component import CompSelf
from ..elements import _Element, _make_element, _VoidElement
from .helpers import classes

T = TypeVar("T")


class _HTMLTag:
    def __init__(self, **kwargs):
        self._parse_class(kwargs)
        super().__init__(**kwargs)

    def append(self, **kwargs) -> CompSelf:
        self._parse_class(kwargs)
        return super().append(**kwargs)

    @staticmethod
    def _parse_class(kwargs):
        class_ = kwargs.get("class_", None)
        if parsed := classes(class_):
            kwargs["class_"] = parsed


class _HTMLElementBase(_HTMLTag, _Element):
    pass


class _VoidHTMLElementBase(_HTMLTag, _VoidElement):
    pass


def _HTMLElement(name: str) -> Type[_HTMLElementBase]:
    """Create Component from HTML element on the fly."""
    # TODO: validate element name
    return _make_element(name, _HTMLElementBase)


def _VoidHTMLElement(name: str) -> Type[_VoidHTMLElementBase]:
    """HTML5 void (self-closing) elements.
    In the HTML spec, they don't need the closing slash like in XML tags.
    """
    # TODO: validate element name
    return _make_element(name, _VoidHTMLElementBase)


def CustomHTMLElement(name: str, class_: T) -> T:
    """Custom, user-defined HTML elements like"""
    # TODO: validate element name
    return _make_element(name, class_)
