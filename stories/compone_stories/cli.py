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
    """Specify Story modules as python import paths, e.g. 'my_project.stories'."""
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
@click.option(
    "--workers", "-w", default=4, show_default=True, help="Number of worker processes."
)
@click.pass_obj
def run(modules, host, port, workers):
    """Run Compone Stories web server."""
    from .renderer import Renderer
    from .server import GunicornServer, fork_process
    from .watcher import watch_files
    from .web import create_app

    # TODO: run number of workers from Renderer too
    renderer = Renderer(modules)
    app = create_app(renderer)
    server = GunicornServer(app, host, port, workers)
    wsgi_server = fork_process(server.run)
    file_watcher = watch_files("example_stories/tailwind.py", callback=renderer.restart)

    with (
        renderer,
        wsgi_server as wsgi_process,
        file_watcher,
    ):
        wsgi_process.join()

    # FIXME: exceptions are not handled, click.Abort will be raised on KeyboardInterrupt
