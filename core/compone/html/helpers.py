from typing import Iterable

from ..utils import is_iterable


def _parse_class_arg(
    arg: str | Iterable[str | None] | dict[str, bool],
) -> Iterable[str]:
    if not arg:
        return tuple()
    elif isinstance(arg, str):
        return arg.split()
    elif isinstance(arg, dict):
        return (class_ for class_, enabled in arg.items() if enabled)
    elif is_iterable(arg):
        return (class_ for elem in arg if elem for class_ in elem.split())
    else:
        raise TypeError(f"Invalid class type: {type(arg)} for {arg!r}")


def classes(*args: str | Iterable[str] | dict[str, bool]) -> list[str]:
    """Convert different types of HTML class arguments to a list of classes.
    str --> list of classes
    list of str --> list of classes
    dict[str, bool] --> list of enabled classes
    """

    if not args:
        return

    pieces = dict()
    for arg in args:
        class_str_list = _parse_class_arg(arg)
        stripped_classes = (
            stripped for class_ in class_str_list if (stripped := class_.strip())
        )
        for class_ in stripped_classes:
            pieces[class_] = True

    return list(pieces.keys())
