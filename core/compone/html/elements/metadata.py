from typing import Optional

from ...component import Component
from ...escape import safe
from ..component import _Elem, _SelfElem

Base = _Elem("base")
Head = _Elem("head")
Link = _SelfElem("link")
Style = _Elem("style")
Title = _Elem("title")


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

    return _SelfElem("meta")(**kwargs)


@Component
def MetaCharset():
    # If the attribute is present, its value must be
    # an ASCII case-insensitive match for the string "utf-8",
    # because UTF-8 is the only valid encoding for HTML5 documents.
    # https://developer.mozilla.org/en-US/docs/Web/HTML/Element/meta#charset
    return safe('<meta charset="utf-8">')
