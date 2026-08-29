from collections.abc import Callable
from functools import lru_cache
from importlib import import_module
from typing import Protocol, TypedDict, TypeVar, cast

import pytest
from jinja2 import DictLoader, Environment, select_autoescape


class Element(Protocol):
    def __getitem__(self, children: object, /) -> "Element": ...


class Tag(Protocol):
    def __call__(self, **kwargs: object) -> Element: ...

    def __getitem__(self, children: object, /) -> Element: ...


class Html(Protocol):
    def __getattr__(self, name: str, /) -> Tag: ...


ComponentFunction = TypeVar("ComponentFunction", bound=Callable[..., object])


class ComponentDecorator(Protocol):
    def __call__(
        self,
        component: ComponentFunction,
        /,
    ) -> ComponentFunction: ...


class Benchmark(Protocol):
    def __call__(self, target: Callable[[], str], /) -> str: ...

    def pedantic(
        self,
        target: Callable[[tuple[int, int]], str],
        *,
        setup: Callable[
            [],
            tuple[tuple[tuple[int, int]], dict[str, object]],
        ],
        rounds: int,
        iterations: int,
    ) -> str: ...


class SmallCardData(TypedDict):
    title: str
    body: str
    href: str


class StatData(TypedDict):
    label: str
    value: str
    status: str


class BoardItemData(TypedDict):
    name: str
    description: str
    badges: list[str]


class BoardGroupData(TypedDict):
    title: str
    items: list[BoardItemData]


class NavItemData(TypedDict):
    href: str
    label: str


class FeatureData(TypedDict):
    slug: str
    title: str
    body: str


class PlanData(TypedDict):
    name: str
    price: str
    features: list[str]


class FaqData(TypedDict):
    question: str
    answer: str


class ImportFeatureData(TypedDict):
    title: str
    body: str


compone = import_module("compone")
Component = cast(ComponentDecorator, vars(compone)["Component"])
html = cast(Html, cast(object, import_module("compone.html")))

TINY_EXPECTED = '<div a="3" b="4"></div>'
TINY_CHILD_EXPECTED = '<div a="3" b="4">simple children</div>'
FIRST_RENDER_VALUE_COUNT = 100
FIRST_RENDER_VALUES = tuple(
    (index + 1_000, index + 2_000) for index in range(FIRST_RENDER_VALUE_COUNT)
)
FIRST_RENDER_EXPECTED = tuple(
    f'<div a="{a}" b="{b}"></div>' for a, b in FIRST_RENDER_VALUES
)

SMALL_CARD: SmallCardData = {
    "title": "Launch Notes",
    "body": "Fast Rust rendering",
    "href": "/notes",
}
SMALL_CARD_EXPECTED = (
    '<article class="card" data-id="42">'
    "<h2>Launch Notes</h2>"
    "<p>Fast Rust rendering</p>"
    '<a href="/notes">Read more</a>'
    "</article>"
)

STATS: list[StatData] = [
    {"label": "Requests", "value": "128k", "status": "ok"},
    {"label": "Latency", "value": "18ms", "status": "ok"},
    {"label": "Errors", "value": "7", "status": "warn"},
    {"label": "Workers", "value": "12", "status": "ok"},
]
MEDIUM_PANEL_EXPECTED = (
    '<section class="panel"><h2>Build metrics</h2><ul>'
    '<li class="status status-ok" data-status="ok">'
    '<span class="label">Requests</span><strong>128k</strong></li>'
    '<li class="status status-ok" data-status="ok">'
    '<span class="label">Latency</span><strong>18ms</strong></li>'
    '<li class="status status-warn" data-status="warn">'
    '<span class="label">Errors</span><strong>7</strong></li>'
    '<li class="status status-ok" data-status="ok">'
    '<span class="label">Workers</span><strong>12</strong></li>'
    "</ul></section>"
)

