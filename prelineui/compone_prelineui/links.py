from compone import Component, html


class LinkUnderline:
    DARK = "decoration-gray-800"
    SECONDARY = "decoration-gray-500"
    PRIMARY = "decoration-blue-600"
    SUCCESS = "decoration-teal-500"
    INVALID = "decoration-red-500"
    YELLOW = "decoration-yellow-500"
    LIGHT = "decoration-white"


@Component
def Link(*, class_="", children, **kwargs):
    return html.A(
        class_=f"text-blue-600 hover:text-blue-500 hover:opacity-80 {class_}"
    )[children]


@Component
def UnderlineLink(*, underline_color, class_="", children, **kwargs):
    return html.A(class_=f"underline {underline_color} {class_}", **kwargs)[children]


@Component
def ColoredLink(*, color):
    return html.A()
