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
@click.option("--host", default="127.0.0.1", help="Hostname to bind to.")
@click.option("--port", default=5000, help="Port to bind to.")
@click.pass_obj
def run(modules, host, port):
    """Run Compone Stories web server."""
    from .runner import GunicornServer
    from .web import create_app

    app = create_app(modules)
    options = {"bind": f"{host}:{port}"}
    GunicornServer(app, options).run()
