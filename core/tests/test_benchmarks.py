from functools import lru_cache

import pytest
from compone import Component, html
from jinja2 import DictLoader, Environment, select_autoescape


@pytest.mark.benchmark(group="micro")
def test_micro_compone(benchmark):
    @Component
    def Comp(a, b):
        return html.Div(a=a, b=b)

    def run_compone():
        comp = Comp(3, 4)
        return str(comp)

    result = benchmark(run_compone)
    assert result == """<div a="3" b="4"></div>"""


@pytest.mark.benchmark(group="micro")
def test_micro_compone_cached(benchmark):
    @Component
    @lru_cache
    def Comp(a, b):
        return html.Div(a=a, b=b)

    def run_compone():
        comp = Comp(3, 4)
        return str(comp)

    result = benchmark(run_compone)
    assert result == """<div a="3" b="4"></div>"""


@pytest.mark.benchmark(group="micro")
def test_micro_jinja2(benchmark):
    env = Environment(
        loader=DictLoader({"benchmark": '<div a="{{ a }}" b="{{ b }}"></div>'}),
        autoescape=select_autoescape(),
    )

    def run_jinja2():
        template = env.get_template("benchmark")
        return template.render(a=3, b=4)

    result = benchmark(run_jinja2)
    assert result == """<div a="3" b="4"></div>"""


@pytest.mark.benchmark(group="single_child")
def test_micro_compone_single_child(benchmark):
    @Component
    def Comp(a, b, children):
        return html.Div(a=a, b=b)[children]

    def run_compone():
        comp = Comp(3, 4)["simple children"]
        return str(comp)

    result = benchmark(run_compone)
    assert result == """<div a="3" b="4">simple children</div>"""


@pytest.mark.benchmark(group="single_child")
def test_micro_jinja2_single_child(benchmark):
    env = Environment(
        loader=DictLoader(
            {"benchmark": '<div a="{{ a }}" b="{{ b }}">{{children}}</div>'}
        ),
        autoescape=select_autoescape(),
    )

    def run_jinja2():
        template = env.get_template("benchmark")
        return template.render(a=3, b=4, children="simple children")

    result = benchmark(run_jinja2)
    assert result == """<div a="3" b="4">simple children</div>"""
