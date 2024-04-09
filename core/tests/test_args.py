import re

import pytest
from compone import Component, html


@Component
def IntDefaultsComp(*, a=1, b=2):
    return html.Div(a=a, b=b)


@Component
def StrDefaultsComp(*, a="alma", b="korte"):
    return html.Div(a=a, b=b)


class TestFuncDefaults:
    def test_defaults_kept(self):
        comp = IntDefaultsComp()
        assert str(comp) == """<div a="1" b="2"></div>"""

    def test_defaults_kept_when_appending(self):
        comp = IntDefaultsComp().append(a=3)
        assert str(comp) == """<div a="4" b="2"></div>"""

    def test_defaults_kept_when_appending_multiple(self):
        comp = IntDefaultsComp().append(a=3).append(a=5)
        assert str(comp) == """<div a="9" b="2"></div>"""

    def test_defaults_replaced(self):
        comp = IntDefaultsComp().replace(a=3)
        assert str(comp) == """<div a="3" b="2"></div>"""

    def test_mixed_defaults_and_no_defaults(self):
        @Component
        def MixedDefaultsComp(*, a, b=2):
            return html.Div(a=a, b=b)

        comp = MixedDefaultsComp(a=1).append(a=3)
        assert str(comp) == """<div a="4" b="2"></div>"""

        comp = MixedDefaultsComp(a=4).append(b=3)
        assert str(comp) == """<div a="4" b="5"></div>"""

        comp = MixedDefaultsComp(a=4).append(a=5, b=3)
        assert str(comp) == """<div a="9" b="5"></div>"""

    def test_defaults_kept_with_str(self):
        comp = StrDefaultsComp()
        assert str(comp) == """<div a="alma" b="korte"></div>"""

    def test_defaults_kept_when_appending_with_str(self):
        comp = StrDefaultsComp().append(a="barack")
        assert str(comp) == """<div a="almabarack" b="korte"></div>"""

    def test_defaults_kept_when_appending_multiple_str(self):
        comp = StrDefaultsComp().append(a=" barack").append(a=" cseresznye")
        assert str(comp) == """<div a="alma barack cseresznye" b="korte"></div>"""

    def test_defaults_replaced_with_str(self):
        comp = StrDefaultsComp().replace(a="barack")
        assert str(comp) == """<div a="barack" b="korte"></div>"""

    def test_different_types_raises_TypeError(self):
        with pytest.raises(TypeError):
            IntDefaultsComp().append(a="barack")


@Component
class ClassCompIntDefaults:
    def __init__(self, *, a=1, b=2):
        self.a = a
        self.b = b

    def render(self):
        return html.Div(a=self.a, b=self.b)


@Component
class ClassCompStrDefaults:
    def __init__(self, *, a="alma", b="korte"):
        self.a = a
        self.b = b

    def render(self):
        return html.Div(a=self.a, b=self.b)


class TestClassDefaults:
    def test_defaults_kept(self):
        comp = ClassCompIntDefaults()
        assert str(comp) == """<div a="1" b="2"></div>"""

    def test_defaults_kept_when_appending(self):
        comp = ClassCompIntDefaults().append(a=3)
        assert str(comp) == """<div a="4" b="2"></div>"""

    def test_defaults_kept_when_appending_multiple(self):
        comp = ClassCompIntDefaults().append(a=3).append(a=5)
        assert str(comp) == """<div a="9" b="2"></div>"""

    def test_defaults_replaced(self):
        comp = ClassCompIntDefaults().replace(a=3)
        assert str(comp) == """<div a="3" b="2"></div>"""

    def test_defaults_kept_with_str(self):
        comp = ClassCompStrDefaults()
        assert str(comp) == """<div a="alma" b="korte"></div>"""

    def test_defaults_kept_when_appending_with_str(self):
        comp = ClassCompStrDefaults().append(a="barack")
        assert str(comp) == """<div a="almabarack" b="korte"></div>"""

    def test_defaults_kept_when_appending_multiple_str(self):
        comp = ClassCompStrDefaults().append(a=" barack").append(a=" cseresznye")
        assert str(comp) == """<div a="alma barack cseresznye" b="korte"></div>"""

    def test_different_types_raises_TypeError(self):
        with pytest.raises(TypeError):
            ClassCompIntDefaults().append(a="barack")

    def test_None_is_not_kept_as_default(self):
        @Component
        def NoneDefaultsComp(*, a=None, b=2):
            return html.Div(a=a, b=b)

        comp1 = NoneDefaultsComp()
        assert str(comp1) == """<div b="2"></div>"""

        # shold not raise TypeError
        comp2 = NoneDefaultsComp().append(a=3)
        assert str(comp2) == """<div a="3" b="2"></div>"""


