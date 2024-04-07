import pytest
from compone import Component, html


def test_component_cannot_overwrite_children_with_getitem():
    @Component
    def WithChildren(*, children):
        return html.Div[children]

    comp = WithChildren["Hello"]
    with pytest.raises(ValueError):
        comp["Another_children"]
