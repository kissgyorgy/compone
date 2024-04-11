import pickle
import re

import pytest
from compone import Component, html


@Component
def MyComponent(a, b):
    return html.Div(a=a, b=b)


def test_partial_repr():
    PartialComp = MyComponent.partial(a=1, b=2)
    assert repr(PartialComp) == "<MyComponent.partial(a=1, b=2)>"


def test_calling_partial_calls_replace():
    PartialComp = MyComponent.partial(a=1)
    comp = PartialComp(a=3, b=2)
    assert str(comp) == """<div a="3" b="2"></div>"""


def test_partial_raises_TypeError_on_rendering():
    with pytest.raises(
        TypeError,
        match=re.escape(
            r"Partial Component <MyComponent.partial(a=1)> cannot be rendered."
        ),
    ):
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


def test_replace_partial_new_instance():
    PartialComp = MyComponent.partial(a=1)
    comp1 = PartialComp(b=2)
    Partial2 = PartialComp.replace(a=2)
    comp2 = Partial2.replace(b=3)()
    assert comp1 is not comp2
    assert str(comp1) == """<div a="1" b="2"></div>"""
    assert str(comp2) == """<div a="2" b="3"></div>"""


def test_unpickable_object():
    make_it_closure = True

    class Unpickable:
        def __init__(self):
            self._a = make_it_closure

        def __str__(self):
            return "Unpickable"

    with pytest.raises(AttributeError):
        pickle.dumps(Unpickable())

    PartialComp = MyComponent.partial(a=Unpickable())
    comp = PartialComp(b=2)
    assert str(comp) == """<div a="Unpickable" b="2"></div>"""


def test_can_be_called_with_args():
    PartialComp = MyComponent.partial(1, 2)
    comp = PartialComp(3, 4)
    assert str(comp) == """<div a="3" b="4"></div>"""


def test_partial_with_no_args():
    PartialComp = MyComponent.partial()
    comp = PartialComp(3, 4)
    assert str(comp) == """<div a="3" b="4"></div>"""


def test_passing_same_argument_multiple_time_raises_TypeError():
    PartialComp = MyComponent.partial(a=1, b=2)
    with pytest.raises(
        TypeError,
        match=re.escape(
            "Partial Component <MyComponent.partial(a=1, b=2)> got multiple values for 'a'"
        ),
    ):
        PartialComp(3, a=4, b=4)
