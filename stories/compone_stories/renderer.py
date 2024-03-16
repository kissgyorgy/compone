import asyncio
import importlib
import multiprocessing as mp
from concurrent.futures import ThreadPoolExecutor
from multiprocessing.context import SpawnProcess
from operator import itemgetter

from .stories import REGISTERED_STORIES, Story


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
            except (EOFError, KeyboardInterrupt):
                break

            cmd, *args = msg
            if res := self._run_command(cmd, *args):
                self._conn.send(res)

        print("_RenderProcess stopped.")

    def _init_stories(self) -> dict[str, Story]:
        importlib.invalidate_caches()
        # TODO: use venusian for this?
        for name in self._module_names:
            # Import them for the side effect of Story.register()
            importlib.import_module(name)
        stories = sorted(REGISTERED_STORIES.items(), key=itemgetter(0))
        self._stories = dict(stories)
        print("Imported stories:", self._stories.keys())

    def _run_command(self, cmd, *args):
        if cmd == _Command.RENDER:
            story_name = args[0]
            content = self._stories[story_name].render()
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
        self._command_executor = None

    def restart(self):
        # It's even required to block, because no other command should run until restarted
        # Don't close the pipe, it will be used for the new process
        self._parent_conn.send([_Command.STOP])
        self._process.join()
        self._process.close()
        self._process = _RenderProcess(self._modules, self._child_conn)
        self._process.start()

    def start(self):
        self._command_executor = ThreadPoolExecutor()
        self._parent_conn, self._child_conn = mp.Pipe()
        self._process = _RenderProcess(self._modules, self._child_conn)
        self._process.start()
        print("Renderer started")

    async def run(self, shutdown_event: asyncio.Event):
        # We can block in start and stop, doesn't really matter
        self.start()
        try:
            await shutdown_event.wait()
        finally:
            self.stop()

    async def _run_command(self, command, *args):
        loop = asyncio.get_running_loop()

        def run_command():
            self._parent_conn.send([command, *args])
            return self._parent_conn.recv()

        result = await loop.run_in_executor(self._command_executor, run_command)
        return result

    async def render_story(self, story_name: str) -> str:
        return await self._run_command(_Command.RENDER, story_name)

    async def story_names(self) -> list[str]:
        return await self._run_command(_Command.STORY_NAMES)

    def stop(self):
        # Must not recv(), otherwise it will hang
        self._parent_conn.send([_Command.STOP])
        self._parent_conn.close()
        self._command_executor.shutdown(wait=False, cancel_futures=True)

        self._process.join()
        self._process.close()

        self._parent_conn, self._child_conn = None, None
        self._process = None
        self._command_executor = None
        print("Renderer stopped")