NESTED_GROUPS: list[BoardGroupData] = [
    {
        "title": "Core",
        "items": [
            {
                "name": "Components",
                "description": "Composable Python objects",
                "badges": ["typed", "reusable"],
            },
            {
                "name": "Rendering",
                "description": "HTML without templates",
                "badges": ["safe", "fast"],
            },
        ],
    },
    {
        "title": "Integrations",
        "items": [
            {
                "name": "Static sites",
                "description": "Generate pages ahead of time",
                "badges": ["ssg", "docs"],
            },
            {
                "name": "Frameworks",
                "description": "Use the same components everywhere",
                "badges": ["flask", "django"],
            },
        ],
    },
]
NESTED_BOARD_EXPECTED = (
    '<section class="board"><h2>Component map</h2><div class="groups">'
    '<article class="group"><h3>Core</h3><ul>'
    "<li><h4>Components</h4><p>Composable Python objects</p>"
    '<div class="badges"><span class="badge">typed</span>'
    '<span class="badge">reusable</span></div></li>'
    "<li><h4>Rendering</h4><p>HTML without templates</p>"
    '<div class="badges"><span class="badge">safe</span>'
    '<span class="badge">fast</span></div></li>'
    "</ul></article>"
    '<article class="group"><h3>Integrations</h3><ul>'
    "<li><h4>Static sites</h4><p>Generate pages ahead of time</p>"
    '<div class="badges"><span class="badge">ssg</span>'
    '<span class="badge">docs</span></div></li>'
    "<li><h4>Frameworks</h4><p>Use the same components everywhere</p>"
    '<div class="badges"><span class="badge">flask</span>'
    '<span class="badge">django</span></div></li>'
    "</ul></article>"
    "</div></section>"
)

NAV_ITEMS: list[NavItemData] = [
    {"href": "/", "label": "Home"},
    {"href": "/docs", "label": "Docs"},
    {"href": "/pricing", "label": "Pricing"},
]
FEATURES: list[FeatureData] = [
    {
        "slug": "speed",
        "title": "Speed",
        "body": "Rust-backed rendering with low overhead",
    },
    {
        "slug": "safety",
        "title": "Safety",
        "body": "Escaped output by default",
    },
    {
        "slug": "types",
        "title": "Types",
        "body": "Components keep Python signatures",
    },
    {
        "slug": "reuse",
        "title": "Reuse",
        "body": "Share UI across frameworks",
    },
]
PLANS: list[PlanData] = [
    {"name": "Starter", "price": "$19", "features": ["One project", "Email support"]},
    {"name": "Team", "price": "$49", "features": ["Ten projects", "Priority support"]},
    {"name": "Scale", "price": "$99", "features": ["Unlimited", "Private chat"]},
]
FAQ_ITEMS: list[FaqData] = [
    {"question": "Is it typed?", "answer": "Yes, components keep Python signatures."},
    {"question": "Can it nest?", "answer": "Yes, children compose naturally."},
    {"question": "Is output escaped?", "answer": "Yes, unsafe strings are escaped."},
]
BIG_PAGE_EXPECTED = (
    '<main class="landing">'
    '<header class="site-header"><a href="/" class="brand">Compone</a><nav>'
    '<a href="/">Home</a><a href="/docs">Docs</a><a href="/pricing">Pricing</a>'
    "</nav></header>"
    '<section class="hero"><p class="eyebrow">Python components</p>'
    "<h1>Build HTML with objects</h1>"
    '<p class="lead">Reusable typed UI without template strings</p>'
    '<a href="/docs" class="cta">Read the docs</a></section>'
    '<section class="features"><h2>Features</h2><div class="feature-grid">'
    '<article class="feature" data-slug="speed"><h3>Speed</h3>'
    "<p>Rust-backed rendering with low overhead</p></article>"
    '<article class="feature" data-slug="safety"><h3>Safety</h3>'
    "<p>Escaped output by default</p></article>"
    '<article class="feature" data-slug="types"><h3>Types</h3>'
    "<p>Components keep Python signatures</p></article>"
    '<article class="feature" data-slug="reuse"><h3>Reuse</h3>'
    "<p>Share UI across frameworks</p></article>"
    "</div></section>"
    '<section class="pricing"><h2>Pricing</h2><div class="plans">'
    '<article class="plan"><h3>Starter</h3><p class="price">$19</p><ul>'
    "<li>One project</li><li>Email support</li></ul></article>"
    '<article class="plan"><h3>Team</h3><p class="price">$49</p><ul>'
    "<li>Ten projects</li><li>Priority support</li></ul></article>"
    '<article class="plan"><h3>Scale</h3><p class="price">$99</p><ul>'
    "<li>Unlimited</li><li>Private chat</li></ul></article>"
    "</div></section>"
    '<section class="faq"><h2>Questions</h2>'
    "<details><summary>Is it typed?</summary>"
    "<p>Yes, components keep Python signatures.</p></details>"
    "<details><summary>Can it nest?</summary>"
    "<p>Yes, children compose naturally.</p></details>"
    "<details><summary>Is output escaped?</summary>"
    "<p>Yes, unsafe strings are escaped.</p></details>"
    "</section>"
    '<footer class="footer"><p>© 2026 Compone</p></footer>'
    "</main>"
)

