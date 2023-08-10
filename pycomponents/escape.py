from typing import Self


class _SafeStr(str):
    def __add__(self, other: str | Self):
        if isinstance(other, self.__class__):
            return self.__class__(str(self) + other)
        return str(self) + other

    def __repr__(self):
        return f'{self.__class__.__name__}("{str(self)}")'


def escape(s):
    """Replace special characters to HTML-safe sequences.
    Marks the resulting string as safe.
    """

    if isinstance(s, _SafeStr):
        return s
    elif not isinstance(s, str):
        s = str(s)

    s = s.replace("&", "&amp;")  # Must be done first!
    s = s.replace("<", "&lt;")
    s = s.replace(">", "&gt;")
    s = s.replace('"', "&quot;")
    s = s.replace("'", "&#x27;")

    return _SafeStr(s)


def safe(s: str):
    return _SafeStr(s)
