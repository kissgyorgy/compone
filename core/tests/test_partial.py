import pytest
from compone import Component, html, safe


@Component
def MyComponent(a, b):
    return html.Div(a=a, b=b)


def test_partial_repr():
    PartialComp = MyComponent.partial(a=1, b=2)
    assert repr(PartialComp) == "<MyComponent.partial(a=1, b=2)>"


def test_partial_raises_TypeError_on_rendering():
    with pytest.raises(TypeError, match=r"Partial Component cannot be rendered."):
        str(MyComponent.partial(a=1))


def test_calling_partial_makes_original_component():
    PartialComp = MyComponent.partial(a=1)
    comp = PartialComp(b=2)
    assert str(comp) == """<div a="1" b="2"></div>"""
    assert isinstance(comp, MyComponent)


def test_partial_props_can_be_replaced():
    PartialComp = MyComponent.partial(a=1)
    comp = PartialComp.replace(a=3)(b=2)
    assert str(comp) == """<div a="3" b="2"></div>"""


def test_partial_has_props():
    PartialComp = MyComponent.partial(a=1)
    assert PartialComp.props == {"a": 1}


def test_is_partial_property():
    PartialComp = MyComponent.partial(a=1)
    assert PartialComp.is_partial is True
    assert PartialComp(b=2).is_partial is False
