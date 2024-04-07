from typing import List

from .component import _ChildrenBase, _HTMLComponentBase, safe

Xml10 = safe('<?xml version="1.0" encoding="UTF-8"?>')
Xml11 = safe('<?xml version="1.1" encoding="UTF-8"?>')


class Comment(_ChildrenBase, _HTMLComponentBase):
    def _escape(self, item) -> List[safe]:
        # Anything inside comments should not be escaped
        return safe(item)

    def _render(self, children: safe) -> safe:
        return safe(f"<-- {children} -->")
