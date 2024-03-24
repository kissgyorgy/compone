from ..component import Component, _Elem, _SelfElem
from ..escape import safe

Base = _Elem("base")
Head = _Elem("head")
Link = _SelfElem("link")
Style = _Elem("style")
Title = _Elem("title")


@Component
def Meta(
    *,
    name: str,
    http_equiv: str | None = None,
    itemprop: str | None = None,
    content: str | None = None,
):
    kwargs = {"name": name}
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
