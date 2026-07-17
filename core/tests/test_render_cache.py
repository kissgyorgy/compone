from compone import Component, html


@Component
def ItemList(items: list[str]) -> object:
    return html.Ul[[html.Li[item] for item in items]]


@Component
def DataLabel(data: dict[str, str]) -> object:
    return html.Span(data_kind=data["kind"])[data["label"]]


def test_render_cache_observes_list_mutations():
    items = ["first", "second"]
    expected = "<ul><li>first</li><li>second</li></ul>"
    assert tuple(str(ItemList(items)) for _ in range(3)) == (expected,) * 3

    items[1] = "changed"
    items.append("third")
    assert str(ItemList(items)) == (
        "<ul><li>first</li><li>changed</li><li>third</li></ul>"
    )


def test_render_cache_observes_dict_mutations():
    data = {"kind": "status", "label": "ready"}
    expected = '<span data-kind="status">ready</span>'
    assert tuple(str(DataLabel(data)) for _ in range(3)) == (expected,) * 3

    data["kind"] = "result"
    data["label"] = "finished"
    assert str(DataLabel(data)) == '<span data-kind="result">finished</span>'
