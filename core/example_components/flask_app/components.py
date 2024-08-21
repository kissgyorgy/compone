import datetime as dt

from compone import Component, html

count = 0


@Component
def Header():
    return html.Div[
        html.Center["Welcome to my page",],
        html.Hr(),
    ]


@Component
def Footer():
    return html.Div[
        html.Hr(),
        html.Center["Created by Walkman"],
    ]


@Component
def Layout(title: str = "Welcome to my page", *, children: str):
    return html.Html[
        html.Head[html.Title[title],],
        html.Body[
            Header,
            children,
            Footer,
        ],
    ]


@Component
def Created(date: dt.datetime):
    return html.P[
        "Page created at:",
        html.B[date.strftime("%Y-%m-%d %H:%M:%S"),],
    ]


@Component
def Page(title: str, created_at: dt.datetime, children: str):
    created = Created(created_at)
    return Layout(title)[
        html.H1[title],
        html.Article[
            created,
            children,
            created,
        ],
    ]


@Component
def Counter():
    global count
    count += 1
    content = html.P[
        "This page has been viewed",
        html.Strong[count],
        "times",
    ]
    return content
