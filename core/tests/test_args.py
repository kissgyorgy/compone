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

        comp = MixedDefaultsComp().append(a=3)
        assert str(comp) == """<div a="3" b="2"></div>"""

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

        # shold not raise TypeError
        comp = NoneDefaultsComp().append(a=3)
        assert str(comp) == """<div a="3" b="2"></div>"""


def test_None_is_not_rendered_for_html_components():
    comp = html.Div(a=None, b=1)
    assert str(comp) == """<div b="1"></div>"""
