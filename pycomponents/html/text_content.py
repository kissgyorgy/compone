from ..component import _Elem, _HTMLComponent
from ..escape import safe

Blockquote = _Elem("blockquote")
Dd = _Elem("dd")
Dl = _Elem("dl")
Dt = _Elem("dt")
Div = _Elem("div")
Figcaption = _Elem("figcaption")
Figure = _Elem("figure")
Hr = safe("<hr>")
Menu = _Elem("menu")
P = _Elem("p")
Pre = _Elem("pre")
Li = _Elem("li")


class _ListComp(_HTMLComponent):
    def __getitem__(self, children):
        if isinstance(children, str):
            children = (children,)

        for child in children:
            ch = child.strip()
            error_message = "List element children must be <li>"
            assert ch.startswith("<li") and ch.endswith("</li>"), error_message
            self._children.append(child)
        return str(self)


class Ul(_ListComp):
    """Unordered List"""


class Ol(_ListComp):
    """Ordered List"""
