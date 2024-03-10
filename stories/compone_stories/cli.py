import click

from .web import create_app


@click.command()
@click.argument("modules", nargs=-1, required=True)
def stories(modules):
    """Run Compone Stories web server

    Specify Story modules as python import paths, e.g. 'my_project.stories'
    """
    app = create_app(modules)
    app.run()
