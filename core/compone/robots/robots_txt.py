"""
Generating robots.txt and meta tags for search engine crawlers. See:
- https://www.robotstxt.org/
- https://developers.google.com/search/docs/crawling-indexing/robots/intro
- https://en.wikipedia.org/wiki/Meta_element#The_robots_attribute
"""

import enum
from typing import List, Optional

from ..component import Component


class Bot(enum.Enum):
    All = "*"
    Google = "Googlebot"
    Bing = "Bingbot"
    Yahoo = "Slurp"
    Yandex = "Yandex"
    Baidu = "BaiduSpider"
    # https://duckduckgo.com/duckduckgo-help-pages/results/duckduckbot/
    DuckDuckGo = "DuckDuckBot"
    # https://developer.twitter.com/en/docs/twitter-for-websites/cards/guides/getting-started
    Twitter = "Twitterbot"


@Component
def RobotsTxt(*, children: List["Entry"]):
    return children


@Component
def Entry(
    *,
    user_agent: Bot,
    disallow: List[str],
    allow: List[str] = [],
    crawdelay: Optional[int] = None,
    sitemap: Optional[str] = None,
):
    return [
        UserAgent(agent=user_agent),
        *[Disallow(path=path) for path in disallow],
        *[Allow(path=path) for path in allow],
        CrawDelay(delay=crawdelay) if crawdelay else None,
        Sitemap(url=sitemap) if sitemap else None,
        "\n",
    ]


@Component
def UserAgent(*, agent: Bot):
    return f"User-agent: {agent.value}\n"


@Component
def Disallow(*, path: str):
    return f"Disallow: {path}\n"


@Component
def Allow(*, path: str):
    return f"Allow: {path}\n"


@Component
def CrawDelay(*, delay: int):
    return f"Crawl-delay: {delay}\n"


@Component
def Sitemap(*, url: str):
    return f"Sitemap: {url}\n"