def test_None_is_not_rendered_for_html_components():
    comp = html.Div(a=None, b=1)
    assert str(comp) == """<div b="1"></div>"""


@Component
def CompWithArgsOnly(a, b, /):
    return html.Div(a=a, b=b)


def test_args_saved_as_named_props():
    comp = CompWithArgsOnly(1, 2)
    assert comp.props == {"a": 1, "b": 2}


@pytest.mark.skip
def test_props_can_be_mutated():
    comp = CompWithArgsOnly(1, 2)
    comp.props["a"] = 3
    assert str(comp) == """<div a="3" b="2"></div>"""


def test_append_works_on_args_only_components():
    comp = CompWithArgsOnly(1, 2).append(a=3)
    assert str(comp) == """<div a="4" b="2"></div>"""


def test_missing_args():
    with pytest.raises(TypeError):
        CompWithArgsOnly()


def test_more_args():
    with pytest.raises(
        TypeError,
        match=re.escape("too many positional arguments"),
    ):
        CompWithArgsOnly(1, 2, 3)


def test_component_with_more_args_and_kwarg():
    with pytest.raises(
        TypeError,
        match=re.escape("too many positional arguments"),
    ):
        CompWithArgsOnly(1, 2, 3, c=4)


def test_merge_works_on_args_only_components():
    @Component
    def MyComp(a, b=2, /):
        return html.Div(a=a, b=b)

    comp = MyComp(1).replace(b=4)
    assert str(comp) == """<div a="1" b="4"></div>"""


@Component
def CompWithMixedArgs(a, b=2, *, c, d=4):
    return html.Div(a=a, b=b, c=c, d=d)


@pytest.mark.parametrize(
    "comp, expected",
    [
        (CompWithMixedArgs(1, 5, c=3), """<div a="1" b="5" c="3" d="4"></div>"""),
        (CompWithMixedArgs(5, c=3), """<div a="5" b="2" c="3" d="4"></div>"""),
        (CompWithMixedArgs(a=1, c=3), """<div a="1" b="2" c="3" d="4"></div>"""),
        (CompWithMixedArgs(a=1, b=5, c=4), """<div a="1" b="5" c="4" d="4"></div>"""),
    ],
)
def test_comp_with_mixed_args(comp, expected):
    assert str(comp) == expected


@Component
def CompWithKwargs(a, b, **kwargs):
    return html.Div(a=a, b=b, **kwargs)


def test_component_with_kwargs():
    comp1 = CompWithKwargs(1, 2, c=3, d=4)
    assert str(comp1) == """<div a="1" b="2" c="3" d="4"></div>"""

    comp2 = CompWithKwargs(1, 2)
    assert str(comp2) == """<div a="1" b="2"></div>"""


def test_comp_with_kwargs_append():
    comp = CompWithKwargs(1, 2).append(c=3, d=4)
    assert str(comp) == """<div a="1" b="2" c="3" d="4"></div>"""


def test_components_append_non_existing_prop():
    @Component
    def MyComp(a, b):
        return html.Div(a=a, b=b)

    with pytest.raises(TypeError, match=".*unexpected keyword argument"):
        MyComp(1, 2).append(c=3)

    with pytest.raises(TypeError, match=".*unexpected keyword argument"):
        MyComp(1, 2).append(c=3, d=4)


def test_replace_raise_TypeError_for_non_existing_prop():
    @Component
    def MyComp(a, b):
        return html.Div(a=a, b=b)

    with pytest.raises(TypeError, match=".*unexpected keyword argument"):
        MyComp(1, 2).replace(c=3)

    with pytest.raises(TypeError, match=".*unexpected keyword argument"):
        MyComp(1, 2).replace(c=3, d=4)
