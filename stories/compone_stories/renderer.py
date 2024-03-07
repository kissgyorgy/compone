import importlib
import inspect
import multiprocessing as mp
from multiprocessing.context import SpawnProcess

from .stories import Story, is_story


class _Command:
    RENDER = "render"
    STORY_NAMES = "story_names"
    STOP = "stop"


class _RenderProcess(SpawnProcess):
    daemon = True

    def __init__(self, modules, conn):
        super().__init__()
        self._stories = []
        self._module_names = modules
        self._conn = conn
        self._running = False

    def start(self):
        self._running = True
        super().start()

    def run(self):
        self._init_stories()

        while self._running:
            try:
                msg = self._conn.recv()
                print("Got message", msg)
            # can happen when the parent process exits
            # and the process is shut down
            except EOFError:
                break

            cmd, *args = msg
            if res := self._run_command(cmd, *args):
                self._conn.send(res)

        print("_RenderProcess stopped.")

    def _init_stories(self) -> dict[str, Story]:
        print("Got modules", self._module_names)
        importlib.invalidate_caches()
        modules = [importlib.import_module(name) for name in self._module_names]

        all_stories = {}
        for mod in modules:
            story_objects = inspect.getmembers(mod, predicate=is_story)
            storymap = {story.get_name(): story for _, story in story_objects}
            all_stories.update(storymap)

        print("Imported stories:", all_stories.keys())
        self._stories = all_stories

    def _run_command(self, cmd, *args):
        if cmd == _Command.RENDER:
            story_name = args[0]
            comp_obj = self._stories[story_name].component()
            content = str(comp_obj)
            return content
        elif cmd == _Command.STORY_NAMES:
            story_names = list(self._stories.keys())
            return story_names
        elif cmd == _Command.STOP:
            self._conn.close()
            self._running = False
        else:
            raise ValueError(f"Unknown command: {cmd}")


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
        self._parent_conn, self._child_conn = mp.Pipe()
        self._process = _RenderProcess(self._modules, self._child_conn)
        self._process.start()

    def _run_command(self, command, *args):
        self._parent_conn.send([command, *args])
        return self._parent_conn.recv()

    def render_story(self, story_name: str) -> str:
        return self._run_command(_Command.RENDER, story_name)

    def story_names(self) -> list[str]:
        return self._run_command(_Command.STORY_NAMES)

    def stop(self):
        # Must not recv(), otherwise it will hang
        self._parent_conn.send([_Command.STOP])
        self._parent_conn.close()

        self._process.join()
        self._process.close()

        self._parent_conn, self._child_conn = None, None
        self._process = None
