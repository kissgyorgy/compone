import inspect
from typing import Any, Optional, Type

from compone import safe
from compone.component import _ComponentBase

from .components import StoryPage

REGISTERED_STORIES = {}


class Story:
    component: Type[_ComponentBase]
    template: Type[_ComponentBase] = StoryPage
    title: Optional[str] = None

    @staticmethod
    def register(*stories):
        for story in stories:
            REGISTERED_STORIES[story.get_name()] = story
        # In case when used as decorator
        return stories[0]

    @classmethod
    def get_name(cls) -> str:
        return cls.title or cls.component.__name__

    @classmethod
    def render(cls) -> safe | _ComponentBase:
        # FIXME?: if every component would be lazy by default, we might not need this
        if inspect.isclass(cls.component) and issubclass(cls.component, _ComponentBase):
            content = cls.component()
        else:
            content = cls.component
        return cls.template[content]


def is_story(obj: Any) -> bool:
    return inspect.isclass(obj) and issubclass(obj, Story) and obj is not Story
