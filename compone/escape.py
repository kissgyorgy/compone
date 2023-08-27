from typing import Self


class safe(str):
    """Exclude a string from autoescaping."""

    def __add__(self, other: str | Self):
        if isinstance(other, self.__class__):
            return self.__class__(str(self) + other)
        return str(self) + other

    def __repr__(self):
        return f'{self.__class__.__name__}("{str(self)}")'

    def __mul__(self, other):
        mul_str = super().__mul__(other)
        return self.__class__(mul_str)


def escape(s):
    """Replace special characters to HTML-safe sequences.
    Marks the resulting string as safe.
    """

    if isinstance(s, safe):
        return s
    elif s is None:
        return safe("")
    elif not isinstance(s, str):
        s = str(s)

    s = s.replace("&", "&amp;")  # Must be done first!
    s = s.replace("<", "&lt;")
    s = s.replace(">", "&gt;")
    s = s.replace('"', "&quot;")
    s = s.replace("'", "&#x27;")

    return safe(s)
