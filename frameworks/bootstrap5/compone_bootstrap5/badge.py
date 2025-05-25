from compone import Component, html
from compone.html import classes


def _make_badge(variant: str, pill: bool = False, children=None, **attrs):
    class_ = classes("badge", f"text-bg-{variant}")

    if pill:
        class_ = classes(class_, "rounded-pill")

    return html.Span(class_=class_, **attrs)[children]


@Component
def BadgePrimary(*, pill: bool = False, children=None, **attrs):
    return _make_badge("primary", pill, children, **attrs)


@Component
def BadgeSecondary(*, pill: bool = False, children=None, **attrs):
    return _make_badge("secondary", pill, children, **attrs)


@Component
def BadgeSuccess(*, pill: bool = False, children=None, **attrs):
    return _make_badge("success", pill, children, **attrs)


@Component
def BadgeDanger(*, pill: bool = False, children=None, **attrs):
    return _make_badge("danger", pill, children, **attrs)


@Component
def BadgeWarning(*, pill: bool = False, children=None, **attrs):
    return _make_badge("warning", pill, children, **attrs)


@Component
def BadgeInfo(*, pill: bool = False, children=None, **attrs):
    return _make_badge("info", pill, children, **attrs)


@Component
def BadgeLight(*, pill: bool = False, children=None, **attrs):
    return _make_badge("light", pill, children, **attrs)


@Component
def BadgeDark(*, pill: bool = False, children=None, **attrs):
    return _make_badge("dark", pill, children, **attrs)
