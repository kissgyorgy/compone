import pytest
from compone import escape, html, safe
from compone.utils import is_iterable, snake_to_camel_case


@pytest.mark.parametrize(
    "input_value, expected_output",
    [
        ("snake_case", "snakeCase"),
        ("Snake_case", "SnakeCase"),
        ("SnakeCase", "SnakeCase"),
    ],
)
def test_snake_case(input_value, expected_output):
    assert snake_to_camel_case(input_value) == expected_output


@pytest.mark.parametrize(
    "value, expected",
    [
        ("string", False),
        (1, False),
        (None, False),
        (safe, False),
        (escape("string"), False),
        ([1, 2, 3], True),
        ((1, 2, 3), True),
        ({1, 2, 3}, True),
        ({"a": 1, "b": 2, "c": 3}, True),
        (str(html.Div()), False),
        (range(10), True),
        (map(str, range(10)), True),
        (filter(lambda x: x % 2 == 0, range(10)), True),
        (zip(range(10), range(10)), True),
    ],
)
def test_is_iterable_component(value, expected):
    assert is_iterable(value) is expected
