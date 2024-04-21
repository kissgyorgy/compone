import pytest
from compone import html, safe


@pytest.mark.parametrize(
    "elem, expected",
    [
        pytest.param(
            html.Div(data_attr=safe('{ some: "data" }')),
            """<div data-attr='{ some: "data" }'></div>""",
            id="contains double quote",
        ),
        pytest.param(
            html.Div(data_attr=safe("{ some: 'data' }")),
            """<div data-attr="{ some: 'data' }"></div>""",
            id="contains single quote",
        ),
    ],
)
def test_quotes_in_attribute_value(elem, expected):
    assert str(elem) == expected


def test_both_quotes_in_attribute_value():
    with pytest.raises(ValueError):
        str(html.Div(data_attr=safe("""{ some: "data", someOther: 'data' }""")))


def test_html_component_replace():
    div = html.Div(a=1, b=2)
    new_div = div.replace(a=3, b=4)

    assert str(div) == """<div a="1" b="2"></div>"""
    assert str(new_div) == """<div a="3" b="4"></div>"""


def test_html_components_are_comparable():
    div1 = html.Div(a=1, b=2)["Hello"]
    div2 = html.Div(a=1, b=2)["Hello"]
    div3 = html.Div(a=1, b=2)["World"]

    assert div1 == div2
    assert div2 != div3

    assert div1 is not div2
    assert div2 is not div3

    assert div1.children == div2.children
    assert div2.children != div3.children


def test_self_closing_html_components_are_comparable():
    img1 = html.Img(src="/image.jpg")
    img2 = html.Img(src="/image.jpg")
    img3 = html.Img(src="/image2.jpg")

    assert img1 == img2
    assert img2 != img3

    assert img1 is not img2
    assert img2 is not img3


def test_class_list():
    div1 = html.Div(class_=["alma", "korte"])
    div2 = div1.append(class_=["barack"])
    assert str(div2) == """<div class="alma korte barack"></div>"""


def test_multiple_spaces_are_removed():
    div1 = html.Div(class_="alma    korte  barack\nrepa")
    assert str(div1) == """<div class="alma korte barack repa"></div>"""

    div2 = html.Div(class_=["  alma  ", "  korte  "])
    assert str(div2) == """<div class="alma korte"></div>"""

    div3 = div2.append(class_=["  barack  "])
    assert str(div3) == """<div class="alma korte barack"></div>"""


def test_class_str_and_list_can_be_mixed():
    div1 = html.Div(class_="alma")
    div2 = div1.append(class_=["korte", "barack"])
    assert str(div2) == """<div class="alma korte barack"></div>"""

    div3 = div2.append(class_="repa")
    assert str(div3) == """<div class="alma korte barack repa"></div>"""

    div4 = html.Div(class_=["alma", "korte"])
    div5 = div4.append(class_="barack")
    assert str(div5) == """<div class="alma korte barack"></div>"""


def test_class_accept_None():
    div1 = html.Div(class_=None)
    assert str(div1) == """<div></div>"""

    div2 = html.Div(class_=["alma", None, "korte"])
    assert str(div2) == """<div class="alma korte"></div>"""


def test_classes_are_stripped():
    div1 = html.Div(class_="  alma  ")
    assert str(div1) == """<div class="alma"></div>"""

    div2 = html.Div(class_=["  alma  ", "  korte  "])
    assert str(div2) == """<div class="alma korte"></div>"""

    div3 = div2.append(class_=["  barack  "])
    assert str(div3) == """<div class="alma korte barack"></div>"""


def test_class_elems_can_have_multiple():
    div1 = html.Div(class_=["alma", "  korte  barack repa"])
    assert str(div1) == """<div class="alma korte barack repa"></div>"""

    div3 = div1.append(class_=["szilva    cseresznye"])
    assert (
        str(div3) == """<div class="alma korte barack repa szilva cseresznye"></div>"""
    )
