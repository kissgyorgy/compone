from .html.component import _ChildrenBase, _HTMLComponentBase, safe

Xml10 = safe('<?xml version="1.0" encoding="UTF-8"?>')
Xml11 = safe('<?xml version="1.1" encoding="UTF-8"?>')


class Comment(_ChildrenBase, _HTMLComponentBase):
    def __str__(self) -> str:
        # Anything inside comments should not be escaped
        children = "".join(str(e) for e in self._children)
        return safe(f"<-- {children} -->")
