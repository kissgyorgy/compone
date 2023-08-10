from typing import Optional

from ..component import Component, Elem, SelfElem

Area = SelfElem("area")
Audio = Elem("audio")
Map = Elem("map")
Track = SelfElem("track")
Video = Elem("video")


class Img(Component):
    def __init__(
        self,
        src: str,
        width: Optional[int] = None,
        height: Optional[int] = None,
    ):
        super().__init__()
        self._src = src
        self._width = width
        self._height = height

    def __str__(self):
        width = f" width={self._width}" if self._width else ""
        height = f" height={self._height}" if self._height else ""
        return f'<img src="{self._src}"{width}{height} />'
