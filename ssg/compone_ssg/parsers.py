import abc

import yaml
from compone import safe
from markdown import markdown


class BaseParser(metaclass=abc.ABCMeta):
    def parse(self, get_content: callable):
        content_text = get_content()
        meta = self.parse_meta(content_text)
        content = self.parse_content(content_text)
        return meta, content

    @abc.abstractmethod
    def parse_meta(content: str):
        """Parse the page metadata like Front matter YAML or RST meta."""

    @abc.abstractmethod
    def parse_content(content: str):
        """Parse the page main content."""


class MarkdownParser(BaseParser):
    def parse_meta(self, content: str):
        meta_content = content.split("---", 2)[1]
        return yaml.safe_load(meta_content)

    def parse_content(self, content: str):
        page = content.rsplit("---", 1)[-1]
        return safe(markdown(page))