IMPORT_FEATURES: list[ImportFeatureData] = [
    {"title": "Macro parity", "body": "Jinja import renders the same HTML"},
    {"title": "Component parity", "body": "Compone components render matching HTML"},
]
IMPORTED_EXPECTED = (
    '<section class="imported"><header><h2>Imported macros</h2><nav>'
    '<a href="/">Home</a><a href="/docs">Docs</a><a href="/pricing">Pricing</a>'
    "</nav></header>"
    '<div class="cards"><article><h3>Macro parity</h3>'
    "<p>Jinja import renders the same HTML</p></article>"
    "<article><h3>Component parity</h3>"
    "<p>Compone components render matching HTML</p></article></div>"
    "</section>"
)


@Component
def TinyComp(a: int, b: int) -> object:
    return html.Div(a=a, b=b)


@Component
@lru_cache
def CachedTinyComp(a: int, b: int) -> object:
    return html.Div(a=a, b=b)


@Component
def TinyChildComp(a: int, b: int, children: object = None) -> object:
    return html.Div(a=a, b=b)[children]


TinyChildComponent = cast(Callable[[int, int], Element], TinyChildComp)


@Component
def SmallCard(title: str, body: str, href: str) -> object:
    return html.Article(class_="card", data_id="42")[
        html.H2[title],
        html.P[body],
        html.A(href=href)["Read more"],
    ]


@Component
def StatRow(label: str, value: str, status: str) -> object:
    return html.Li(class_=f"status status-{status}", data_status=status)[
        html.Span(class_="label")[label],
        html.Strong[value],
    ]


@Component
def StatsPanel(title: str, items: list[StatData]) -> object:
    return html.Section(class_="panel")[
        html.H2[title],
        html.Ul[[StatRow(**item) for item in items]],
    ]


@Component
def Badge(text: str) -> object:
    return html.Span(class_="badge")[text]


@Component
def BoardItem(name: str, description: str, badges: list[str]) -> object:
    return html.Li[
        html.H4[name],
        html.P[description],
        html.Div(class_="badges")[[Badge(badge) for badge in badges]],
    ]


@Component
def BoardGroup(title: str, items: list[BoardItemData]) -> object:
    return html.Article(class_="group")[
        html.H3[title],
        html.Ul[[BoardItem(**item) for item in items]],
    ]


@Component
def NestedBoard(title: str, groups: list[BoardGroupData]) -> object:
    return html.Section(class_="board")[
        html.H2[title],
        html.Div(class_="groups")[[BoardGroup(**group) for group in groups]],
    ]


@Component
def SiteHeader(nav_items: list[NavItemData]) -> object:
    return html.Header(class_="site-header")[
        html.A(href="/", class_="brand")["Compone"],
        html.Nav[[html.A(href=item["href"])[item["label"]] for item in nav_items]],
    ]


@Component
def Hero() -> object:
    return html.Section(class_="hero")[
        html.P(class_="eyebrow")["Python components"],
        html.H1["Build HTML with objects"],
        html.P(class_="lead")["Reusable typed UI without template strings"],
        html.A(href="/docs", class_="cta")["Read the docs"],
    ]


@Component
def FeatureCard(slug: str, title: str, body: str) -> object:
    return html.Article(class_="feature", data_slug=slug)[html.H3[title], html.P[body]]


@Component
def FeatureSection(features: list[FeatureData]) -> object:
    return html.Section(class_="features")[
        html.H2["Features"],
        html.Div(class_="feature-grid")[
            [FeatureCard(**feature) for feature in features]
        ],
    ]


@Component
def PlanCard(name: str, price: str, features: list[str]) -> object:
    return html.Article(class_="plan")[
        html.H3[name],
        html.P(class_="price")[price],
        html.Ul[[html.Li[feature] for feature in features]],
    ]


