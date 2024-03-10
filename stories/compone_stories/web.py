from compone.component import _ComponentBase
from flask import Flask, Response, redirect, url_for
from flask import typing as ft

from .components import AllStoriesPage
from .renderer import Renderer


class ComponentApp(Flask):
    def make_response(self, rv: ft.ResponseReturnValue) -> Response:
        if isinstance(rv, _ComponentBase):
            return self.response_class(str(rv))
        else:
            return super().make_response(rv)


def create_app(modules: list[str]):
    app = ComponentApp("compone_stories")
    renderer = Renderer(modules)

    @app.route("/")
    def index():
        first_story_name = renderer.story_names()[0]
        return redirect(url_for("story", story_name=first_story_name))

    @app.route("/story/<story_name>")
    def story(story_name):
        story_names = renderer.story_names()
        story_content = renderer.render_story(story_name)
        return AllStoriesPage(
            story_names=story_names,
            active_story=story_name,
        )[story_content,]

    renderer.start()

    return app
