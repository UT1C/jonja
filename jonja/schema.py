from typing import TYPE_CHECKING, Callable, Any, TypeAlias
from abc import ABC, abstractmethod
import importlib
import functools
import io

from .structures import JonjaContext
from .cache import CacheContainer, CacheStrategy
from .di import DependencyInjector as DI

if TYPE_CHECKING:
    import ruamel.yaml as ryaml
    import ruyaml
    import yaml

StrStream: TypeAlias = io.StringIO | str
YAMLLoader: TypeAlias = Callable[[StrStream], Any]
MISSING = object()


class SchemaParser(ABC):
    cache: CacheContainer

    @abstractmethod
    def get(self, render_ctx: JonjaContext) -> Any:
        ...

    @abstractmethod
    def parse(self, spec: StrStream) -> Any:
        ...


class YAMLSchemaParser(SchemaParser):
    yaml_loader: YAMLLoader

    cache = DI[CacheContainer, "YAMLSchemaParser"]("schema_cache")

    def __init__(self, yaml_loader: YAMLLoader | None = None) -> None:
        if yaml_loader is None:
            yaml_loader = self._make_yaml_loader()
        self.yaml_loader = yaml_loader

    @staticmethod
    def _make_yaml_loader() -> YAMLLoader:
        try:
            module: "ryaml" = importlib.import_module("ruamel.yaml")
            return module.YAML().load
        except ImportError:
            ...

        try:
            module: "ruyaml" = importlib.import_module("ruyaml")
            return ruyaml.YAML().load
        except ImportError:
            ...

        try:
            module: "yaml" = importlib.import_module("yaml")
            loader_cls: "yaml.Loader" = (
                getattr(module, "CLoader", None)
                or getattr(module, "Loader")
            )
            return functools.partial(module.load, Loader=loader_cls)
        except ImportError:
            ...

        raise Exception("no suitable yaml parser found")

    def get(self, render_ctx: JonjaContext) -> Any:
        if render_ctx.cache_strategy in (CacheStrategy.SCHEMA, CacheStrategy.OBJECT):
            schema = self.cache.get(
                render_ctx.obj_id,
                render_ctx.vars_hash,
                default=MISSING
            )
            if schema is not MISSING:
                return schema
        return self.parse(render_ctx.spec)

    def parse(self, spec: StrStream) -> Any:
        data = self.yaml_loader(spec)
        return data


DI.register_factory(YAMLSchemaParser, key=SchemaParser)