@Component
def PricingSection(plans: list[PlanData]) -> object:
    return html.Section(class_="pricing")[
        html.H2["Pricing"],
        html.Div(class_="plans")[[PlanCard(**plan) for plan in plans]],
    ]


@Component
def FaqSection(items: list[FaqData]) -> object:
    return html.Section(class_="faq")[
        html.H2["Questions"],
        [
            html.Details[html.Summary[item["question"]], html.P[item["answer"]]]
            for item in items
        ],
    ]


@Component
def BigLandingPage(
    nav_items: list[NavItemData],
    features: list[FeatureData],
    plans: list[PlanData],
    faq_items: list[FaqData],
) -> object:
    return html.Main(class_="landing")[
        SiteHeader(nav_items),
        Hero(),
        FeatureSection(features),
        PricingSection(plans),
        FaqSection(faq_items),
        html.Footer(class_="footer")[html.P["© 2026 Compone"]],
    ]


@Component
def ImportedCard(title: str, body: str) -> object:
    return html.Article[html.H3[title], html.P[body]]


@Component
def ImportedComponentPage(
    nav_items: list[NavItemData],
    features: list[ImportFeatureData],
) -> object:
    return html.Section(class_="imported")[
        html.Header[
            html.H2["Imported macros"],
            html.Nav[[html.A(href=item["href"])[item["label"]] for item in nav_items]],
        ],
        html.Div(class_="cards")[[ImportedCard(**feature) for feature in features]],
    ]


def make_environment(templates: dict[str, str]) -> Environment:
    return Environment(loader=DictLoader(templates), autoescape=select_autoescape())


def render_template(env: Environment, name: str, **context: object) -> str:
    template = env.get_template(name)
    return template.render(**context)


TEMPLATES = {
    "tiny.html": '<div a="{{ a }}" b="{{ b }}"></div>',
    "tiny_child.html": '<div a="{{ a }}" b="{{ b }}">{{ children }}</div>',
    "small_card.html": (
        '<article class="card" data-id="42"><h2>{{ title }}</h2><p>{{ body }}</p>'
        '<a href="{{ href }}">Read more</a></article>'
    ),
    "medium_panel.html": (
        '<section class="panel"><h2>{{ title }}</h2><ul>'
        "{% for item in items %}"
        '<li class="status status-{{ item.status }}" '
        'data-status="{{ item.status }}">'
        '<span class="label">{{ item.label }}</span>'
        "<strong>{{ item.value }}</strong></li>"
        "{% endfor %}"
        "</ul></section>"
    ),
    "nested_board.html": (
        '<section class="board"><h2>{{ title }}</h2><div class="groups">'
        "{% for group in groups %}"
        '<article class="group"><h3>{{ group.title }}</h3><ul>'
        "{% for item in group['items'] %}"
        "<li><h4>{{ item.name }}</h4><p>{{ item.description }}</p>"
        '<div class="badges">'
        "{% for badge in item.badges %}"
        '<span class="badge">{{ badge }}</span>'
        "{% endfor %}"
        "</div></li>"
        "{% endfor %}"
        "</ul></article>"
        "{% endfor %}"
        "</div></section>"
    ),
    "big_page.html": (
        '<main class="landing">'
        '<header class="site-header"><a href="/" class="brand">Compone</a><nav>'
        "{% for item in nav_items %}"
        '<a href="{{ item.href }}">{{ item.label }}</a>'
        "{% endfor %}"
        "</nav></header>"
        '<section class="hero"><p class="eyebrow">Python components</p>'
        "<h1>Build HTML with objects</h1>"
        '<p class="lead">Reusable typed UI without template strings</p>'
        '<a href="/docs" class="cta">Read the docs</a></section>'
        '<section class="features"><h2>Features</h2><div class="feature-grid">'
        "{% for feature in features %}"
        '<article class="feature" data-slug="{{ feature.slug }}">'
        "<h3>{{ feature.title }}</h3><p>{{ feature.body }}</p></article>"
        "{% endfor %}"
        "</div></section>"
        '<section class="pricing"><h2>Pricing</h2><div class="plans">'
        "{% for plan in plans %}"
        '<article class="plan"><h3>{{ plan.name }}</h3>'
        '<p class="price">{{ plan.price }}</p><ul>'
        "{% for feature in plan.features %}<li>{{ feature }}</li>{% endfor %}"
        "</ul></article>"
        "{% endfor %}"
        "</div></section>"
        '<section class="faq"><h2>Questions</h2>'
        "{% for item in faq_items %}"
        "<details><summary>{{ item.question }}</summary>"
        "<p>{{ item.answer }}</p></details>"
        "{% endfor %}"
        "</section>"
        '<footer class="footer"><p>© 2026 Compone</p></footer>'
        "</main>"
    ),
    "macros.html": (
        "{% macro nav(items) %}<nav>{% for item in items %}"
        '<a href="{{ item.href }}">{{ item.label }}</a>'
        "{% endfor %}</nav>{% endmacro %}"
        "{% macro card(item) %}<article><h3>{{ item.title }}</h3>"
        "<p>{{ item.body }}</p></article>{% endmacro %}"
    ),
    "imported.html": (
        '{% import "macros.html" as ui %}'
        '<section class="imported"><header><h2>Imported macros</h2>'
        "{{ ui.nav(nav_items) }}</header>"
        '<div class="cards">{% for feature in features %}'
        "{{ ui.card(feature) }}{% endfor %}</div></section>"
    ),
}


