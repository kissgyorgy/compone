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
        html.Div(data_attr=safe("""{ some: "data", someOther: 'data' }"""))
