from ..component import Elem, _HTMLComponent
from ..escape import safe

Blockquote = Elem("blockquote")
Dd = Elem("dd")
Dl = Elem("dl")
Dt = Elem("dt")
Div = Elem("div")
Figcaption = Elem("figcaption")
Figure = Elem("figure")
Hr = safe("<hr>")
Menu = Elem("menu")
P = Elem("p")
Pre = Elem("pre")
Li = Elem("li")


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