@pytest.mark.benchmark(group="tiny")
def test_tiny_compone(benchmark: Benchmark):
    def run_compone() -> str:
        return str(TinyComp(3, 4))

    result = benchmark(run_compone)
    assert result == TINY_EXPECTED


@pytest.mark.benchmark(group="tiny")
def test_tiny_compone_cached(benchmark: Benchmark):
    def run_compone() -> str:
        return str(CachedTinyComp(3, 4))

    result = benchmark(run_compone)
    assert result == TINY_EXPECTED


@pytest.mark.benchmark(group="tiny")
def test_tiny_jinja2(benchmark: Benchmark):
    env = make_environment(TEMPLATES)

    def run_jinja2() -> str:
        return render_template(env, "tiny.html", a=3, b=4)

    result = benchmark(run_jinja2)
    assert result == TINY_EXPECTED


@pytest.mark.benchmark(group="tiny_child")
def test_tiny_child_compone(benchmark: Benchmark):
    def run_compone() -> str:
        return str(TinyChildComponent(3, 4)["simple children"])

    result = benchmark(run_compone)
    assert result == TINY_CHILD_EXPECTED


@pytest.mark.benchmark(group="tiny_child")
def test_tiny_child_jinja2(benchmark: Benchmark):
    env = make_environment(TEMPLATES)

    def run_jinja2() -> str:
        return render_template(
            env,
            "tiny_child.html",
            a=3,
            b=4,
            children="simple children",
        )

    result = benchmark(run_jinja2)
    assert result == TINY_CHILD_EXPECTED


@pytest.mark.benchmark(group="first_render_unique")
def test_first_render_unique_compone(benchmark: Benchmark):
    outputs: list[str] = []
    values = iter(FIRST_RENDER_VALUES)

    def setup() -> tuple[tuple[tuple[int, int]], dict[str, object]]:
        return (next(values),), {}

    def run_compone(value: tuple[int, int]) -> str:
        result = str(TinyComp(*value))
        outputs.append(result)
        return result

    # Each round uses a distinct value, so no render can hit the cache.
    result = benchmark.pedantic(
        run_compone,
        setup=setup,
        rounds=FIRST_RENDER_VALUE_COUNT,
        iterations=1,
    )
    assert result == outputs[-1]

    if len(outputs) < FIRST_RENDER_VALUE_COUNT:
        for value in FIRST_RENDER_VALUES[len(outputs) :]:
            outputs.append(str(TinyComp(*value)))

    normalized_outputs = tuple(str.__str__(output) for output in outputs)
    assert normalized_outputs == FIRST_RENDER_EXPECTED


