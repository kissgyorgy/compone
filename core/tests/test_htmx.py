from compone import html, htmx


def test_htmx_attribute_chaining():
    htmx_attrs = htmx.Hx().get("/example").push_url(True).swap(htmx.Swap.INNER_HTML)
    assert (
        str(html.Div(**htmx_attrs))
        == '<div hx-get="/example" hx-push-url="true" hx-swap="innerHTML"></div>'
    )


def test_config():
    config = htmx.Config(history_enabled=True, default_swap_style=htmx.Swap.OUTER_HTML)
    assert str(config) == (
        '<meta name="htmx-config" content='
        """'{"historyEnabled": true, "defaultSwapStyle": "outerHTML"}'"""
        " />"
    )
