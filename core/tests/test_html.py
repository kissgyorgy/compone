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