@pytest.mark.benchmark(group="first_render_unique")
def test_first_render_unique_jinja2(benchmark: Benchmark):
    env = make_environment(TEMPLATES)
    outputs: list[str] = []
    values = iter(FIRST_RENDER_VALUES)

    def setup() -> tuple[tuple[tuple[int, int]], dict[str, object]]:
        return (next(values),), {}

    def run_jinja2(value: tuple[int, int]) -> str:
        a, b = value
        result = render_template(env, "tiny.html", a=a, b=b)
        outputs.append(result)
        return result

    # Match the Compone benchmark: one pedantic round per distinct value.
    result = benchmark.pedantic(
        run_jinja2,
        setup=setup,
        rounds=FIRST_RENDER_VALUE_COUNT,
        iterations=1,
    )
    assert result == outputs[-1]

    if len(outputs) < FIRST_RENDER_VALUE_COUNT:
        for a, b in FIRST_RENDER_VALUES[len(outputs) :]:
            outputs.append(render_template(env, "tiny.html", a=a, b=b))

    assert tuple(outputs) == FIRST_RENDER_EXPECTED


@pytest.mark.benchmark(group="small_card")
def test_small_card_compone(benchmark: Benchmark):
    def run_compone() -> str:
        return str(SmallCard(**SMALL_CARD))

    result = benchmark(run_compone)
    assert result == SMALL_CARD_EXPECTED


@pytest.mark.benchmark(group="small_card")
def test_small_card_jinja2(benchmark: Benchmark):
    env = make_environment(TEMPLATES)

    def run_jinja2() -> str:
        return render_template(env, "small_card.html", **SMALL_CARD)

    result = benchmark(run_jinja2)
    assert result == SMALL_CARD_EXPECTED


@pytest.mark.benchmark(group="medium_panel")
def test_medium_panel_compone(benchmark: Benchmark):
    def run_compone() -> str:
        return str(StatsPanel("Build metrics", STATS))

    result = benchmark(run_compone)
    assert result == MEDIUM_PANEL_EXPECTED


@pytest.mark.benchmark(group="medium_panel")
def test_medium_panel_jinja2(benchmark: Benchmark):
    env = make_environment(TEMPLATES)

    def run_jinja2() -> str:
        return render_template(
            env, "medium_panel.html", title="Build metrics", items=STATS
        )

    result = benchmark(run_jinja2)
    assert result == MEDIUM_PANEL_EXPECTED


@pytest.mark.benchmark(group="nested_board")
def test_nested_board_compone(benchmark: Benchmark):
    def run_compone() -> str:
        return str(NestedBoard("Component map", NESTED_GROUPS))

    result = benchmark(run_compone)
    assert result == NESTED_BOARD_EXPECTED


@pytest.mark.benchmark(group="nested_board")
def test_nested_board_jinja2(benchmark: Benchmark):
    env = make_environment(TEMPLATES)

    def run_jinja2() -> str:
        return render_template(
            env,
            "nested_board.html",
            title="Component map",
            groups=NESTED_GROUPS,
        )

    result = benchmark(run_jinja2)
    assert result == NESTED_BOARD_EXPECTED


@pytest.mark.benchmark(group="big_page")
def test_big_page_compone(benchmark: Benchmark):
    def run_compone() -> str:
        return str(BigLandingPage(NAV_ITEMS, FEATURES, PLANS, FAQ_ITEMS))

    result = benchmark(run_compone)
    assert result == BIG_PAGE_EXPECTED


@pytest.mark.benchmark(group="big_page")
def test_big_page_jinja2(benchmark: Benchmark):
    env = make_environment(TEMPLATES)

    def run_jinja2() -> str:
        return render_template(
            env,
            "big_page.html",
            nav_items=NAV_ITEMS,
            features=FEATURES,
            plans=PLANS,
            faq_items=FAQ_ITEMS,
        )

    result = benchmark(run_jinja2)
    assert result == BIG_PAGE_EXPECTED


@pytest.mark.benchmark(group="imported_components")
def test_imported_components_compone(benchmark: Benchmark):
    def run_compone() -> str:
        return str(ImportedComponentPage(NAV_ITEMS, IMPORT_FEATURES))

    result = benchmark(run_compone)
    assert result == IMPORTED_EXPECTED


@pytest.mark.benchmark(group="imported_components")
def test_imported_components_jinja2_imported_macros(benchmark: Benchmark):
    env = make_environment(TEMPLATES)

    def run_jinja2() -> str:
        return render_template(
            env,
            "imported.html",
            nav_items=NAV_ITEMS,
            features=IMPORT_FEATURES,
        )

    result = benchmark(run_jinja2)
    assert result == IMPORTED_EXPECTED
