import pytest
from compone import html


def test_original_class_args_not_affected():
    original = {"class_": "red     blue"}
    html.P(class_="green").append(**original)
    assert original == {"class_": "red     blue"}


def test_html_class_append_different_name():
    original = {"class": "red     blue"}
    with pytest.raises(TypeError):
        html.P(class_="green").append(**original)

    with pytest.raises(TypeError):
        html.P(class_="green").replace(**original)
