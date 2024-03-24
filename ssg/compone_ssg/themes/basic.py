from compone import Component, html


@Component
def BaseLayout(*, title, children):
    return html.Html[
        html.Head[html.Title[title],],
        html.Body[children,],
    ]


@Component
def IndexPage(*, title, children):
    return BaseLayout(title=title)[children]


@Component
def ContentPage(*, title: str, children):
    return BaseLayout(title=title)[html.Article[children],]


class BasicTheme:
    PAGE_COMPONENT = ContentPage
    INDEX_COMPONENT = IndexPage
