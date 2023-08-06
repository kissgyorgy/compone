from pycomp import Component
from pycomp import html as h


@Component
def Layout(title: str, children: str):
    return f"""
        <html>
            <head>
                <title>{title}</title>
            </head>
            <body>
                {children}
            </body>
        </html>
    """


@Component
def UnordList(elems: list, children: str):
    li_elems = (h.Li()[elem] for elem in elems)
    return h.Ul()[li_elems]


def main():
    names = ["György", "Dóri1", "Dóri2"]
    title = "Page title"

    return Layout(title=title)[
        h.P()[title],
        "<div>HTML string</div>",
        h.Ul()[
            h.Li()["first elem"],
            h.Li()["second elem"],
        ],
        h.Sel("hr"),
        UnordList(names),
        h.Div()[
            h.H1()[title],
            h.P()["paragraph"],
            "<br>",
            h.Br(),
        ],
        h.Div()[
            h.P()["first paragraph"],
            h.P()["second paragraph"],
        ],
    ]


print(main())
