import inspect
from dataclasses import dataclass
from pathlib import Path

from compone.component import _ComponentBase

from .parsers import BaseParser, MarkdownParser
from .themes import BasicTheme


@dataclass
class PageRoute:
    get_content: callable
    parser: BaseParser
    component: _ComponentBase
    output_path: Path


class Config:
    THEME: _ComponentBase = BasicTheme
    OUTPUT_DIR = "public_html"
    CONTENT_DIR = "content"
    CONTENT_PARSERS = {
        ".md": MarkdownParser(),
    }
    INDEX_NAME = "index"

    def __init__(self) -> None:
        self._cwd = Path.cwd()

    @staticmethod
    def _is_subclass(cls):
        return inspect.isclass(cls) and issubclass(cls, Config) and cls is not Config

    @property
    def _output_dir(self):
        return Path(self.OUTPUT_DIR).resolve()

    @property
    def _content_dir(self):
        return Path(self.CONTENT_DIR).resolve()

    def get_content_routes(self) -> list[PageRoute]:
        paths = []
        for content_path in self._content_dir.rglob("*"):
            if content_path.is_dir():
                continue

            content_relpath = content_path.relative_to(self._content_dir)
            if content_path.stem == self.INDEX_NAME:
                component = self.THEME.INDEX_COMPONENT
                output_relpath = content_relpath.parent / "index.html"
            else:
                component = self.THEME.PAGE_COMPONENT
                output_relpath = (
                    content_relpath.parent / content_path.stem / "index.html"
                )

            parser = self.CONTENT_PARSERS.get(content_path.suffix)
            page_route = PageRoute(
                content_path.read_text,
                parser,
                component,
                self._output_dir / output_relpath,
            )
            paths.append(page_route)

        return paths
