from typing import Iterable, List, NamedTuple

from lxml import etree


class ComponentTag(NamedTuple):
    tag: str
    attrs: dict
    children: List[str]


class PysxParser:
    def __init__(self, components=[]):
        self._components = {cls.__name__: cls for cls in components}
        self._stack: List[ComponentTag] = []
        self._content = []

    def start(self, tag, attrs):
        print("start:", tag)
        ct = ComponentTag(tag=tag, attrs=attrs, children=[])
        self._stack.append(ct)

    def end(self, tag):
        print("end:", tag)
        ct = self._stack.pop()
        children = "".join(ct.children)

        if ct.tag[0].isupper():
            CompCls = self._components[tag]
            props = dict(ct.attrs)
            if children:
                props["children"] = children
            rendered = CompCls(**props)
            # recursively parse components until there is no component inside
            rendered = parse(rendered, self._components.values())

        else:
            attrs = " ".join(f'{key}="{val}"' for key, val in ct.attrs.items())
            pre = " " if attrs else ""
            if children:
                rendered = f"<{tag}{pre}{attrs}>{children}</{tag}>"
            else:
                rendered = f"<{tag}{pre}{attrs} />"

        try:
            last = self._stack[-1]
        except IndexError:
            self._content.append(rendered)
        else:
            last.children.append(rendered)

    def data(self, data: str):
        try:
            last = self._stack[-1]
        except IndexError:
            self._content.append(data)
        else:
            last.children.append(data)

    def close(self):
        return "".join(self._content)


def parse(content: str, components: Iterable):
    parser = PysxParser(components=components)
    xml_parser = etree.XMLParser(target=parser)
    return etree.XML(content, xml_parser)
