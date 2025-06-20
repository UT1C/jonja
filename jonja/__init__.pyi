from typing import Mapping, TypeVar, Callable, Awaitable, TypeAlias, Literal, Any, overload
from os import PathLike
from pathlib import Path
import functools
import re

from yamt import IterativeRandomizer
from jinja2.ext import Extension
import jinja2 as j2

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
        block_start_string: str = ...,
        block_end_string: str = ...,
        variable_start_string: str = ...,
        variable_end_string: str = ...,
        comment_start_string: str = ...,
        comment_end_string: str = ...,
        line_statement_prefix: str | None = ...,
        line_comment_prefix: str | None = ...,
        trim_blocks: bool = ...,
        lstrip_blocks: bool = ...,
        newline_sequence: Literal['\n', '\r\n', '\\u0000'] = ...,
        keep_trailing_newline: bool = ...,
        extensions: functools.Sequence[str | type[Extension]] = ...,
        optimized: bool = ...,
        undefined: j2.Undefined = ...,
        finalize: Callable[..., Any] | None = ...,
        autoescape: bool | Callable[[str | None], bool] = ...,
        cache_size: int = ...,
        bytecode_cache: j2.BytecodeCache | None = ...
    ): ...

    async def search_file(self, name: str) -> tuple[Path, ...]: ...

    @staticmethod
    async def random_paths(paths: tuple[Path, ...]) -> IterativeRandomizer[Path]: ...

    async def read_file(self, path: Path) -> ReadedResult: ...

    def _match_separator(self, text: str) -> bool: ...

    async def render(self, name: str, **kwargs) -> tuple[str, Any]: ...

    async def construct_objs(self, obj_decl: str) -> Any: ...

    @overload
    def filter(self, func: FuncT, name: str | None = None) -> FuncT: ...

    @overload
    def filter(self, name: str, /) -> Callable[[FuncT], FuncT]: ...

    @overload
    def var(self, value: T, name: str | None = None) -> T: ...

    @overload
    def var(self, name: str, /) -> Callable[[T], T]: ...
