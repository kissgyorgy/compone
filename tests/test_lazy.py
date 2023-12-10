import pytest

from compone import Component, html, safe


def test_lazy_without_children():
    @Component
    def NoChildren():
        return html.Div()

    assert str(NoChildren().lazy) == "<div></div>"
    assert str(NoChildren().lazy()) == "<div></div>"


def test_lazy_with_fixed_children():
    @Component
    def WithChildren():
        return html.Div["Hello"]

    expected = safe("<div>Hello</div>")
    assert str(WithChildren().lazy) == expected
    assert str(WithChildren().lazy()) == expected


def test_lazy_with_dynamic_children():
    @Component
    def WithChildren(*, children):
        return html.Div[children]

    expected = safe("<div>Hello</div>")
    assert str(WithChildren().lazy["Hello"]) == expected
    assert str(WithChildren().lazy()["Hello"]) == expected


def test_lazy_is_idempotent():
    @Component
    def WithChildren(*, children):
        return html.Div[children]

    expected = safe("<div>Hello</div>")
    assert str(WithChildren().lazy.lazy["Hello"]) == expected
    assert str(WithChildren().lazy.lazy()["Hello"]) == expected
    assert str(WithChildren().lazy().lazy["Hello"]) == expected
    assert str(WithChildren().lazy().lazy()["Hello"]) == expected


def test_lazy_component_cannot_overwrite_children():
    @Component
    def WithChildren(*, children):
        return html.Div[children]

    lazy_comp = WithChildren().lazy["Hello"]
    with pytest.raises(ValueError):
        lazy_comp["Another_children"]


def test_html_components_are_lazy():
    expected = safe("<div>Hello</div>")
    assert str(html.Div().lazy["Hello"]) == expected
    assert str(html.Div().lazy()["Hello"]) == expected
