from typing import Any

from markupsafe import Markup
from markupsafe import escape as markupsafe_escape

__all__ = ["escape", "safe"]

# Alias, because this is more generic than HTML and make sure
# that the API is future proof in case we change implementation
safe = Markup
"""Exclude a string from autoescaping using Markupsafe."""


def escape(s: Any) -> safe:
    """Replace special characters to HTML/XML-safe sequences.
    Marks the resulting string as safe with Markupsafe.
    """
    if isinstance(s, safe):
        return s
    elif s is None:
        return safe()
    # We use the __str__ method instead of __html__
    elif hasattr(s, "__str__"):
        s = s.__str__()

    return markupsafe_escape(s)
