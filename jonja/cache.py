from typing import Any, Protocol
from collections import defaultdict, OrderedDict
from collections.abc import Hashable
from abc import abstractmethod
from enum import IntEnum

from .di import DependencyInjector as DI

MISSING = object()


class CacheContainer(Protocol):
    @abstractmethod
    def get(
        self,
        object_key: str,
        data_key: int,
        default: Any = ...
    ) -> Any:
        ...

    @abstractmethod
    def set(
        self,
        object_key: str,
        data_key: int,
        value: Any
    ):
        ...


class DictCacheContainer(CacheContainer):
    data: defaultdict[str, OrderedDict[int, Any]]
    maxsize: int = 16

    def __init__(self) -> None:
        self.data = defaultdict(OrderedDict)

    def get(
        self,
        object_key: str,
        data_key: int,
        default: Any = None
    ) -> Any:
        storage = self.data[object_key]
        value = storage.get(data_key, MISSING)
        if value is MISSING:
            return default
        storage.move_to_end(data_key)
        return value

    def set(
        self,
        object_key: str,
        data_key: int,
        value: Any
    ):
        storage = self.data[object_key]
        storage[data_key] = value
        if len(storage) > self.maxsize:
            oldest_key = next(iter(storage))
            del storage[oldest_key]

    def __repr__(self) -> str:
        return f"<DictCacheContainer {self.data}>"


class CacheStrategy(IntEnum):
    NONE = 0
    SCHEMA = 1
    OBJECT = 2


DI.register_factory(DictCacheContainer, key=CacheContainer)
DI.register_factory(DictCacheContainer, key="schema_cache")
DI.register_factory(DictCacheContainer, key="render_cache")
