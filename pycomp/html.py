from .component import Component

Br = "<br>"
Hr = "<hr />"


@Component
def Html(children: str):
    return f"""
        <html>
            {children}
        </html>
    """


@Component
def Head(children: str):
    return f"""
        <head>
            {children}
        </head>
    """


@Component
def Body(children: str):
    return f"""
        <body>
            {children}
        </body>
    """


@Component
def Title(children: str):
    return f"<title>{children}</title>"


@Component
def P(children: str):
    return f"<p>{children}</p>"


@Component
def Ul(children: str):
    return f"""
        <ul>
            {children}
        </ul>
    """


@Component
def Ol(children: str):
    return f"""
        <ol>
            {children}
        </ol>
    """


@Component
def Li(children: str):
    return f"<li>{children}</li>"


@Component
def H1(children: str):
    return f"<h1>{children}</h1>"


@Component
def H2(children: str):
    return f"<h2>{children}</h2>"


@Component
def H3(children: str):
    return f"<h3>{children}</h3>"


@Component
def H4(children: str):
    return f"<h4>{children}</h4>"


@Component
def H5(children: str):
    return f"<h5>{children}</h5>"


@Component
def H6(children: str):
    return f"<h6>{children}</h6>"


@Component
def Div(children: str):
    return f"""
        <div>
            {children}
        </div>
    """
