def is_iterable(value):
    if isinstance(value, str):
        return False
    try:
        iter(value)
    except TypeError:
        return False
    else:
        return True


def snake_to_camel_case(name: str) -> str:
    words = name.split("_")
    return words[0] + "".join(word.capitalize() for word in words[1:])
