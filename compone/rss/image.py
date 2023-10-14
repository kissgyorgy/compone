from ..component import _Elem

# <image> sub-element of <channel>
Image = _Elem("image")
# required
Url = _Elem("url")
Title = _Elem("title")
Link = _Elem("link")
# optional
# FIXME: Maximum value for width is 144, default value is 88.
# FIXME: Maximum value for height is 400, default value is 31.
Width = _Elem("width")
Height = _Elem("height")
# Description also can be specified, but already declared above
