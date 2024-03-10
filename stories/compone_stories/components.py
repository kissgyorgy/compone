from compone import Component, html
from flask import url_for


@Component
def StoryNav(*, story_names, active_story):
    nav = html.Div()
    for name in story_names:
        story_url = url_for("story", story_name=name)
        if name == active_story:
            text = html.Strong[name]
        else:
            text = name
        nav += html.P[html.A(href=story_url)[text]]
    return nav


@Component
def StoryFrame(*, children):
    story_html = "".join(children)
    return html.Iframe(srcdoc=story_html)


@Component
def StoryPage(*, children):
    return html.Html[html.Body[children]]


@Component
def StoryProps(*, props):
    return html.Div[
        html.H2["Props"],
        html.Pre["No props"],
    ]


@Component
def AllStoriesPage(*, story_names, active_story, children):
    with html.Html(class_="m-4") as page:
        with html.Meta() as meta:
            css_url = url_for("static", filename="stories.css")
            meta += html.Link(rel="stylesheet", href=css_url)

        page += html.H1(class_="text-center mx-auto pb-4 border-b")["Compone Stories"]

        with html.Div(class_="grid grid-cols-[1fr_3fr] p-4 border-l") as grid:
            grid += StoryNav(story_names=story_names, active_story=active_story)
            with html.Div() as content:
                content += StoryFrame[children]
                content += StoryProps(props=None)

    return page
