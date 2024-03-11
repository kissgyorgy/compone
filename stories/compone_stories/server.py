import contextlib
import multiprocessing as mp

import gunicorn.app.base


class GunicornServer(gunicorn.app.base.BaseApplication):
    def __init__(self, app, host, port, workers):
        self._app = app
        self._options = dict(bind=f"{host}:{port}", workers=workers)
        super().__init__()

    def load_config(self):
        config = {
            key: value
            for key, value in self._options.items()
            if key in self.cfg.settings and value is not None
        }
        for key, value in config.items():
            self.cfg.set(key.lower(), value)

    def load(self):
        return self._app


@contextlib.contextmanager
def fork_process(target):
    ctx = mp.get_context("fork")
    p = ctx.Process(target=target)
    p.start()
    yield p
    p.terminate()
    p.join()
