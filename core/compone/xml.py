from .component import _ChildrenBase
from .elements import _Tag
from .escape import safe

XML_10 = safe('<?xml version="1.0" encoding="UTF-8"?>')
XML_11 = safe('<?xml version="1.1" encoding="UTF-8"?>')


class Comment(_ChildrenBase, _Tag):
    def __str__(self) -> safe:
        # Anything inside comments should not be escaped
        children = "".join(str(e) for e in self._children)
        return safe(f"<-- {children} -->")
