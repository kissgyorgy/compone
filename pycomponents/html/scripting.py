from ..component import _Elem, _HTMLComponent
from ..escape import safe

Canvas = _Elem("canvas")
Noscript = _Elem("noscript")
Script = _Elem("script")


class ScriptTemplate(_HTMLComponent):
    html_tag = "script"

    def __init__(self, **kwargs):
        self._args = []
        self._kwargs = {}
        self._template_kwargs = kwargs

    def __getitem__(self, children):
        parts = self._convert_tuple(children)
        safe_template = "".join(self._escape(parts))
        self._rendered = safe(safe_template % self._template_kwargs)
        return safe(self)

    def __str__(self):
        return safe(f"<{self.html_tag}>{self._rendered}</{self.html_tag}>")
