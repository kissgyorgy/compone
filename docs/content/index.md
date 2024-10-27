# About

**Compone** is a Python **component framework** which makes it possible to
**generate HTML, XML**, RSS and other markup formats using type-safe 
**Python objects** with a very simple API.

`compone.Component`s are **fully-reusable** Python classes in **ANY Python web
framework** or project out-of-the-box without extra code needed.

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

This is a very silly example, but for more examples and features, check out the
[Tutorial](tutorial.md).

## Installation

You can simply install the [`compone` package](https://pypi.org/project/compone/) from PyPI:

```bash
$ pip install compone
```

The only dependency is [markupsafe](https://pypi.org/project/MarkupSafe/) for escaping HTML.

## Motivation

:simple-react: The main reason why I created Compone is when I tried **React.JS**, it felt
really-really **productive** with the component-based architecture. When I
worked with Python web frameworks, I really missed that huge boost in
productivity.

:no_entry: I always disliked **template engines**, mostly because working with them was
**very cumbersome**. When you wanted to create a reusable piece, you had to create
yet-another-template, in yet-another-file in a specific directory, include it
in another template, and so on.

:no_entry: I **never seen** implemented truly **reusable templates**, probably because they
are not very convenient to do that and it's not the main goal of template engines.
It's also hard to create a reusable piece of HTML in a template engine.

:no_entry: Another reason was that it always felt that **presentation was far from my code**,
I always had to juggle between different files, which was very annoying and cumbersome.

:no_entry: Also implicit function calling is a big mistake in template engines, because
it leads to **side-effects**, N+1 query problems and **hard-to-debug** code.

:no_entry: Also different **template engines are not really re-usable between different web**
frameworks. It took years for Django to implement Jinja2 support, and it will still
never be as powerful as Django templates.

:disappointed: The recent trend of new "modern" Python web frameworks (like
ReactPy, Streamlit, Reflex, Ludic and co.) to invent their own component system
is fragmenting the Python web ecosystem, because components written for one are
not reusable for others.

:bulb: In compone land, everything is just regular Python, no magic, no implicit function
calling, you can organize your code as you like and every `compone.Component` works accross 
every Python web framework already.

## :eye: My Vision

My _vision_ for Compone is to build a rich ecosystem of Component Libraries for
popular frameworks based on a very simple API on Compone Core, which can be
**reused in any Python projects**.

The _goal_ is to create simple tools and APIs, which the community can quickly
and easily build custom Component frameworks and libraries for any design system
and share them with the whole Python community, **not just specific frameworks**.

## License

Compone is MIT licensed and all of the projects related to compone are also MIT licensed.
