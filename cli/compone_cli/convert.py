import textwrap

import click
from compone import html
from compone.escape import safe
from lxml import etree


@click.group()
def convert():
    """Convert HTML to Component classes."""


@convert.command(name="html")
@click.argument("file", type=click.File())
@click.argument("component_name")
def convert_html(file, component_name: str):
    from lxml import etree

    root = etree.XML(file.read())

    args = {"class_": "margin-right"}
    kwargs = ", ".join([f'{k}="{v}"' for k, v in args.items()])

    funcdef = textwrap.dedent(
        f"""\
        from compone import html, safe, Component
        @Component
        def {component_name}(*, {kwargs}):
            return """
    )
    res = parse_element_tree(root, parent=None)
    print(funcdef, end="")
    print(textwrap.indent(make_source(res), "    "))


def parse_element_tree(element, parent):
    if not element.nsmap:
        tagname = element.tag
    else:
        tagname = etree.QName(element).localname

    if tagname == "svg":
        obj = safe(etree.tostring(element).decode())
        return obj

    cls_name = tagname.capitalize()
    attribs = {}
    for k, v in element.attrib.items():
        if k in {"class", "for", "is", "async"}:
            k = f"{k}_"
        k = k.replace("-", "_")
        attribs[k] = v

    obj = getattr(html, cls_name)(**attribs)

    if parent is None:
        parent = obj

    if stripped := element.text.strip():
        obj += stripped

    for child in element:
        new_child = parse_element_tree(child, parent=parent)
        obj += new_child

    return obj


def make_source(obj, root=True):
    pieces = []
    if isinstance(obj, safe):
        return '"""' + str(obj) + '"""' + ",\n"
    elif isinstance(obj, str):
        return repr(obj) + ",\n"

    kwargs_str = ", ".join(f"{k}={v!r}" for k, v in obj._original_kwargs.items())
    pieces.append(f"html.{obj.__class__.__name__}({kwargs_str})")

    if obj._children:
        pieces.append("[")
        for child in obj._children:
            pieces.append(make_source(child, root=False))
    pieces.append("]")
    if not root:
        pieces.append(",\n")
    return "".join(pieces)
