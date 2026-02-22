from typing import Any
import importlib

from .cache import CacheContainer, CacheStrategy
from .structures import JonjaContext
from .di import DependencyInjector as DI
from .schema import SchemaParser

MISSING = object()


class ObjRender:
    namespace: dict

    schema_parser = DI(SchemaParser)
    cache = DI[CacheContainer, "ObjRender"]("render_cache")

    def __init__(self, namespace: dict | None = None) -> dict:
        if namespace is None:
            namespace = dict()
        self.namespace = namespace

    def get(self, render_ctx: JonjaContext) -> Any:
        if render_ctx.cache_strategy == CacheStrategy.OBJECT:
            obj = self.cache.get(
                render_ctx.obj_id,
                render_ctx.vars_hash,
                default=MISSING
            )
            if obj is not MISSING:
                return obj
        return self.construct(self.schema_parser.get(render_ctx))

    def construct(self, schema: Any) -> Any:
        match schema:
            case dict():
                if "$cls" in schema:
                    return self._make_obj(schema)

                else:
                    results = list()
                    for v in schema.values():
                        results.append(self.construct(v))
                    return dict(zip(schema, results))

            case list():
                return tuple(map(self.construct, schema))

            case _:
                return schema

    def _make_obj(self, schema: dict[str, Any]) -> Any:
        schema = schema.copy()
        cls_name: str = schema.pop("$cls")

        cls = self.namespace.get(cls_name)
        if cls is None:
            module, cls = cls_name.split(":")
            module = importlib.import_module(module)
            cls = getattr(module, cls)

        args = schema.pop("$args", None)
        if args is None:
            args = tuple()
        else:
            args = self.construct(args)
        kwargs = self.construct(schema)

        instance = cls(*args, **kwargs)
        return instance


DI.register_factory(ObjRender)
