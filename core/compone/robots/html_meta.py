from .. import html
from ..component import Component
from ..escape import safe


@Component
def MetaTag(
    *,
    index: bool = False,
    follow: bool = False,
    archive: bool = True,
    snippet: bool = True,
):
    """HTML meta tag for preventing robots to index a specific site.

    noindex: prevents a page from being indexed
    nofollow: prevents links from being crawled
    noarchive: not to store an archived copy of the page
    nosnippet: not include a snippet from the page along with the page's listing in search results

    See:
      - https://www.robotstxt.org/meta.html
      - https://en.wikipedia.org/wiki/Meta_element#The_robots_attribute
    """  # noqa: E501

    directives = []
    for directive, novalue in [
        (index, "noindex"),
        (follow, "nofollow"),
        (archive, "noarchive"),
        (snippet, "nosnippet"),
    ]:
        if not directive:
            directives.append(novalue)

    if not directives:
        return safe("")

    directives_str = ", ".join(directives)
    return html.Meta(name="robots", content=directives_str)
