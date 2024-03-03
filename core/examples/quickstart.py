from compone import Component, html


@Component
def Layout(title: str, children: str):
    return html.Html[
        html.Head[html.Title[title],],
        html.Body[children],
    ]


@Component
def UnordList(elems: list, children: str):
    li_elems = (html.Li[elem] for elem in elems)
    return html.Ul[li_elems]


def main():
    names = ["György", "Dóri1", "Dóri2"]
    title = "Page title"

    return Layout(title=title)[
        html.P[title],
        "<div>HTML string</div>",
        html.Ul[
            html.Li["first elem"],
            html.Li["second elem"],
        ],
        html.Hr,
        UnordList(names),
        html.Div[
            html.H1[title],
            html.H2["title2"],
            html.H3["title3"],
            html.H4["title4"],
            html.H5["title5"],
            html.P["paragraph"],
            # these two are the same
            "<br>",
            html.Br,
        ],
        html.Div[
            html.P["first paragraph"],
            html.P["second paragraph"],
        ],
    ]


print(main())
