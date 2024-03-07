import importlib
import inspect
import multiprocessing as mp
from multiprocessing.connection import Connection
from pathlib import Path

from .stories import Story, is_story


def init_stories(module_names: list[str]) -> dict[str, Story]:
    print("Got modules", module_names)
    importlib.invalidate_caches()
    module_names = [importlib.import_module(path) for path in module_names]
    all_stories = {}
    for mod in module_names:
        story_objects = inspect.getmembers(mod, predicate=is_story)
        storymap = {story.get_name(): story for _, story in story_objects}
        all_stories.update(storymap)
    print("Imported stories:", all_stories.keys())
    return all_stories


class Command:
    RENDER = "render"
    STORY_NAMES = "story_names"
    STOP = "stop"


def start_process(modules: list[Path], conn: Connection):
    stories = init_stories(modules)

    while True:
        msg = conn.recv()
        print("Got message", msg)
        cmd, *args = msg

        if cmd == Command.RENDER:
            story_name = args[0]
            comp_obj = stories[story_name].component()
            content = str(comp_obj)
            conn.send(content)
        elif cmd == Command.STORY_NAMES:
            story_names = list(stories.keys())
            conn.send(story_names)
        elif cmd == Command.STOP:
            conn.close()
            break
        else:
            raise ValueError(f"Unknown message: {msg}")

    print("Renderer stopped.")


class Renderer:
    """A class to render stories in a separate process to avoid
    re-importing the stories every time a component is rendered
    and possible story side effects breaking the main process.
    """

    def __init__(self, modules: list[str]):
        self._modules = modules
        self._parent_conn, self._child_conn = None, None
        self._process = None

    def start(self):
        ctx = mp.get_context("spawn")
        self._parent_conn, self._child_conn = ctx.Pipe()
        self._process = ctx.Process(
            target=start_process, args=(self._modules, self._child_conn)
        )
        self._process.daemon = True
        self._process.start()

    def _run_command(self, command, *args):
        self._parent_conn.send([command, *args])
        return self._parent_conn.recv()

    def stop(self):
        # Must not recv(), otherwise it will hang
        self._parent_conn.send([Command.STOP])
        self._parent_conn.close()
        self._process.join()
        self._process.close()

    def render_story(self, story_name: str) -> str:
        return self._run_command(Command.RENDER, story_name)

    def story_names(self) -> list[str]:
        return self._run_command(Command.STORY_NAMES)
