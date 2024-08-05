import pytest
from compone.html import classes


@pytest.mark.parametrize(
    "input, expected",
    [
        (("",), ""),
        (("", None), ""),
        ((None, None), ""),
        ((None, False), ""),
        ((None, []), ""),
        (([None, None], None), ""),
        (("red",), "red"),
        (("red blue",), "red blue"),
        (("red red red",), "red"),
        (("red  blue",), "red blue"),
        ((["red", "blue"],), "red blue"),
        ((["red", "blue"], "green"), "red blue green"),
        ((["red ", " blue"],), "red blue"),
        ((["red green", "blue"],), "red green blue"),
        ((["red  green ", " blue"],), "red green blue"),
        ((["red  green\n ", " blue"], "apple orange"), "red green blue apple orange"),
        ((["red  green\n grey", " blue"],), "red green grey blue"),
        ((["red  green\n grey", " blue"], "yellow"), "red green grey blue yellow"),
        (({"red": True, "blue": False},), "red"),
        (({"red": True, "blue": False}, "red"), "red"),
        (("red", {"red": True, "blue": False}), "red"),
        (({"red ": True, " blue": False},), "red"),
        (({"red ": False, " blue": True},), "blue"),
        (
            ({"red ": False, " blue": True}, {"  orange  ": True, "black": False}),
            "blue orange",
        ),
    ],
)
def test_classes_helper(input: tuple, expected: str):
    assert classes(*input) == expected.split()
