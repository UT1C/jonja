from typing import Any, Hashable
from collections.abc import Callable, Iterable
import functools

import jinja2 as j2

from .cache import CacheStrategy


class JonjaContext:
    lineno: int
    cache_strategy: CacheStrategy
    used_vars: set[str]
    jinja_ctx: j2.runtime.Context

    _caller: Callable[[], str]

    def __init__(
        self,
        *,
        lineno: int,
        caller: Callable[[], str],
        jinja_ctx: j2.runtime.Context,
        used_vars: set[str],
        cache_strategy: CacheStrategy
    ) -> None:
        self.lineno = lineno
        self._caller = caller
        self.used_vars = used_vars
        self.jinja_ctx = jinja_ctx
        self.cache_strategy = cache_strategy

    @functools.cached_property
    def spec(self) -> str:
        value = self._caller()
        assert isinstance(value, str)
        return value

    @functools.cached_property
    def obj_id(self) -> str:
        return f"{self.jinja_ctx.name}:{self.lineno}"

    @functools.cached_property
    def vars_hash(self) -> int:
        return self._calc_hash(self.jinja_ctx.get(i) for i in self.used_vars)

    @staticmethod
    def _calc_hash(items: Iterable) -> int:
        items = tuple(items)
        for value in items:
            if not isinstance(value, Hashable):
                raise Exception("Cache requested on block of unhashable params")

            if getattr(value, "__hash__", None) is object.__hash__:
                ...  # TODO: throw a warn
        return hash(items)
