import click

from .runner import GunicornServer
from .web import create_app


@click.command()
@click.argument("modules", nargs=-1, required=True)
@click.option("--host", default="127.0.0.1", help="Hostname to bind to")
@click.option("--port", default=5000, help="Port to bind to")
def stories(modules, host, port):
    """Run Compone Stories web server

    Specify Story modules as python import paths, e.g. 'my_project.stories'
    """
    app = create_app(modules)
    options = {"bind": f"{host}:{port}"}
    GunicornServer(app, options).run()
