import inspect
from contextvars import ContextVar

state_context_vars = {}


def use_state(default):
    global state_context_vars
    outer_frames = inspect.getouterframes(inspect.currentframe())
    parent_frame = outer_frames[1].frame
    varname = f"{parent_frame.f_code}-{parent_frame.f_lasti}"
    var = state_context_vars.setdefault(varname, ContextVar(varname, default=default))
    return var.get, var.set
