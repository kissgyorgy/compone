import enum
from typing import Literal

from compone import Component, html
from compone.html import classes


class Size(enum.Enum):
    SMALL = "sm"
    LARGE = "lg"


def _make_button(
    variant: str,
    outline: bool = False,
    size: Literal["sm", "lg"] | Size | None = None,
    disabled: bool = False,
    children=None,
    **attrs,
):
    if outline:
        class_ = classes("btn", f"btn-outline-{variant}")
    else:
        class_ = classes("btn", f"btn-{variant}")

    if size:
        size_value = size.value if isinstance(size, Size) else size
        class_ = classes(class_, f"btn-{size_value}")

    return html.Button(class_=class_, disabled=disabled, **attrs)[children]


@Component
def ButtonPrimary(
    *,
    outline: bool = False,
    size: Literal["sm", "lg"] | Size | None = None,
    disabled: bool = False,
    children=None,
    **attrs,
):
    return _make_button("primary", outline, size, disabled, children, **attrs)


@Component
def ButtonSecondary(
    *,
    outline: bool = False,
    size: Literal["sm", "lg"] | Size | None = None,
    disabled: bool = False,
    children=None,
    **attrs,
):
    return _make_button("secondary", outline, size, disabled, children, **attrs)


@Component
def ButtonSuccess(
    *,
    outline: bool = False,
    size: Literal["sm", "lg"] | Size | None = None,
    disabled: bool = False,
    children=None,
    **attrs,
):
    return _make_button("success", outline, size, disabled, children, **attrs)


@Component
def ButtonDanger(
    *,
    outline: bool = False,
    size: Literal["sm", "lg"] | Size | None = None,
    disabled: bool = False,
    children=None,
    **attrs,
):
    return _make_button("danger", outline, size, disabled, children, **attrs)


@Component
def ButtonWarning(
    *,
    outline: bool = False,
    size: Literal["sm", "lg"] | Size | None = None,
    disabled: bool = False,
    children=None,
    **attrs,
):
    return _make_button("warning", outline, size, disabled, children, **attrs)


@Component
def ButtonInfo(
    *,
    outline: bool = False,
    size: Literal["sm", "lg"] | Size | None = None,
    disabled: bool = False,
    children=None,
    **attrs,
):
    return _make_button("info", outline, size, disabled, children, **attrs)


@Component
def ButtonLight(
    *,
    outline: bool = False,
    size: Literal["sm", "lg"] | Size | None = None,
    disabled: bool = False,
    children=None,
    **attrs,
):
    return _make_button("light", outline, size, disabled, children, **attrs)


@Component
def ButtonDark(
    *,
    outline: bool = False,
    size: Literal["sm", "lg"] | Size | None = None,
    disabled: bool = False,
    children=None,
    **attrs,
):
    return _make_button("dark", outline, size, disabled, children, **attrs)


@Component
def ButtonLink(
    *,
    size: Literal["sm", "lg"] | Size | None = None,
    disabled: bool = False,
    children=None,
    **attrs,
):
    return _make_button("link", False, size, disabled, children, **attrs)


@Component
def CloseButton(*, dark: bool = False, disabled: bool = False, **attrs):
    return html.ButtonButton(
        class_="btn-close",
        disabled=disabled,
        aria_label="Close",
        data_bs_theme="dark" if dark else None,
        **attrs,
    )
