from pathlib import Path

import click

from .config import Config


@click.group()
def ssg():
    """Static Site Generator for Compone Components."""


@ssg.command()
@click.option(
    "--config",
    "-c",
    "config_path",
    default="compone_ssg_config.py",
    type=click.Path(
        exists=True, file_okay=True, dir_okay=False, resolve_path=True, path_type=Path
    ),
    help="Configuration file.",
    show_default=True,
    envvar="COMPONE_SSG_CONFIG",
)
def build(config_path: Path):
    """Build the site from the content directory.

    You can specify the config file with the --config option
    or the COMPONE_SSG_CONFIG environment variable.
    """

    config_globals = {}
    exec(config_path.read_text(), config_globals, config_globals)
    ConfigCls = next(c for c in config_globals.values() if Config._is_subclass(c))
    config: Config = ConfigCls()

    click.echo(f"Content directory: {config._content_dir}")
    click.echo(f"Output directory: {config._output_dir}")
    config._output_dir.mkdir(parents=True, exist_ok=True)

    click.echo("Building site...")
    for route in config.get_content_routes():
        content_meta, content_html = route.parser.parse(route.content_path)
        full_html = route.component(**content_meta)[content_html]

        output_rel = route.output_path.resolve().relative_to(config._output_dir)
        click.echo(f"Creating page: {output_rel}")
        route.output_path.parent.mkdir(parents=True, exist_ok=True)
        route.output_path.write_text(full_html)

    click.echo("Site built successfully! 🎉")
    reldir = config._output_dir.relative_to(Path.cwd())
    click.echo(f"Page content is in ./{reldir} directory.")
