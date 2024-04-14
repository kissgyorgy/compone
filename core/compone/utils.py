def is_iterable(value):
    if isinstance(value, str):
        return False
    try:
        iter(value)
    except TypeError:
        return False
    else:
        return True
