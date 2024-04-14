"""
Examples for opting images into all kinds of behaviors.

https://www.preline.co/docs/images.html
"""
from compone import Component, html


@Component
def ZoomImage(*, class_="", box_class="", **kwargs):
    return html.Div(
        class_=f"group flex-shrink-0 relative rounded-xl overflow-hidden {box_class}"
    )[
        html.Img(
            class_=f"transition-transform duration-500 ease-in-out size-full absolute top-0 start-0 object-cover rounded-xl {class_}",
            **kwargs,
        )
    ]


@Component
def OverlayImage():
    pass
