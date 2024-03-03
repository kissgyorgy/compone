def _is_iterable(content):
    try:
        iter(content)
    except TypeError:
        return False
    else:
        return True
