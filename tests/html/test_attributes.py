import pytest

from compone import html, safe


@pytest.mark.parametrize(
    "html_component, expected_str",
    [
        (html.Html, "<html></html>"),
        (html.Body, "<body></body>"),
        (html.Link, "<link />"),
        (html.A, "<a></a>"),
        (html.Script, "<script></script>"),
        (html.P, "<p></p>"),
        (html.Img, "<img />"),
        (html.Input, "<input />"),
        (html.Ul, "<ul></ul>"),
        (html.Li, "<li></li>"),
    ],
)
def test_html_component_instances(html_component, expected_str):
    assert isinstance(str(html_component()), safe)
    assert str(html_component()) == expected_str


@pytest.mark.parametrize(
    "html_component, expected_str",
    [
        (html.Html(lang="en"), '<html lang="en"></html>'),
        (html.Body(class_="main"), '<body class="main"></body>'),
        (html.Link(src="https://example.com"), '<link src="https://example.com" />'),
        (html.A(href="https://google.com"), '<a href="https://google.com"></a>'),
        (html.Script(src="something.js"), '<script src="something.js"></script>'),
        (html.P(style="display: hidden;"), '<p style="display: hidden;"></p>'),
        (
            html.Img(src="https://cataas.com/cat"),
            '<img src="https://cataas.com/cat" />',
        ),
        (html.Input(type="text"), '<input type="text" />'),
        (html.Ul(style="list-style: square;"), '<ul style="list-style: square;"></ul>'),
    ],
)
def test_html_single_attribute(html_component, expected_str):
    assert isinstance(str(html_component), safe)
    assert str(html_component) == expected_str


@pytest.mark.parametrize(
    "html_component, expected_str",
    [
        (
            html.Html(lang="en", class_="main-content"),
            '<html lang="en" class="main-content"></html>',
        ),
        (
            html.Body(class_="main", style="margin-bottom: 10px;"),
            '<body class="main" style="margin-bottom: 10px;"></body>',
        ),
        (
            html.Link(src="https://example.com", type="text/css"),
            '<link src="https://example.com" type="text/css" />',
        ),
        (
            html.A(href="https://google.com", target="_blank"),
            '<a href="https://google.com" target="_blank"></a>',
        ),
        (
            html.Script(src="something.js", type="application/javascript"),
            '<script src="something.js" type="application/javascript"></script>',
        ),
        (
            html.P(style="display: hidden;", class_="mb-20"),
            '<p style="display: hidden;" class="mb-20"></p>',
        ),
        (
            html.Img(src="https://cataas.com/cat", width=40),
            '<img src="https://cataas.com/cat" width="40" />',
        ),
        (
            html.Input(type="text", disabled="disabled"),
            '<input type="text" disabled="disabled" />',
        ),
    ],
)
def test_html_multiple_attributes(html_component, expected_str):
    assert isinstance(str(html_component), safe)
    assert str(html_component) == expected_str


@pytest.mark.parametrize(
    "html_component, expected_str",
    [
        (html.Label(for_="id_name"), '<label for="id_name"></label>'),
        (html.Html(class_="width-full"), '<html class="width-full"></html>'),
        (html.P(is_="word-count"), '<p is="word-count"></p>'),
    ],
)
def test_html_special_attributes(html_component, expected_str):
    assert isinstance(str(html_component), safe)
    assert str(html_component) == expected_str


@pytest.mark.parametrize(
    "html_component, expected_str",
    [
        (html.Html(data_x="5"), '<html data-x="5"></html>'),
        (
            html.Img(src="https://cataas.com/cat", use_credentials="include"),
            '<img src="https://cataas.com/cat" use-credentials="include" />',
        ),
        (
            html.Div(aria_valuenow=75),
            '<div aria-valuenow="75"></div>',
        ),
    ],
)
def test_html_underscore_converted_to_hyphen(html_component, expected_str):
    assert isinstance(str(html_component), safe)
    assert str(html_component) == expected_str


@pytest.mark.parametrize(
    "html_component, expected_str",
    [
        (html.Button(disabled=True), "<button disabled></button>"),
        (html.Button(disabled=False), "<button></button>"),
        (
            html.Input(type="checkbox", checked=True),
            '<input checked type="checkbox" />',
        ),
        (
            html.Input(type="checkbox", checked=False),
            '<input type="checkbox" />',
        ),
        # TODO: html boolean attributes should be recognized by name
    ],
)
def test_boolean_attributes(html_component, expected_str):
    assert isinstance(str(html_component), safe)
    assert str(html_component) == expected_str


def test_data_attributes():
    article = html.Article(
        data_columns=3, data_index_number="12314", data_parent="cars"
    )
    assert (
        str(article)
        == '<article data-columns="3" data-index-number="12314" data-parent="cars">'
        "</article>"
    )
