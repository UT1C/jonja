from typing import Mapping, TypeVar, Callable, Awaitable, TypeAlias, Any, overload
from os import PathLike
from pathlib import Path
import functools
import itertools
import re

from cache import Cached, LRU, TTL
from aiofile import async_open
import jinja2 as j2
from yamt import IterativeRandomizer

from .tools import ObjRenderer

ReadedResult: TypeAlias = tuple[j2.Template, j2.Template | None] | tuple[str, str | None]
T = TypeVar("T")
FuncT = TypeVar("FuncT", bound=Callable)
ReaderT = TypeVar("ReaderT", bound=Callable[[Path], Awaitable[ReadedResult]])
SearchFileT = TypeVar(
    "SearchFileT",
    bound=Callable[[str], Awaitable[tuple[Path, ...]]]
)
ConstructorT = TypeVar(
    "ConstructorT",
    bound=Callable[[str], Any]
)


class JonjaEnv(j2.Environment):
    templates_path: Path
    obj_decl_separator: re.Pattern | str

    def __init__(
        self,
        templates_path: PathLike,
        *,
        globals: Mapping[str, Any] | None = None,
        filters: Mapping[str, Callable] | None = None,
        reader_wrap: Callable[[ReaderT], ReaderT] | None = None,
        search_file_wrap: Callable[[SearchFileT], SearchFileT] | None = None,
        construct_objs_wrap: Callable[[ConstructorT], ConstructorT] | None = None,
        obj_decl_separator: re.Pattern | str = "*#!#*",
        **kwargs
    ) -> None:
        if reader_wrap is None:
            reader_wrap = Cached(LRU(None))
        if search_file_wrap is None:
            search_file_wrap = Cached(LRU(None))
        if construct_objs_wrap is None:
            construct_objs_wrap = Cached(TTL(300, maxsize=16))

        assert not kwargs.get("enable_async"), "async only"
        kwargs["enable_async"] = True
        kwargs["auto_reload"] = False
        assert kwargs.get("loader") is None, "no loader allowed when path provided"
        kwargs["loader"] = None

        self.templates_path = Path(templates_path)
        self.obj_decl_separator = obj_decl_separator

        self.search_file = search_file_wrap(self.search_file)
        self.random_paths = search_file_wrap(self.random_paths)
        self.read_file = reader_wrap(self.read_file)
        self.construct_objs = construct_objs_wrap(self.construct_objs)

        super().__init__(**kwargs)

        if globals is not None:
            self.globals.update(globals)
        if filters is not None:
            self.filters.update(filters)

    async def search_file(self, name: str) -> tuple[Path, ...]:
        return tuple(
            itertools.chain(
                *(self.templates_path.glob(f"{name}.{ext}") for ext in ("txt", "j2")),
                self.templates_path.glob(f"{name}/*")
            )
        )

    @staticmethod
    async def random_paths(paths: tuple[Path, ...]) -> IterativeRandomizer[Path]:
        return IterativeRandomizer(paths)

    async def read_file(self, path: Path) -> ReadedResult:
        body = list()
        async with async_open(path, encoding="UTF-8") as afp:
            while (line := await afp.readline()):
                line = line.rstrip("\r\n")
                if self._match_separator(line):
                    break
                body.append(line)
            body = "\n".join(body)
            obj_decl = await afp.read()

        if path.suffix != ".txt":
            body = self.from_string(body)
            if obj_decl is not None:
                obj_decl = self.from_string(obj_decl)
        return (body, obj_decl)

    def _match_separator(self, text: str) -> bool:
        sep = self.obj_decl_separator
        text = text.strip()
        match sep:
            case str():
                return text == sep
            case re.Pattern():
                return sep.match(text) is not None
            case _:
                raise AssertionError()

    async def render(self, name: str, **kwargs) -> tuple[str, Any]:
        paths = await self.search_file(name)
        match len(paths):
            case 0:
                raise FileNotFoundError(name)
            case 1:
                path = paths[0]
            case _:
                path = next(await self.random_paths(paths))

        body, obj_decl = await self.read_file(path)
        if isinstance(body, j2.Template):
            body = await body.render_async(**kwargs)
            if obj_decl is not None:
                obj_decl = await obj_decl.render_async(**kwargs)

        if obj_decl is None:
            objs = None
        else:
            objs = await self.construct_objs(obj_decl)
        return (body, objs)

    async def construct_objs(self, obj_decl: str) -> Any:
        return await ObjRenderer(obj_decl, self).construct()

    @overload
    def filter(self, func: FuncT, name: str) -> FuncT:
        ...

    @overload
    def filter(self, name: str, /) -> Callable[[FuncT], FuncT]:
        ...

    def filter(
        self,
        value: FuncT | str,
        name: str | None = None
    ) -> FuncT | Callable[[FuncT], FuncT]:
        if isinstance(value, str):
            return functools.partial(self.filter, name=name)

        if name is None:
            name = value.__name__
        self.filters[name] = value
        return value

    @overload
    def var(self, value: T, name: str) -> T:
        ...

    @overload
    def var(self, name: str, /) -> Callable[[T], T]:
        ...

    def var(
        self,
        value: T | str,
        name: str | None = None
    ) -> T | Callable[[T], T]:
        if isinstance(value, str):
            return functools.partial(self.var, name=name)

        if name is None:
            name = value.__name__
        self.globals[name] = value
        return value
