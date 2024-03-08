from flask import Flask, redirect, url_for

from .components import Page
from .renderer import Renderer


def create_app(modules: list[str]):
    app = Flask("compone_stories")
    renderer = Renderer(modules)

    @app.route("/")
    def index():
        first_story_name = renderer.story_names()[0]
        return redirect(url_for("story", story_name=first_story_name))

    @app.route("/story/<story_name>")
    def story(story_name):
        story_names = renderer.story_names()
        story_content = renderer.render_story(story_name)
        return str(
            Page(
                story_names=story_names,
                story_content=story_content,
                active_story=story_name,
            )
        )

    renderer.start()

    return app
