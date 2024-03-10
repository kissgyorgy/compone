import inspect
from typing import Any, Optional, Type

from compone import safe
from compone.component import _ComponentBase

from .args import Arg
REGISTERED_STORIES = {}


class Story:
    component: Type[_ComponentBase]
    name: Optional[str] = None
    children: Any = None
    args: list[Arg] = []

    @staticmethod
    def register(*stories):
        for story in stories:
            REGISTERED_STORIES[story.get_name()] = story
        # In case when used as decorator
        return stories[0]

    @classmethod
    def get_name(cls) -> str:
        return cls.name or cls.component.__name__

    @classmethod
    def render(cls) -> safe | _ComponentBase:
        content = cls.component()
        if cls.children:
            content = content[cls.children]
        return content


def is_story(obj: Any) -> bool:
    return inspect.isclass(obj) and issubclass(obj, Story) and obj is not Story
