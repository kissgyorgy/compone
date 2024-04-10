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
