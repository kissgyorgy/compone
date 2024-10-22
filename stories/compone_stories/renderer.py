import asyncio
import importlib
import multiprocessing as mp
import signal
from concurrent.futures import ProcessPoolExecutor
from operator import itemgetter
from typing import List

from .stories import REGISTERED_STORIES


class _RenderProcess:
    _stories = {}

    @classmethod
    def _init_stories(cls, module_names):
        print("Running initializer")
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        importlib.invalidate_caches()
        # TODO: use venusian for this?
        for name in module_names:
            # Import them for the side effect of Story.register()
            importlib.import_module(name)
        stories = sorted(REGISTERED_STORIES.items(), key=itemgetter(0))
        cls._stories = dict(stories)
        print(f"Imported {len(cls._stories)} stories:", ", ".join(cls._stories.keys()))

    @classmethod
    def story_names(cls):
        return list(cls._stories.keys())

    @classmethod
    def render_story(cls, story_name):
        return cls._stories[story_name].render()


class Renderer:
    """A class to render stories in a separate process to avoid
    re-importing the stories every time a component is rendered
    and possible story side effects breaking the main process.
    """

    TIMEOUT = 3

    def __init__(self, modules: List[str]):
        self._modules = modules
        self._loop = None
        self._command_executor = None

    def restart(self):
        self.stop()
        self.start()

    def start(self):
        self._loop = asyncio.get_running_loop()
        self._command_executor = ProcessPoolExecutor(
            max_workers=4,
            mp_context=mp.get_context("spawn"),
            initializer=_RenderProcess._init_stories,
            initargs=(self._modules,),
        )
        print("Renderer started")

    async def run(self, shutdown_event: asyncio.Event):
        # We can block in start and stop, doesn't really matter
        self.start()
        try:
            await shutdown_event.wait()
        finally:
            self.stop()

    async def _run_command(self, command, *args):
        fut = self._loop.run_in_executor(self._command_executor, command, *args)
        result = await asyncio.wait_for(fut, timeout=self.TIMEOUT)
        return result

    async def render_story(self, story_name: str) -> str:
        return await self._run_command(_RenderProcess.render_story, story_name)

    async def story_names(self) -> List[str]:
        return await self._run_command(_RenderProcess.story_names)

    def stop(self):
        self._command_executor.shutdown(wait=False, cancel_futures=True)
        self._command_executor = None
        print("Renderer stopped")
