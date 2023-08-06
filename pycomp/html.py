from textwrap import dedent

from .component import Component


class El(Component):
    """Create Component from HTML tag on the fly."""

    def __init__(self, tag: str):
        super().__init__()
        self._tag = tag

    def render(self, children):
        return dedent(
            f"""
            <{self._tag}>
                {children}
            </{self._tag}>
            """
        )


class Sel(El):
    """Self-closing element"""

    def __str__(self):
        return self.render()

    def render(self):
        return f"<{self._tag} />"
