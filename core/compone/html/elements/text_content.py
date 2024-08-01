from ..component import _Elem, _HTMLComponent, _SelfElem

Blockquote = _Elem("blockquote")
Dd = _Elem("dd")
Dl = _Elem("dl")
Dt = _Elem("dt")
Div = _Elem("div")
Figcaption = _Elem("figcaption")
Figure = _Elem("figure")
Hr = _SelfElem("hr")
Menu = _Elem("menu")
P = _Elem("p")
Pre = _Elem("pre")
Li = _Elem("li")


class _ListComp(_HTMLComponent):
    def __getitem__(self, children):
        if isinstance(children, str):
            children = (children,)

        error_message = "List element children must be <li>"
        for child in children:
            ch = str(child).strip()
            assert ch.startswith("<li") and ch.endswith("</li>"), error_message

        return super().__getitem__(children)


class Ul(_ListComp):
    _html_tag = "ul"


class Ol(_ListComp):
    _html_tag = "ol"
