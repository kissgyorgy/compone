By doing this tutorial you can learn the full `compone` API very quickly,
because there are only a couple of concepts and methods you need to know about
to effectively use `compone`.

## Hello World

```python
from compone import Component, html

@Component
def Hello(name: str):
    return html.Div[
        html.H1[f"Hello {name}!"],
    ]

content = str(Hello("World"))
print(content)
# <div><h1>Hello World!</h1></div>
```

What's going on here?

- We are defining a new Component with the `@Component` decorator, with one prop: `name`.  
  It converts the function into a Component class under the hood.
- We use the square brackets syntax (`__getitem__`) to specify
  the children of the `Div` element.  
  Same for the `H1` element with our text.
- We "render" the Component into a string then print it.

!!! note "functions are converted to classes"

    It's important to know that functions with the `@Component` decorator
    are dynamically converted to classes, so you are not calling the function
    directly, but creating an instance of your `Component` class and calling
    it's `__str__` method when rendering it.

Why don't we just use a simple function to return strings?
That's a good question! See the next chapters for features that make
`Component`s more powerful than doing that.

## Composability with children

The main feature of compone is the ability to compose `Component`s with other
Components via the children parameter. (The concept is similar to React.js).
This way any component can be nested inside another component. There are 2 ways
you can pass children to a Component:

### Bracket syntax

Here is an example of nesting two of your custom Components:
```python
from compone import Component

@Component
def Parent(children = ""):
    return f"""
        --- Start of Parent ---
        {children}
        --- End of Parent ---
    """

@Component
def Children(children = ""):
    return f"""
        --- Start of Children ---
        {children}
        --- End of Children ---
    """

print(
    Parent[
        Children["Hello World"]
    ]
)
```

This will print:
```

        --- Start of Parent ---

        --- Start of Children ---
        Hello World
        --- End of Children ---

        --- End of Parent ---

```

!!! note "Whitespace"

    Note the whitespace before the lines, which is because of spaces
    and newlines in the multiline strings.

Ther rendering is lazy, all the children will be rendered only at the time
parent is rendered.

You can return a list from a Component, and it's elements will be concatenated:

```python
from compone import Component, html

@Component
def ListParent(children = ""):
    return [
        "--- Start of Parent ---",
        children,
        "--- End of Parent ---",
    ]

@Component
def ListChildren(children = ""):
    return [
        "--- Start of Children ---",
        children,
        "--- End of Children ---"
    ]

print(
    ListParent[
        ListChildren["Hello World"]
    ]
)
```

This doesn't print whitespaces like the previous example, because the list
elements are concatenated directly:

```plaintext
--- Start of Parent ------ Start of Children ---Hello World--- End of Children ------ End of Parent ---
```

### Context manager syntax
When you have more complex Components with a lot more children (like in HTML usually), 
you can use the context manager syntax.

```python
from compone import Component

@Component
def Section(*, title: str, children):
    return html.Div[
        html.H1[title],
        children,
    ]

@Component
def Article(title: str, children):
    return html.Article[
        html.H2[title],
        children,
    ]

with Section(title="Section title") as main:
    with Article(title="Article title") as article: 
        article += html.P["World"]

print(main)
```

Output (no spaces):
```html
<div>
  <h1>Section title</h1>
  <article>
    <h2>Article title</h2>
    <p>World</p>
  </article>
</div>
```

As you can see, you can _mix and match_ the two syntaxes, any way you like.

My suggestion is to use the bracket syntax for simpler, shorter Components,
and the context manager syntax for more complex Components, especially when
you want to have custom code in the middle of a Component.

## HTML Components

All HTML tags are available as Components in the `html` module.
Here is a full HTML page with separate Components for sections:

```python
import datetime as dt
from compone import Component, html

@Component
def Page(title: str, children):
    return html.Html[
        html.Head[
            html.Title[title],
            html.Meta(name="author", content="György Kiss"),
        ],
        html.Body[children],
    ]

@Component
def Header():
    return html.Header[html.H1["Header"],]

@Component
def Content(children):
    return html.Article[children]

@Component
def Footer():
    return html.Footer[
        html.P[
            "Footer",
            html.Br(),
            "Copyright ©",
            dt.datetime.now().year,
        ],
    ]

page = Page(title="My awesome website")[
    Header(),
    Content["Main content"],
    Footer(),
]

print(page)
```

This will print (without indentation):

