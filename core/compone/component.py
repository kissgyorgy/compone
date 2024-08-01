import copy
import inspect
from contextvars import ContextVar
from functools import cached_property
from types import MappingProxyType
from typing import Callable, Iterable, List, Optional, Protocol, Type, TypeVar, Union

from .escape import escape, safe
from .utils import is_iterable

# previous frame id (frame.f_back), parent object
last_parent = ContextVar("last_parent", default=(None, None))

CompSelf = TypeVar("CompSelf", bound="_ComponentBase")
ChildSelf = TypeVar("ChildSelf", bound="_ChildrenBase")


class ComponentClass(Protocol):
    def render(self, children: safe) -> Union[CompSelf, Iterable[CompSelf]]: ...


class _ComponentBase:
    _sig: inspect.Signature
    _positional_args: List[str]
    _var_keyword: Optional[str]

    def __init__(self, *args, **kwargs):
        self._bound_args = self._bind_args(*args, **kwargs)

    def _bind_args(self, *args, **kwargs):
        bound = self._sig.bind(*args, **kwargs)
        bound.apply_defaults()
        return bound

    @cached_property
    def props(self) -> dict:
        kwargs = {k: v for k, v in self._bound_args.kwargs.items() if v is not None}
        args = {
            k: v
            for k, v in self._bound_args.arguments.items()
            if k not in kwargs and v is not None
        }
        if self._var_keyword is not None:
            del args[self._var_keyword]
        return MappingProxyType({**args, **kwargs})

    def replace(self, **kwargs) -> CompSelf:
        self._check_common_props(kwargs)
        return self._make_new(kwargs)

    def append(self, **kwargs) -> CompSelf:
        self._check_common_props(kwargs)
        appended = {key: (self.props[key] + val) for key, val in kwargs.items()}
        return self._make_new(appended)

    def _check_common_props(self, kwargs):
        if not set(kwargs) & set(self.props):
            kwargs_list = ", ".join(repr(k) for k in kwargs.keys())
            raise TypeError(f"{self!r} has no existing props for {kwargs_list}")

    def __call__(self, *args, **kwargs) -> CompSelf:
        # Replaces existing props, set new ones
        args_only = {name: newval for name, newval in zip(self._positional_args, args)}
        return self._make_new({**args_only, **kwargs})

    def _make_new(self, new_arguments) -> CompSelf:
        arguments_copy = {
            k: copy.copy(v) for k, v in self._bound_args.arguments.items()
        }
        bound_copy = inspect.BoundArguments(self._sig, arguments_copy)

        if self._var_keyword is None:
            bound_copy.arguments.update(new_arguments)
        else:
            old_star_arguments = bound_copy.arguments[self._var_keyword]
            new_star_arguments = {
                k: v for k, v in new_arguments.items() if k in old_star_arguments
            }
            old_star_arguments.update(new_star_arguments)

            other_arguments = {
                k: v for k, v in new_arguments.items() if k not in new_star_arguments
            }
            bound_copy.arguments.update(other_arguments)

        # This is to add new kwargs that was not specified before
        # It will raise TypeError for args not in self._sig
        extra_kwargs = {
            k: v
            for k, v in new_arguments.items()
            if k not in bound_copy.kwargs and k not in self._positional_args
        }
        new_kwargs = {**bound_copy.kwargs, **extra_kwargs}
        new_bound = self._bind_args(*bound_copy.args, **new_kwargs)
        return self.__class__(*new_bound.args, **new_bound.kwargs)

    def __repr__(self):
        if self.props:
            proplist = ", ".join(f"{k}={v!r}" for k, v in self.props.items())
        else:
            proplist = ""
        return f"<{self.__class__.__name__}({proplist})>"

    def __mul__(self, other: int) -> CompSelf:
        if not isinstance(other, int):
            return NotImplemented

        # Every component is safe by default, so the result should be safe too
        Multiple = Component(lambda: safe(self) * other)
        Multiple.__name__ = "Multi" + self.__class__.__name__
        Multiple.__doc__ = "Multiple: " + (self.__doc__ or "")
        return Multiple()


