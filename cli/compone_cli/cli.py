import importlib
from importlib.metadata import entry_points

import click

from .convert import convert


def get_entry_points(name: str | None = None):
    eps = entry_points(group="compone.cli")
    return eps[name] if name else eps


class ComponeCommands(click.MultiCommand):
    def list_commands(self, ctx):
        return [c.name for c in get_entry_points()] + [convert.name]

    def get_command(self, ctx, name):
        if name == convert.name:
            return convert
        try:
            ep = get_entry_points(name)
        except KeyError:
            return None
        module_name, command = ep.value.rsplit(":")
        mod = importlib.import_module(module_name)
        return getattr(mod, command)


main = ComponeCommands()
