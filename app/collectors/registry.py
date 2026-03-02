from app.collectors.base import Collector
from app.collectors.dcinside import DcInsideCollector
from app.collectors.hackernews import HackerNewsCollector
from app.collectors.reddit import RedditCollector


class CollectorRegistry:
    def __init__(self) -> None:
        self._collectors: dict[str, Collector] = {
            "dcinside": DcInsideCollector(),
            "reddit": RedditCollector(),
            "hackernews": HackerNewsCollector(),
        }

    def get(self, source_type: str) -> Collector:
        collector = self._collectors.get(source_type)
        if collector is None:
            raise ValueError(f"Unsupported source_type: {source_type}")
        return collector

    def supported_sources(self) -> list[str]:
        return sorted(self._collectors.keys())

