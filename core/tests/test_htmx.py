from compone import html, htmx


def test_config():
    config = htmx.Config(history_enabled=True, default_swap_style=htmx.Swap.OUTER_HTML)
    assert str(config) == (
        '<meta name="htmx-config" content='
        """'{"historyEnabled": true, "defaultSwapStyle": "outerHTML"}'"""
        " />"
    )
