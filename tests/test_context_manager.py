from compone import html, safe


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
        body_str
        == "<body>carrot&lt;script&gt;alert(&quot;pwned&quot;)&lt;/script&gt;pear</body>"
    )
