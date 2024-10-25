# Compone for Python

**Compone** is a Python **component framework** which makes it possible to
**generate HTML, XML, RSS** (even robots.txt or PDF later) and other markup
formats using type-safe **Python objects** with a very simple API.

`compone.Component`s are **fully-reusable** Python classes in 
**ANY Python web framework** or project out-of-the-box without extra code needed.

It's a modern **alternative to template engines** like Jinja2 or Django
templates for generating strings.

## Hello World

```python
from compone import Component, html

@Component
def Hello(name: str, children):
    return html.Div[
        html.H1[f"Hello {name}!"],
        children,
    ]

print(Hello("World")["My Child"])
# <div><h1>Hello World!</h1>My Child</div>
```

This is a silly example, but for more examples and features, check out the
[Tutorial](https://python-compone.kissgyorgy.me/tutorial/) in the Documentation.

## Installation

You can simply install the [`compone` package](https://pypi.org/project/compone/) from PyPI:

```bash
$ pip install compone
```

The only dependency is [markupsafe](https://pypi.org/project/MarkupSafe/) for escaping HTML.

## Documentation

The documentation is available at
[https://python-compone.kissgyorgy.me](https://python-compone.kissgyorgy.me/).
