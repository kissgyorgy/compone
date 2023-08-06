from pycomp import Component
from pycomp.html import El, Sel


class Layout(Component):
    def __init__(self, title):
        super().__init__()
        self.title = title

    def render(self, children):
        return f"""
            <html>
                <head>
                    <title>{self.title}</title>
                </head>
                <body>
                    {children}
                </body>
            </html>
        """


class UnordList(Component):
    def __init__(self, elems):
        super().__init__()
        self.elems = elems

    def render(self, children):
        namesli = "\n".join(f"<li>{elem}</li>" for elem in self.elems)
        return f"""
            <ul>
                {namesli}
            </ul>
        """


class P(Component):
    def render(self, children):
        return f"<p>{children}</p>"


class Ul(Component):
    def render(self, children):
        return f"<ul>{children}</ul>"


class Li(Component):
    def render(self, children):
        return f"<li>{children}</li>"


class H(Component):
    def __init__(self, level: int):
        self._level = level

    def render(self, children):
        elem = f"h{self._level}"
        return f"<{elem}>{children}</{elem}>"


class Div(Component):
    def render(self, children):
        return f"""
            <div>
                {children}
            </div>
        """


def main():
    names = ["György", "Dóri1", "Dóri2"]
    title = "Page title"

    return Layout(title=title)[
        P()[title],
        El("div")["HTML component"],
        "<div>html as string</div>",
        Ul()[
            Li()["first elem"],
            Li()["second elem"],
        ],
        Sel("hr"),
        UnordList(names),
        Div()[
            H(1)[title],
            P()["paragraph"],
            "<br>",
            Sel("br"),
        ],
    ]


print(main())
