from compone import Component, html
from compone.html import classes


def _make_alert(
    variant: str, dismissible: bool = False, children: str | None = None, **attrs
):
    class_ = classes("alert", f"alert-{variant}")

    if dismissible:
        class_ = classes(class_, "alert-dismissible", "fade", "show")
        close_button = html.Button(
            class_="btn-close", data_bs_dismiss="alert", aria_label="Close"
        )
    else:
        close_button = None

    return html.Div(class_=class_, role="alert", **attrs)[children, close_button]


@Component
def AlertPrimary(*, dismissible: bool = False, children=None, **attrs):
    return _make_alert("primary", dismissible, children, **attrs)


@Component
def AlertSecondary(*, dismissible: bool = False, children=None, **attrs):
    return _make_alert("secondary", dismissible, children, **attrs)


@Component
def AlertSuccess(*, dismissible: bool = False, children=None, **attrs):
    return _make_alert("success", dismissible, children, **attrs)


@Component
def AlertDanger(*, dismissible: bool = False, children: str | None = None, **attrs):
    return _make_alert("danger", dismissible, children, **attrs)


@Component
def AlertWarning(*, dismissible: bool = False, children: str | None = None, **attrs):
    return _make_alert("warning", dismissible, children, **attrs)


@Component
def AlertInfo(*, dismissible: bool = False, children: str | None = None, **attrs):
    return _make_alert("info", dismissible, children, **attrs)


@Component
def AlertLight(*, dismissible: bool = False, children: str | None = None, **attrs):
    return _make_alert("light", dismissible, children, **attrs)


@Component
def AlertDark(*, dismissible: bool = False, children: str | None = None, **attrs):
    return _make_alert("dark", dismissible, children, **attrs)
