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
    comp1 = WithChildren["Children"]
    comp2 = comp1()
    comp2 += "Another Children"

    assert comp1 is not comp2
    assert str(comp1) == """<div>Children</div>"""
    assert str(comp2) == """<div>Another Children</div>"""
