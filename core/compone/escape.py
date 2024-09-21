import inspect
from typing import Any

from markupsafe import Markup
from markupsafe import escape as markupsafe_escape

__all__ = ["escape", "safe"]


# This is more generic than HTML. Make sure that the API is future proof
# in case we change implementation
class safe(Markup):
    """Exclude a string from autoescaping using Markupsafe."""

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({str.__repr__(self)})"

    def __html__(self) -> str:
        raise AttributeError(
            f"'{self.__class__.__name__}' object has no attribute '__html__'"
        )


def escape(s: Any) -> safe:
    """Replace special characters to HTML/XML-safe sequences.
    Marks the resulting string as safe with Markupsafe.
    """
    if isinstance(s, safe):
        return s
    elif s is None:
        return safe()
    elif inspect.isclass(s):
        raise ValueError("Cannot escape classes. Instantiate the class first!")
    # We use the __str__ method instead of __html__
    elif hasattr(s, "__str__"):
        s = s.__str__()
        if isinstance(s, safe):
            return s

    return safe(markupsafe_escape(s))