class _ChildrenBase(_ComponentBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._children = []

    def __enter__(self) -> ChildSelf:
        parent_frame_id, parent = last_parent.get()
        self._parent_frame_id = parent_frame_id
        self._parent = parent
        current_frame_id = id(inspect.currentframe().f_back)
        last_parent.set((current_frame_id, self))
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        current_frame_id = id(inspect.currentframe().f_back)
        if self._parent is not None and current_frame_id == self._parent_frame_id:
            self._parent._children.append(self)
        last_parent.set((self._parent_frame_id, self._parent))

    def __iadd__(self, other) -> ChildSelf:
        self._children.append(other)
        return self

    def __class_getitem__(cls, key) -> ChildSelf:
        return cls()[key]

    def __getitem__(self, children) -> safe:
        if self._children:
            # Not AttributeError because it would be confusing,
            # for example when using hasattr.
            # Also this is like a function call, so ValueError makes sense
            raise ValueError(
                "Component already has children, "
                "use the += operator if you want to add more."
            )

        # _ChildrenBase are also iterators because of this very method
        if not is_iterable(children) or isinstance(children, _ChildrenBase):
            children = (children,)

        new = self.__class__(*self._bound_args.args, **self._bound_args.kwargs)
        new._children = children
        return new

    @property
    def children(self):
        return tuple(self._children)

    def __call__(self, *args, **kwargs) -> CompSelf:
        if self._children:
            raise ValueError("Component already has children, cannot replace them.")
        return super().__call__(*args, **kwargs)

    def __eq__(self, other):
        if not isinstance(other, _ChildrenBase):
            return NotImplemented
        # This is the safest way to do this, because user-implemented,
        # class-based Components can have different properties, which
        # might render them differently. We can't compare those without rendering.
        return str(self) == str(other)

    def __str__(self) -> safe:
        safe_children = self._escape(self._children) if self._children else safe()
        content = self._render(safe_children)
        return self._escape(content)

    @classmethod
    def _escape(cls, item) -> safe:
        if isinstance(item, _ComponentBase):
            return escape(item)
        elif is_iterable(item):
            return safe("".join(cls._escape(e) for e in item))
        else:
            return escape(item)


class _FuncComponent(_ChildrenBase):
    _func: Callable
    _pass_children: bool

    def _render(self, children: safe) -> Union[CompSelf, Iterable[CompSelf]]:
        # BoundArguments.kwargs is a property, this makes a copy
        kwargs = self._bound_args.kwargs

        if self._pass_children:
            kwargs["children"] = children

        # self.func is unbound
        content = self.__class__._func(*self._bound_args.args, **kwargs)
        return content


class _ClassComponent(_ChildrenBase):
    _pass_children: bool
    _user_class: ComponentClass

    @cached_property
    def _user_instance(self) -> ComponentClass:
        return self._user_class(*self._bound_args.args, **self._bound_args.kwargs)

    def _render(self, children: safe):
        if self._pass_children:
            return self._user_instance.render(children)
        else:
            return self._user_instance.render()


def Component(
    func_or_class: Union[ComponentClass, Callable],
) -> Union[Type[_ClassComponent], Type[_FuncComponent]]:
    if inspect.isfunction(func_or_class):
        return _make_func_component(func_or_class)
    elif inspect.isclass(func_or_class):
        return _make_class_component(func_or_class)
    else:
        raise TypeError("Components can only be classes or functions")


def _make_sig(func):
    sig = inspect.signature(func)
    # This is only for caching in the class
    positional_args = [
        name
        for name, param in sig.parameters.items()
        if param.kind in {param.POSITIONAL_ONLY, param.POSITIONAL_OR_KEYWORD}
    ]
    return sig, positional_args


def _get_var_keyword(sig) -> Optional[str]:
    try:
        return next(p.name for p in sig.parameters.values() if p.kind == p.VAR_KEYWORD)
    except StopIteration:
        return None


def _make_class_component(user_class: ComponentClass) -> Type[_ClassComponent]:
    if not hasattr(user_class, "render"):
        raise TypeError(f"{user_class.__name__} doesn't have a .render() method.")

    orig_sig, positional_args = _make_sig(user_class.__init__)
    without_passed = [
        param
        for key, param in orig_sig.parameters.items()
        if key not in {"self", "children"}
    ]
    sig = inspect.Signature(parameters=without_passed)
    render_sig = inspect.signature(user_class.render)

    return type(
        user_class.__name__,
        (_ClassComponent,),
        dict(
            _user_class=user_class,
            _sig=sig,
            _positional_args=positional_args,
            _var_keyword=_get_var_keyword(sig),
            _pass_children="children" in render_sig.parameters,
            __module__=user_class.__module__,
        ),
    )


def _make_func_component(func: Callable) -> Type[_FuncComponent]:
    orig_sig, positional_args = _make_sig(func)
    without_children = [
        param for key, param in orig_sig.parameters.items() if key != "children"
    ]
    sig = inspect.Signature(parameters=without_children)

    return type(
        func.__name__,
        (_FuncComponent,),
        dict(
            _func=func,
            _sig=sig,
            _positional_args=positional_args,
            _var_keyword=_get_var_keyword(orig_sig),
            _pass_children="children" in orig_sig.parameters,
            __module__=func.__module__,
        ),
    )
