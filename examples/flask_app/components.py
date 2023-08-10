import datetime as dt

from pycomp import Component
from pycomp import html as h

count = 0


@Component
def Header():
    return h.Div[
        h.Center["Welcome to my page",],
        h.Hr,
    ]


@Component
def Footer():
    return h.Div[
        h.Hr,
        h.Center["Created by Walkman"],
    ]


@Component
def Layout(title: str = "Welcome to my page", *, children: str):
    return h.Html[
        h.Head[h.Title[title],],
        h.Body[
            Header,
            children,
            Footer,
        ],
    ]


@Component
def Created(date: dt.datetime, children: str):
    return h.P[
        "Page created at:",
        h.B[date.strftime("%Y-%m-%d %H:%M:%S")],
    ]


@Component
def Page(title: str, created_at: dt.datetime, children: str):
    created = Created(created_at)
    return Layout(title)[
        h.H1[title],
        h.Article[
            created,
            children,
            created,
        ],
    ]


@Component
def Counter(children: str):
    global count
    count += 1
    content = h.P["This page has been viewed", h.Strong[count], "times"]
    return content
