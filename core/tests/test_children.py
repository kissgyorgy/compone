import pytest
from compone import Component, html


@Component
def WithChildren(*, children):
    return html.Div[children]


def test_component_cannot_overwrite_children_with_getitem():
    comp = WithChildren["Hello"]
    with pytest.raises(ValueError):
        comp["Another Children"]


def test_getitem_doesnt_affect_original_children():
    comp1 = WithChildren()
    comp2 = comp1()
    comp1 += "First Child"
    comp2 += "Another Child"

    assert comp1 is not comp2
    assert str(comp1) == "<div>First Child</div>"
    assert str(comp2) == "<div>Another Child</div>"


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


def test_cannot_make_new_component_with_children():
    with pytest.raises(ValueError):
        WithChildren["Hello"]()