```html
<html>
  <head>
    <title>My awesome website</title>
    <meta name="author" content="György Kiss" />
  </head>
  <body>
    <header><h1>Header</h1></header>
    <article>Main content</article>
    <footer>
      <p>Footer<br />Copyright ©2024</p>
    </footer>
  </body>
</html>
```

### HTML attributes

Any parameter you pass to an HTML Component will be rendered as HTML attribute,
with underscores converted to dashes:
```python   
print(html.Div(id="my-id", some_attribute="value", data_value="data"))
# <div id="my-id" some-attribute="value" data-value="data"></div>
```

For Python keywords, append an underscore to the attribute name:
```python
print(html.Div(class_="my-class"))
# <div class="my-class"></div>

print(html.Label(for_="my-for"))
# <label for="my-for"></label>
```

Boolean type attributes will be rendered only when `True`:
```python
print(html.Button(disabled=True))
# <button disabled></button>

print(html.Label(disabled=False))
# <button></button>
```

List attribute types will be joined with spaces:
```python
print(html.Div(class_=["class1", "class2"]))
# <div class="class1 class2"></div>
```

### HTML autoescape

Every HTML attribute and children will be automatically escaped by default. You
can opt-out with marking the string with the `safe` class (which uses MarkupSafe
under the hood for now.). Every Component is safe by default.

```python
from compone import html, safe

evil_user_input = "<script>alert('Hello!')</script>"
safe_div = html.Div[evil_user_input]
print(safe_div)
# <div>&lt;script&gt;alert(&#39;Hello!&#39;)&lt;/script&gt;</div>
```

!!! danger

    Be careful when using `safe`, always think about every single case
    whether it will contain user input or not, don't just blindly apply
    it when you encounter an escaped content which should be rendered as html.

    For example, you can't just mark `safe` a dynamically rendered JavaScript
    which contains user input, because it can lead to XSS attacks.


If you pass a list or `*args` as HTML Component children, `str` will be
autoescaped, `safe` objects will be rendered as is:


```python
from compone import html, safe

evil_username = '<script>alert("Hello!")</script>'
look_ma_no_xss = html.Div[
    safe("<script>console.log('Valid script')</script>"),
    evil_username,
]
print(look_ma_no_xss)
# <div><script>console.log('Valid script')</script>&lt;script&gt;alert(&#34;Hello!&#34;)&lt;/script&gt;</div>
```

!!! danger "This still doesn't protect against XSS"

    This is still susceptible to XSS attacks, you have to escape user input
    differently when injecting it to JavaScript context.  
    [See OWASP XSS prevention cheat sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html)
    to defend against different kind of attacks.

### HTML helpers
There are some helpers to make it less cumbersome when working with HTML.

You can manipulate the html `class` attribute easier with the `html.classes` helper.
It is inspired by the `classnames` [JavaScript library](https://www.npmjs.com/package/classnames).

Dynamically applying classes to HTML `class` property:

```python
my_dynamic_classes = html.classes({"red": False, "green": True})
print(html.Div(class_=my_dynamic_classes))
# <div class="green"></div>
```

Concatenating list of classes with strings:

```python
my_classes = html.classes("red", "green", ["blue", "yellow"], "brown black")
print(html.Div(class_=my_classes))
# <div class="red green blue yellow brown black"></div>
```

## Component introspection

If for some reason you need to inspect a Component class, you can use the `.props` property
for all parameters of the instance:

```python
@Component
def MyComponent(a=1, b=2):
    return str(a*b)

my_component = MyComponent()
print(my_component.props)
# {'a': 1, 'b': 2}
```

You can access the children of a Component instance with the `.children` property:
```python
@Component
def MyComponent(a=1, b=2, children=None):
    return html.Div[str(a*b), children]

my_component = MyComponent["My Content", html.P["New paragraph"]]
print(my_component.children)
# ('My Content', <P()>)
```


## Class components
In rare cases when you have a complex logic and want to sticky it to one class,
you can use the `Component` decorator on classes too.
The class only need to have a `.render()` method.

```python
@Component
class MyComponent:
    def __init__(self, a=1, b=2):
        self._a = a
        self._b = b

    def render(self, children):
        return html.Div[str(self._a * self._b), " ", children]

my_component = MyComponent(2, 3)["eggs"]
print(my_component)
# <div>6 eggs</div>
```

!!! note "Works the same as function components"

    This works the same way as function Components, the decorator 
    converts your class to a Component class and calls your `.render()` 
    method when the Component `__str__` method is called.
