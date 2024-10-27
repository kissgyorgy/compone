from compone import Component, html


@Component
def PageLayout(title: str, children: str | None = None):
    return html.Html[
        html.Head[html.Title[title],],
        html.Body[children],
    ]


@Component
def BlogContent(title: str, children: str | None = None):
    return html.Div[
        html.H2[title],
        children,
    ]


@Component
def BlogPage(title: str):
    return PageLayout(title)[
        html.H1[title],
        BlogContent("My blog post title")[
            html.P["first paragraph"],
            html.P["second paragraph"],
        ],
    ]


page = BlogPage("My Blog")
print(page)
