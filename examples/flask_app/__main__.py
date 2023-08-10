import datetime as dt

from flask import Flask

from pycomp.html import H1, H2, Br, Div, Img

from .components import Counter, Layout, Page

app = Flask(__name__)


@app.route("/")
def hello_world():
    hello = "Hello World"
    return Layout(title=hello)[H1[hello],]


@app.route("/blog/<title>")
def page(title):
    now = dt.datetime.now()
    return Page(title, now)[
        Div[
            H2[title],
            "Here is a cat:" + Br,
            Img(src="https://cataas.com/cat", width=400),
        ],
        Counter,
    ]


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
