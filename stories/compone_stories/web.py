from starlette.applications import Starlette
from starlette.responses import RedirectResponse, Response
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles

from .components import AllStoriesPage
from .renderer import Renderer


def create_app(renderer: Renderer):
    async def index(request):
        story_names = await renderer.story_names()
        return RedirectResponse(request.url_for("story", story_name=story_names[0]))

    async def story(request):
        story_name = request.path_params["story_name"]
        story_names = await renderer.story_names()
        story_urls = [
            request.url_for("story", story_name=story_name)
            for story_name in story_names
        ]
        stories = zip(story_names, story_urls)
        story_content = await renderer.render_story(story_name)
        css_url = request.url_for("static", path="stories.css")
        page = AllStoriesPage(
            css_url=css_url,
            stories=stories,
            active_story=story_name,
        )[story_content,]
        return Response(str(page))

    # This uses /{path} as path_param
    static_app = StaticFiles(packages=[("compone_stories", "static")])
    routes = [
        Route("/", index),
        Route("/story/{story_name}", story),
        Mount("/static", app=static_app, name="static"),
    ]
    app = Starlette(debug=True, routes=routes)
    return app
