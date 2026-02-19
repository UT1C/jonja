from typing import TYPE_CHECKING, Callable, Any, TypeAlias
from abc import ABC, abstractmethod
import importlib
import functools
import io

import jinja2 as j2

if TYPE_CHECKING:
    import ruamel.yaml as ryaml
    import ruyaml
    import yaml

YAMLLoader: TypeAlias = Callable[[io.StringIO | str], Any]


class SchemaParser(ABC):
    def __init__(self, env: j2.Environment) -> None:
        super().__init__()

    @abstractmethod
    def parse():
        ...


class YAMLSchemaParser(SchemaParser):
    yaml_loader: YAMLLoader

    def __init__(self, yaml_loader: YAMLLoader | None = None) -> None:
        if yaml_loader is None:
            yaml_loader = self._make_yaml_loader()
        self.yaml_loader = yaml_loader

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
