from .component import Elem, _Comp

Html = Elem("html")
Head = Elem("head")
Body = Elem("body")
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


class _ListComp(_Comp):
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
