import gunicorn.app.base


class GunicornServer(gunicorn.app.base.BaseApplication):
    def __init__(self, app, options):
        self._options = options
        self._app = app
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
