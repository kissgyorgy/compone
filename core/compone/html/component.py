import inspect
import keyword
from typing import TypeVar

from ..component import CompSelf, _ChildrenBase, _ComponentBase
from ..escape import escape, safe
from ..utils import is_iterable

T = TypeVar("T")


class _HTMLComponentBase(_ComponentBase):
    _html_tag: str
    _attributes = None
    _sig = inspect.signature(lambda **kwargs: None)
    _var_keyword = "kwargs"
    _positional_args = []

    def __init__(self, **kwargs):
        if self._attributes is not None:
            kwargs.update(self._attributes)
        self._original_kwargs = kwargs
        self._convert_class(kwargs)
        super().__init__(**kwargs)

    @classmethod
    def _convert_class(cls, kwargs) -> list:
        class_ = kwargs.get("class_", None)
        if not class_:
            return
        elif isinstance(class_, str):
            if not class_.strip():
                return
            classes = class_.split()
        elif is_iterable(class_):
            classes = [spc for cls in class_ if cls for spc in cls.split() if spc]

        kwargs["class_"] = [stripped for c in classes if c and (stripped := c.strip())]

    def append(self, **kwargs) -> CompSelf:
        self._convert_class(kwargs)
        return super().append(**kwargs)

    def _get_attributes(self) -> str:  # noqa: C901
        bool_args = []
        keyval_args = []

        for key, val in self.props.items():
            if isinstance(val, str) and '"' in val and "'" in val:
                raise ValueError("Both single and double quotes in attribute value")
            if keyword.iskeyword(no_underscore := key[:-1]):
                key = no_underscore
            if isinstance(val, (list, tuple)):
                val = " ".join(str(i) for i in val)

            html_key = escape(key.replace("_", "-"))

            if isinstance(val, bool):
                # by HTML standard, False values must not be included in attributes
                if not val:
                    continue
                bool_args.append(html_key)
            else:
                html_val = escape(val)
                if '"' in html_val:
                    html_attr = f"{html_key}='{html_val}'"
                else:
                    html_attr = f'{html_key}="{html_val}"'
                keyval_args.append(html_attr)

        bool_prefix = " " if bool_args else ""
        bool_arguments = " ".join(bool_args)

        keyval_prefix = " " if keyval_args else ""
        keyval_arguments = " ".join(keyval_args)

        return bool_prefix + bool_arguments + keyval_prefix + keyval_arguments


class _HTMLComponent(_HTMLComponentBase, _ChildrenBase):
    def _render(self, children: safe) -> safe:
        attributes = self._get_attributes()
        return safe(f"<{self._html_tag}{attributes}>{children}</{self._html_tag}>")


class _SelfClosingHTMLComponent(_HTMLComponentBase):
    def __str__(self) -> safe:
        attributes = self._get_attributes()
        return safe(f"<{self._html_tag}{attributes} />")

    def __eq__(self, other):
        if not isinstance(other, _SelfClosingHTMLComponent):
            return NotImplemented
        return (
            # It's a little bit cheaper to compare this way than rendering
            self._html_tag == other._html_tag
            and self._original_kwargs == other._original_kwargs
        )


def _HtmlElem(html_tag: str, parent_class: T) -> T:
    return type(
        html_tag.capitalize(),
        (parent_class,),
        dict(
            _html_tag=html_tag,
            __module__="compone.html",
        ),
    )


def _Elem(html_tag: str) -> type[_HTMLComponent]:
    """Create Component from HTML element on the fly."""
    return _HtmlElem(html_tag, _HTMLComponent)


def _SelfElem(html_tag: str) -> type[_SelfClosingHTMLComponent]:
    """Create Component from self-closing HTML element on the fly."""
    return _HtmlElem(html_tag, _SelfClosingHTMLComponent)
