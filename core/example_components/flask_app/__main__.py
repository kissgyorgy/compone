import datetime as dt

from compone import html
from flask import Flask

from .components import Counter, Layout, Page

app = Flask(__name__)


@app.route("/")
def hello_world():
    hello = "Hello World"
    return Layout(title=hello)[html.H1[hello],]


@app.route("/blog/<title>")
def page(title):
    now = dt.datetime.now()
    return Page(title, now)[
        html.Div[
            html.H2[title],
            "Here is a cat:" + html.Br,
            html.Img(src="https://cataas.com/cat", width=400),
        ],
        Counter,
    ]


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
