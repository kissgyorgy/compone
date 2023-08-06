from typing import Optional

from .component import Component, Elem, _HTMLComponent

Html = Elem("html")
Head = Elem("head")
Body = Elem("body")
Article = Elem("article")
Title = Elem("title")
Div = Elem("div")

Br = "<br>"
Hr = "<hr />"

P = Elem("p")
Li = Elem("li")

H1 = Elem("h1")
H2 = Elem("h2")
H3 = Elem("h3")
H4 = Elem("h4")
H5 = Elem("h5")
H6 = Elem("h6")


class Img(Component):
    def __init__(
        self,
        src: str,
        width: Optional[int] = None,
        height: Optional[int] = None,
    ):
        super().__init__()
        self._src = src
        self._width = width
        self._height = height

    def __str__(self):
        width = f"width={self._width}" if self._width else ""
        height = f"height={self._height}" if self._height else ""
        return f'<img src="{self._src}"{width}{height} />'


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
