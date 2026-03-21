from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime


@dataclass
class Article:
    title: str
    url: str
    source_name: str
    summary_raw: str = ""
    published_at: str = ""
    language: str = "ja"  # "ja" or "en"
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Article":
        return cls(**data)


class BaseCollector(ABC):
    """All collectors must implement this interface."""

    @property
    @abstractmethod
    def source_name(self) -> str:
        pass

    @abstractmethod
    def collect(self) -> list[Article]:
        """Collect articles and return a list of Article objects."""
        pass
