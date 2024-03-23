import click


@click.group()
@click.option(
    "-m",
    "--modules",
    help="Python modules to load Story classes from.",
    required=True,
    multiple=True,
    envvar="COMPONE_STORY_MODULES",
)
@click.pass_context
def stories(ctx, modules):
    """Storybook for Compone Components.

    Specify Story modules as python import paths, e.g. 'my_project.stories'.
    """
    ctx.obj = modules


@stories.command(name="list")
@click.pass_obj
def list_stories(modules):
    """List all available stories."""
    import importlib

    from .stories import REGISTERED_STORIES

    for mod in modules:
        importlib.import_module(mod)
    story_titles = REGISTERED_STORIES.keys()
    click.echo("- " + "\n- ".join(story_titles))


@stories.command()
@click.option(
    "--host", "-h", default="127.0.0.1", show_default=True, help="Hostname to bind to."
)
@click.option("--port", "-p", default=5000, show_default=True, help="Port to bind to.")
@click.pass_obj
def run(modules, host: str, port: int):
    """Run Compone Stories web server."""
    import asyncio
    import signal

    from hypercorn.asyncio import serve
    from hypercorn.config import Config
    from watchfiles import awatch

    from .renderer import Renderer
    from .web import create_app

    config = Config()
    config.bind = [f"{host}:{port}"]

    loop = asyncio.new_event_loop()
    shutdown_event = asyncio.Event()
    for signal_name in {"SIGINT", "SIGTERM", "SIGQUIT"}:
        loop.add_signal_handler(getattr(signal, signal_name), shutdown_event.set)

    renderer = Renderer(modules)
    app = create_app(renderer)

    async def watch_files(shutdown_event):
        async for changes in awatch("example_stories/", stop_event=shutdown_event):
            renderer.restart()

    loop.create_task(renderer.run(shutdown_event))
    loop.create_task(watch_files(shutdown_event))
    loop.run_until_complete(serve(app, config, shutdown_trigger=shutdown_event.wait))
