from typing import Literal, overload
from pathlib import Path

from yamt import IterativeRandomizer
from cache import AsyncTTL, AsyncLRU
from aiofile import async_open
import jinja2 as j2


@AsyncLRU(maxsize=None)
async def cached_path_rand(path: Path, ext: str) -> IterativeRandomizer[Path]:
    return IterativeRandomizer(path.glob(f"[!_]*.{ext}"))


@overload
async def load_text(
    name: str,
    rand: bool = False,
    *,
    return_name: bool = False,
    force_template: bool = False,
    **kwargs
) -> str:
    ...


@overload
async def load_text(
    name: str,
    rand: bool = False,
    *,
    return_name: Literal[True],
    force_template: bool = False,
    **kwargs
) -> tuple[str, str]:  # value, name
    ...


async def load_text(
    name: str,
    rand: bool = False,
    *,
    return_name: bool = False,
    force_template: bool = False,
    **kwargs
) -> str | tuple[str, str]:
    if force_template or kwargs:
        ext = "j2"
        path = struct.TEMPLATES_PATH
        render = j2_render
    else:
        ext = "txt"
        path = struct.TEXTS_PATH
        render = read_file

    if rand:
        path /= name
        assert path.exists() and path.is_dir()
        path = (await cached_path_rand(path, ext)).get()
    else:
        path /= f"{name}.{ext}"
        assert path.exists()

    result = await render(path, **kwargs)
    if return_name:
        return result, path.stem
    else:
        return result


@AsyncTTL(300, maxsize=8)
async def read_file(path: Path) -> str:
    async with async_open(path) as afp:
        return await afp.read()


async def j2_render(path: Path, **kwargs) -> str:
    return await j2_env.from_string(await read_file(path)).render_async(**kwargs)


j2_env = j2.Environment(
    loader=j2.FileSystemLoader(struct.TEMPLATES_PATH),
    enable_async=True
)
# j2_env.globals.update({})
# j2_env.filters.update({})
