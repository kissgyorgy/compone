"""
Examples for Preline UI typography, including global settings,
headings, body text, lists, and more.

https://www.preline.co/docs/typography.html
"""
from compone import Component, html


@Component
def H1(*, class_="", children):
    return html.H1(class_=f"text-4xl dark:text-white {class_}")[children]


@Component
def H2(*, class_="", children):
    return html.H2(class_=f"text-3xl dark:text-white {class_}")[children]


@Component
def H3(*, class_="", children):
    return html.H3(class_=f"text-2xl dark:text-white {class_}")[children]


@Component
def H4(*, class_="", children):
    return html.H4(class_=f"text-xl dark:text-white {class_}")[children]


@Component
def H5(*, class_="", children):
    return html.H5(class_=f"text-lg dark:text-white {class_}")[children]


@Component
def H6(*, class_="", children):
    return html.H6(class_=f"text-base dark:text-white {class_}")[children]
