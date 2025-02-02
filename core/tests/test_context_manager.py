from compone import Component, html, safe


def test_nested_html():
    with html.Body() as body:
        body += "carrot"

        with html.Div() as div:
            div += "radish"

            with html.Span() as span:
                span += "hazelnut"

            div += "apple"

        body += "pear"

    body_str = str(body)
    assert isinstance(body_str, safe)
    assert (
        body_str == "<body>carrot<div>radish<span>hazelnut</span>apple</div>pear</body>"
    )


def test_nested_html_escaped():
    with html.Body() as body:
        body += "carrot"
        body += '<script>alert("pwned")</script>'

    body += "pear"

    body_str = str(body)
    assert isinstance(body_str, safe)
    assert (
        body_str == "<body>carrot"
        "&lt;script&gt;alert(&#34;pwned&#34;)&lt;/script&gt;"
        "pear</body>"
    )


def test_nested_same_level_multiple():
    with html.Body() as body:
        body += "carrot"

        with html.Div() as div:
            div += "radish"

        with html.Div() as div2:
            div2 += "hazelnut"

        body += "pear"

    body_str = str(body)
    assert isinstance(body_str, safe)
    assert body_str == "<body>carrot<div>radish</div><div>hazelnut</div>pear</body>"


def test_separate_components():
    @Component
    def Main():
        with html.Div(class_="outer") as div:
            div += html.Div(class_="inner")[Span()]
        return div

    @Component
    def Span():
        with html.Span() as span:
            span += "hazelnut"
        return span

    assert str(Main()) == (
        '<div class="outer"><div class="inner"><span>hazelnut</span></div></div>'
    )
