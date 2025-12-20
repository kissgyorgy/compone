from ..html_elements import _HTMLElement, _HTMLElementBase, _VoidHTMLElement

Blockquote = _HTMLElement("blockquote")
Dd = _HTMLElement("dd")
Dl = _HTMLElement("dl")
Dt = _HTMLElement("dt")
Div = _HTMLElement("div")
Figcaption = _HTMLElement("figcaption")
Figure = _HTMLElement("figure")
Hr = _VoidHTMLElement("hr")
Menu = _HTMLElement("menu")
P = _HTMLElement("p")
Pre = _HTMLElement("pre")
Li = _HTMLElement("li")


class _ListComp(_HTMLElementBase):
    def __getitem__(self, children):
        if isinstance(children, str):
            children = (children,)

        error_message = "List element children must be <li>"
        for child in children:
            ch = str(child).strip()
            assert ch.startswith("<li") and ch.endswith("</li>"), error_message

        return super().__getitem__(children)


class Ul(_ListComp):
    _name = "ul"


class Ol(_ListComp):
    _name = "ol"
