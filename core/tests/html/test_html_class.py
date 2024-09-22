from compone import html


def test_original_class_args_not_affected():
    original = {"class_": "red     blue"}
    html.P(class_="green").append(**original)
    assert original == {"class_": "red     blue"}
