import json
from collections.abc import Mapping
from typing import Literal, Optional, Union

from ..escape import escape
from .enums import Event, Swap


class Hx(Mapping):
    def __init__(self):
        self._attrs = {}

    def get(self, url: str):
        self._attrs["hx-get"] = url
        return self

    def post(self, url: str):
        self._attrs["hx-post"] = url
        return self

    def on(self, event: Union[str, Event], js: str):
        self._attrs[f"hx-on:{event.value}"] = js
        return self

    def push_url(self, value: Union[bool, str]):
        value = strbool(value) if isinstance(value, bool) else value
        self._attrs["hx-push-url"] = value
        return self

    def select(self, selector: str):
        self._attrs["hx-select"] = selector
        return self

    def select_oob(self, *selectors: str):
        """The hx-select-oob attribute allows you to select content from a response
        to be swapped in via an out-of-band swap.
        """
        self._attrs["hx-select-oob"] = ",".join(selectors)
        return self

    def swap(self, strategy: Swap, modifier: Optional[str] = None):
        modifier = f" {modifier}" if modifier else ""
        self._attrs["hx-swap"] = f"{strategy.value}{modifier}"
        return self

    def swap_oob(
        self, strategy: Union[Literal[True], Swap], selector: Optional[str] = None
    ):
        value = "true" if strategy is True else strategy.value
        selector = f":{selector}" if selector else ""
        self._attrs["hx-swap-oob"] = f"{value}{selector}"
        return self

    def target(
        self, value: Union[Literal["this"], Literal["next"], Literal["previous"], str]
    ):
        """The hx-target attribute allows you to target a different element for swapping
        than the one issuing the AJAX request.
        """
        self._attrs["hx-target"] = value
        return self

    def trigger(self, event: Event):
        self._attrs["hx-trigger"] = event.value
        return self

    def vals(self, values: dict):
        self._attrs["hx-vals"] = json.dumps(values)
        return self

    def js_vals(self, js_object_str: str):
        self._attrs["hx-vals"] = f"js:{js_object_str}"
        return self

    def __call__(self):
        new = self.__class_()
        new._attrs = self._attrs.copy()
        return new

    def __getitem__(self, key):
        # usually should not contain user input, but better be safe than sorry
        return escape(self._attrs[key])

    def __iter__(self):
        return iter(self._attrs)

    def __len__(self):
        return len(self._attrs)


def strbool(value: bool) -> str:
    return "true" if value else "false"


class SwapModifier:
    @staticmethod
    def transition(value: bool = True):
        return f"transition:{strbool(value)}"

    @staticmethod
    def swap(time: str):
        return f"swap:{time}"

    @staticmethod
    def settle(time: str):
        return f"settle:{time}"

    @staticmethod
    def ignore_title(value: bool = True):
        return f"ignoreTitle:{strbool(value)}"

    @classmethod
    def scroll(
        cls,
        where: Union[Literal["top"], Literal["bottom"]],
        selector: Optional[str] = None,
    ):
        return cls._make_scroll_value("scroll", where, selector)

    @classmethod
    def show(
        cls,
        where: Union[Literal["top"], Literal["bottom"]],
        selector: Optional[str] = None,
    ):
        return cls._make_scroll_value("show", where, selector)

    @staticmethod
    def _make_scroll_value(action: str, where: str, selector: Optional[str]):
        if selector is not None:
            return f"{action}:{selector}:{where}"
        else:
            return f"{action}:{where}"

    @staticmethod
    def focus_scroll(value: bool = True):
        return f"focus-scroll:{strbool(value)}"


class Target:
    @staticmethod
    def this():
        return "this"

    @staticmethod
    def next(selector: Optional[str] = None):
        selector = f" {selector}" if selector else ""
        return f"next{selector}"

    @staticmethod
    def previous(selector: Optional[str] = None):
        selector = f" {selector}" if selector else ""
        return f"previous{selector}"

    @staticmethod
    def closest(selector: str):
        return f"closest {selector}"

    @staticmethod
    def find(selector: str):
        return f"find {selector}"
