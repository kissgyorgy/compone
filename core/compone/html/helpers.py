from typing import Dict, Iterable, List, Optional, Union

from ..utils import is_iterable

ClassTypes = Union[str, Iterable[Optional[str]], Dict[str, bool]]


def _make_class_list(arg: ClassTypes) -> Iterable[str]:
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


def classes(*args: ClassTypes) -> List[str]:
    """Convert different types of HTML class arguments to a list of classes.
    str --> list of classes
    list of str --> list of classes
    dict[str, bool] --> list of enabled classes
    """
    pieces = [
        stripped
        for arg in args
        for class_ in _make_class_list(arg)
        if (stripped := class_.strip())
    ]
    return list(dict.fromkeys(pieces))
