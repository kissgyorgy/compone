import textwrap

import pytest
from compone import robots as r


@pytest.mark.parametrize(
    "entry, expected",
    [
        (
            r.Entry(user_agent=r.Bot.All, disallow=["*"]),
            "User-agent: *\nDisallow: *\n\n",
        ),
        (
            r.Entry(user_agent=r.Bot.All, disallow=["/admin/"]),
            "User-agent: *\nDisallow: /admin/\n\n",
        ),
        (
            r.Entry(user_agent=r.Bot.Google, disallow=["*"]),
            "User-agent: Googlebot\nDisallow: *\n\n",
        ),
    ],
)
def test_robots_txt_entry(entry, expected):
    assert str(entry) == expected


def test_robots_txt():
    robots_txt = r.RobotsTxt[
        r.Entry(user_agent=r.Bot.All, disallow=["*"]),
        r.Entry(user_agent=r.Bot.Google, disallow=["/admin/"]),
    ]
    expected = textwrap.dedent(
        "User-agent: *\nDisallow: *\n\nUser-agent: Googlebot\nDisallow: /admin/\n\n"
    )
    assert str(robots_txt) == expected


@pytest.mark.parametrize(
    "tag, expected",
    [
        (
            r.MetaTag(index=True, follow=True),
            "",
        ),
        (
            r.MetaTag(index=False, follow=True),
            '<meta name="robots" content="noindex" />',
        ),
        (
            r.MetaTag(index=True, follow=False),
            '<meta name="robots" content="nofollow" />',
        ),
        (
            r.MetaTag(index=False, follow=False),
            '<meta name="robots" content="noindex, nofollow" />',
        ),
        (
            r.MetaTag(index=True, follow=True, archive=False, snippet=True),
            '<meta name="robots" content="noarchive" />',
        ),
        (
            r.MetaTag(index=True, follow=True, archive=True, snippet=False),
            '<meta name="robots" content="nosnippet" />',
        ),
    ],
)
def test_meta_tag(tag, expected):
    assert str(tag) == expected
