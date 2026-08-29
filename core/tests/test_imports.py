from pathlib import Path
from types import ModuleType

import compone
import compone.component as component
import compone.elements as elements
import compone.html as html
import compone.html.elements.content_sectioning as content_sectioning
import compone.html.elements.embedded as embedded
import compone.html.elements.forms as forms
import compone.html.elements.inline_text as inline_text
import compone.html.elements.interactive as interactive
import compone.html.elements.main as main
import compone.html.elements.metadata as metadata
import compone.html.elements.multimedia as multimedia
import compone.html.elements.other as other
import compone.html.elements.scripting as scripting
import compone.html.elements.table as table
import compone.html.elements.text_content as text_content
import compone.html.elements.web_components as web_components
import compone.html.helpers as helpers
import compone.html.html_elements as html_elements
import compone.htmx as htmx
import compone.htmx.config as htmx_config
import compone.htmx.constants as htmx_constants
import compone.robots as robots
import compone.robots.html_meta as robots_html_meta
import compone.robots.robots_txt as robots_txt
import compone.utils as utils
import compone.xml as xml
import pytest

IS_RUST_PACKAGE = Path(compone.__file__).suffix in {
    ".pyd",
    ".so",
}


def same_export(
    left: ModuleType,
    right: ModuleType,
    name: str,
) -> bool:
    return vars(left)[name] is vars(right)[name]


@pytest.mark.skipif(not IS_RUST_PACKAGE, reason="requires the released Rust package")
def test_compone_is_the_compiled_extension():
    assert IS_RUST_PACKAGE


def test_existing_import_paths_resolve_to_native_exports():
    assert {
        "component": same_export(component, compone, "Component"),
        "element": same_export(elements, compone, "Element"),
        "content_sectioning": same_export(content_sectioning, html, "Article"),
        "embedded": same_export(embedded, html, "Embed"),
        "forms": same_export(forms, html, "SubmitButton"),
        "inline_text": same_export(inline_text, html, "Span"),
        "interactive": same_export(interactive, html, "Dialog"),
        "main": same_export(main, html, "Html"),
        "metadata": same_export(metadata, html, "Meta"),
        "multimedia": same_export(multimedia, html, "Video"),
        "other": same_export(other, html, "Svg"),
        "scripting": same_export(scripting, html, "Script"),
        "table": same_export(table, html, "Table"),
        "text_content": same_export(text_content, html, "Div"),
        "web_components": same_export(web_components, html, "Template"),
        "helpers": same_export(helpers, html, "classes"),
        "htmx_config": same_export(htmx_config, htmx, "Config"),
        "htmx_constants": same_export(htmx_constants, htmx, "Swap"),
        "robots_meta": same_export(robots_html_meta, robots, "MetaTag"),
        "robots_txt": same_export(robots_txt, robots, "Entry"),
    } == {
        "component": True,
        "element": True,
        "content_sectioning": True,
        "embedded": True,
        "forms": True,
        "inline_text": True,
        "interactive": True,
        "main": True,
        "metadata": True,
        "multimedia": True,
        "other": True,
        "scripting": True,
        "table": True,
        "text_content": True,
        "web_components": True,
        "helpers": True,
        "htmx_config": True,
        "htmx_constants": True,
        "robots_meta": True,
        "robots_txt": True,
    }


@pytest.mark.skipif(not IS_RUST_PACKAGE, reason="requires the released Rust package")
def test_modules_do_not_export_private_names():
    modules = [
        compone,
        component,
        elements,
        html,
        content_sectioning,
        embedded,
        forms,
        inline_text,
        interactive,
        main,
        metadata,
        multimedia,
        other,
        scripting,
        table,
        text_content,
        web_components,
        helpers,
        html_elements,
        htmx,
        htmx_config,
        htmx_constants,
        robots,
        robots_html_meta,
        robots_txt,
        utils,
        xml,
    ]
    assert {
        module.__name__: sorted(
            name
            for name in vars(module)
            if name.startswith("_") and not name.startswith("__")
        )
        for module in modules
    } == {module.__name__: [] for module in modules}
