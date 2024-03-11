import contextlib
from pathlib import Path

from watchdog import events
from watchdog.observers import Observer

_ignore_common_dirs = {
    "__pycache__",
    ".git",
    ".hg",
    ".tox",
    ".nox",
    ".pytest_cache",
    ".mypy_cache",
}


class FileChangedEventHandler(events.PatternMatchingEventHandler):
    def __init__(self, restart_callback, extra_paths=None):
        self._restart_callback = restart_callback

        if extra_paths is None:
            extra_patterns = []
        else:
            extra_patterns = [p for p in extra_paths if not Path(p).is_dir()]
        super().__init__(
            patterns=["*.py", *extra_patterns],
            ignore_patterns=[f"*/{d}/*" for d in _ignore_common_dirs],
        )

    def on_any_event(self, event):
        if event.event_type in (events.EVENT_TYPE_CREATED, events.EVENT_TYPE_MODIFIED):
            print(f"Story file changed: {event.src_path} , restarting")
            self._restart_callback()


@contextlib.contextmanager
def watch_files(path, callback):
    obs = Observer()
    event_handler = FileChangedEventHandler(callback)
    obs.schedule(event_handler, path, recursive=True)
    obs.start()
    yield obs
    obs.stop()
    obs.join()
    print("FileWatcher stopped")
