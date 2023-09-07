from compone import html

with html.Body() as body:
    body += "répa"

    with html.Div() as div:
        div += "retek"

        with html.Span() as span:
            span += "mogyoró"

        div += "alma"

    body += "körte"

print(body)
# <body>répa<div>retek<span>mogyoró</span>alma</div>körte</body>
