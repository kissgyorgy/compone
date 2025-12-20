import inspect
import keyword
from typing import Type, TypeVar

from .component import _ChildrenBase, _ComponentBase
from .escape import escape, safe

T = TypeVar("T")


class _Tag(_ComponentBase):
    """Tag is the opening and closing parts of an element.
    e.g. <div> and </div> are tags, "div" is the name of the element.
    """

    _name: str
    _attributes = None
    _sig = inspect.signature(lambda **kwargs: None)
    _var_keyword = "kwargs"
    _positional_args = []

    def __init__(self, **kwargs):
        if self._attributes is not None:
            kwargs.update(self._attributes)
        self._original_kwargs = kwargs
        super().__init__(self.__class__, **kwargs)

    def _get_attributes(self) -> str:  # noqa: C901
        bool_args = []
        keyval_args = []

        for key, val in self.props.items():
            if isinstance(val, str) and '"' in val and "'" in val:
                raise ValueError("Both single and double quotes in attribute value")
            if keyword.iskeyword(no_underscore := key[:-1]):
                key = no_underscore
            # This is not using is_iterable, because there can be iterable
            # objects which behave like strings, but not subclasses of str. For
            # example gettext_lazy and reverse_lazy in Django, which are proxy
            # objects We aim for the most common case here
            if isinstance(val, (tuple, list)):
                val = " ".join(str(i) for i in val)

            key = escape(key.replace("_", "-"))

            if isinstance(val, bool):
                # by HTML standard, False values must not be included in attributes
                if not val:
                    continue
                bool_args.append(key)
            else:
                val = escape(val)
                if '"' in val:
                    attr = f"{key}='{val}'"
                else:
                    attr = f'{key}="{val}"'
                keyval_args.append(attr)

        bool_prefix = " " if bool_args else ""
        bool_arguments = " ".join(bool_args)

        keyval_prefix = " " if keyval_args else ""
        keyval_arguments = " ".join(keyval_args)

        return bool_prefix + bool_arguments + keyval_prefix + keyval_arguments


class _Element(_Tag, _ChildrenBase):
    def _render(self, children: safe) -> safe:
        attributes = self._get_attributes()
        return safe(f"<{self._name}{attributes}>{children}</{self._name}>")


class _VoidElement(_Tag):
    def __str__(self) -> safe:
        attributes = self._get_attributes()
        return safe(f"<{self._name}{attributes} />")

    def __eq__(self, other):
        if not isinstance(other, _VoidElement):
            return NotImplemented
        return (
            # It's a little bit cheaper to compare this way than rendering
            self._name == other._name
            and self._original_kwargs == other._original_kwargs
        )


def _make_element(name: str, parent_class: T) -> T:
    # TODO: validate element name
    return type(
        name.capitalize(),
        (parent_class,),
        dict(
            _name=name,
            __module__=parent_class.__module__,
        ),
    )


def Element(name: str) -> Type[_Element]:
    """Elements are basic building blocks of Components."""
    return _make_element(name, _Element)


def VoidElement(name: str) -> Type[_VoidElement]:
    """Void (self-closing) elements can't have any children."""
    return _make_element(name, _VoidElement)
