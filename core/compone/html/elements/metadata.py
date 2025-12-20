from typing import Optional

from ...component import Component
from ...escape import safe
from ..html_elements import _HTMLElement, _VoidHTMLElement

Base = _HTMLElement("base")
Head = _HTMLElement("head")
Link = _VoidHTMLElement("link")
Style = _HTMLElement("style")
Title = _HTMLElement("title")


@Component
def Meta(
    *,
    name: Optional[str] = None,
    http_equiv: Optional[str] = None,
    itemprop: Optional[str] = None,
    content: Optional[str] = None,
):
    kwargs = {}
    if name:
        kwargs["name"] = name
    if http_equiv:
        kwargs["http-equiv"] = http_equiv
    if content:
        kwargs["content"] = content
    if itemprop:
        kwargs["itemprop"] = itemprop

    return _VoidHTMLElement("meta")(**kwargs)


@Component
def MetaCharset():
    # If the attribute is present, its value must be
    # an ASCII case-insensitive match for the string "utf-8",
    # because UTF-8 is the only valid encoding for HTML5 documents.
    # https://developer.mozilla.org/en-US/docs/Web/HTML/Element/meta#charset
    return safe('<meta charset="utf-8">')
