from typing import Callable, Any
import importlib

from jinja2.ext import Extension
from jinja2.parser import Parser
from jinja2 import nodes
import jinja2 as j2


class JonjaExt(Extension):
    tags = {"jobj"}

    def __init__(self, environment: j2.Environment) -> None:
        super().__init__(environment)

    def parse(self, parser: Parser) -> nodes.Node | list[nodes.Node]:
        lineno: int = next(parser.stream).lineno
        body = parser.parse_statements(("name:endjobj", ), drop_needle=True)
        return nodes.CallBlock(
            self.call_method(self._render_objects.__name__),
            [],
            [],
            body
        ).set_lineno(lineno)

    def _render_objects(self, caller: Callable) -> str:
        obj_spec: str = caller()
        obj_spec = obj_spec.strip()

        return ""


class ObjRenderer:
    namespace: dict

    def __init__(self, namespace: dict | None = None) -> dict:
        if namespace is None:
            namespace = dict()
        self.namespace = namespace

    def construct(self, spec: dict | list | Any) -> Any:
        match spec:
            case dict():
                if "$cls" in spec:
                    return self.make_obj(spec)

                else:
                    results = list()
                    for v in spec.values():
                        results.append(self.construct(v))
                    return dict(zip(spec, results))

            case list():
                return tuple(map(self.construct, spec))

            case _:
                return spec

    def make_obj(self, spec: dict[str, Any]) -> Any:
        spec = spec.copy()
        cls_name: str = spec.pop("$cls")

        cls = self.namespace.get(cls_name)
        if cls is None:
            module, cls = cls_name.split(":")
            module = importlib.import_module(module)
            cls = getattr(module, cls)

        args = spec.pop("$args", None)
        if args is None:
            args = tuple()
        else:
            args = self.construct(args)
        kwargs = self.construct(spec)

        instance = cls(*args, **kwargs)
        return instance
