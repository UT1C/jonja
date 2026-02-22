from typing import cast
from collections import deque
from collections.abc import Callable, Sequence, Hashable, Iterable
import functools

from jinja2.ext import Extension
from jinja2.parser import Parser
from jinja2 import nodes
import jinja2 as j2

from .cache import CacheStrategy
from .schema import SchemaParser, YAMLSchemaParser
from .render import ObjRender
from .structures import JonjaContext
from .di import DependencyInjector as DI

MISSING = object()


class JonjaExt(Extension):
    tags = {"jobj"}

    obj_render = DI(ObjRender)

    def parse(self, parser: Parser) -> nodes.Node | list[nodes.Node]:
        lineno: int = next(parser.stream).lineno

        cache_strategy = CacheStrategy.NONE
        while not parser.stream.current.test("block_end:%}"):
            expr = parser.parse_expression()
            if isinstance(expr, nodes.Name):
                match expr.name:
                    case "cached":
                        if cache_strategy != CacheStrategy.SCHEMA:
                            cache_strategy = CacheStrategy.OBJECT
                    case "schema":
                        cache_strategy = CacheStrategy.SCHEMA
                    case _:
                        raise Exception("invalid args for jobj")
            else:
                raise Exception("invalid args for jobj")

        body = parser.parse_statements(("name:endjobj", ), drop_needle=True)

        render_kwargs = list()
        render_kwargs.append(nodes.Keyword("lineno", nodes.Const(lineno)))
        render_kwargs.append(nodes.Keyword("used_vars", nodes.Const(self._search_names(body))))
        render_kwargs.append(nodes.Keyword("cache_strategy", nodes.Const(cache_strategy.value)))

        return nodes.CallBlock(
            self.call_method(self._render_objects.__name__, kwargs=render_kwargs),
            [],
            [],
            body
        ).set_lineno(lineno)

    @j2.pass_context
    def _render_objects(
        self,
        ctx: j2.runtime.Context,
        lineno: int,
        used_vars: set[str],
        cache_strategy: CacheStrategy,
        caller: Callable
    ) -> str:
        render_ctx = JonjaContext(
            lineno=lineno,
            caller=caller,
            jinja_ctx=ctx,
            used_vars=used_vars,
            cache_strategy=cache_strategy
        )

        objs = self.obj_render.get(render_ctx)

        return ""

    @classmethod
    def _search_names(cls, body: nodes.Node | Sequence[nodes.Node]) -> set[str]:
        names = set()
        exclude = set()
        for node in cls._flatten_nodes(body):
            if isinstance(node, nodes.Name):
                if node.name not in names:
                    if node.ctx == "load":
                        names.add(node.name)
                    else:
                        exclude.add(node.name)
        names -= exclude
        return names

    @staticmethod
    def _flatten_nodes(body: nodes.Node | Sequence[nodes.Node]) -> deque[nodes.Node]:
        if isinstance(body, nodes.Node):
            body = (body, )

        result = deque(body)
        queue = deque(range(len(result)))
        while len(queue) != 0:
            offset = 0
            for i in tuple(queue):
                queue.popleft()
                i += offset

                node = result[i]
                children = tuple(node.iter_child_nodes())

                for child in children:
                    result.insert(i, child)
                    queue.append(i)
                    i += 1
                offset += len(children)

        return result
