from compone import Component, html
from compone_stories import Story


@Component
def TailwindPage(*, children):
    return html.Html[
        html.Meta[html.Script(src="https://cdn.tailwindcss.com"),],
        html.Body[children],
    ]


@Component
def TailwindButton(*, children):
    return html.Button(class_="bg-blue-400 border p-2 text-white rounded")[children]


class TailwindStory(Story):
    template = TailwindPage


@Story.register
class Button(TailwindStory):
    title = "TW Primary Button"
    template = TailwindPage
    # FIXME: AttributeError: component has no attribute __name__
    component = TailwindButton().lazy["Click me"]
