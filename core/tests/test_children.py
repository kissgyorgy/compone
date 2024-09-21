import pytest
from compone import Component, html


@Component
def WithChildren(*, children):
    return html.Div[children]


def test_component_cannot_overwrite_children_with_getitem():
    comp = WithChildren["Hello"]
    with pytest.raises(ValueError):
        comp["Another Children"]


def test_children_property():
    comp = WithChildren["Hello"]
    assert comp.children == tuple(["Hello"])


def test_children_property_is_not_writable():
    comp = WithChildren["Hello"]
    with pytest.raises(AttributeError):
        comp.children = ("Another Children",)


def test_children_accessible_for_children_components():
    sub = WithChildren["Hello"]
    comp = WithChildren[sub]

    assert comp.children == (sub,)
    assert comp.children[0].children == ("Hello",)
    assert str(comp) == "<div><div>Hello</div></div>"
    assert str(comp.children[0]) == "<div>Hello</div>"


def test_child_components_are_comparable():
    ch1 = WithChildren["Hello"]
    ch2 = WithChildren["Hello"]
    ch3 = WithChildren["World"]

    assert ch1 == ch2
    assert ch2 != ch3

    assert ch1 is not ch2
    assert ch2 is not ch3

    assert ch1.children == ch2.children
    assert ch2.children != ch3.children

    assert ch1.children is not ch2.children
