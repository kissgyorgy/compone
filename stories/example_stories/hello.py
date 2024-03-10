from compone import Component, html
from compone_stories import Story


@Component
def HelloWorld(*, name: str = "world"):
    return html.Div[
        html.H1["Hello, world!"],
        html.P["This is an example story."],
    ]


@Component
def HelloName(*, name: str = "Python community"):
    return html.Div[
        html.H1[f"Hello, {name}"],
        html.P["This is an parametrized story."],
    ]


@Component
def PrimaryButton(*, children):
    return html.Button()[children]


class HelloWorldStory(Story):
    component = HelloWorld


class HelloNameStory(Story):
    component = HelloName


class ButtonStory(Story):
    title = "Primary button"
    component = PrimaryButton().lazy["Click me"]


Story.register(HelloWorldStory, HelloNameStory, ButtonStory)
