from typing import List, NamedTuple

from .html_parser import CaseSensitiveHTMLParser


class ComponentTag(NamedTuple):
    tag: str
    attrs: dict
    children: List[str]


class PysxParser(CaseSensitiveHTMLParser):
    def __init__(self, *args, components=[], **kwargs):
        super().__init__(*args, **kwargs)
        self._components = {cls.__name__: cls for cls in components}
        self._stack: List[ComponentTag] = []
        self._content = []

    def handle_starttag(self, tag, attrs):
        ct = ComponentTag(tag=tag, attrs=attrs, children=[])
        self._stack.append(ct)

    def handle_endtag(self, tag):
        ct = self._stack.pop()
        children = "".join(ct.children)

        if ct.tag[0].isupper():
            CompCls = self._components[tag]
            rendered = CompCls(**dict(ct.attrs), children=children)
        else:
            rendered = f"{self.get_starttag_text()}{children}</{tag}>"

        try:
            last = self._stack[-1]
        except IndexError:
            self._content.append(rendered)
        else:
            last.children.append(rendered)

    def handle_data(self, data: str):
        try:
            last = self._stack[-1]
        except IndexError:
            self._content.append(data)
        else:
            last.children.append(data)

    @property
    def content(self):
        return "".join(self._content)
