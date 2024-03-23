import click


@click.group()
@click.pass_context
def ssg(ctx):
    """Static Site Generator for Compone Stories."""
