from typing import Any
import importlib
import asyncio

import jinja2 as j2
import oyaml as yaml


class ObjRenderer:
    objs_spec: dict | list
    env: j2.Environment

    def __init__(self, obj_decl: str, env: j2.Environment) -> None:
        self.objs_spec = yaml.load(obj_decl.strip(), yaml.FullLoader)
        self.env = env

    async def construct(self) -> Any:
        return await self._construct(self.objs_spec)

    async def _construct(self, spec: dict | list) -> Any:
        match spec:
            case dict():
                if "$cls" in spec:
                    return await self.make_obj(spec)

                else:
                    tasks = list()
                    for v in spec.values():
                        tasks.append(self._construct(v))
                    results = await asyncio.gather(*tasks)
                    return dict(zip(spec, results))

            case list():
                return tuple(await asyncio.gather(*map(self._construct, spec)))

            case _:
                return spec

    async def make_obj(self, spec: dict[str, Any]) -> Any:
        spec = spec.copy()
        cls_name: str = spec.pop("$cls")

        cls = self.env.globals.get(cls_name)
        if cls is None:
            module, cls = cls_name.split(":")
            module = importlib.import_module(module)
            cls = getattr(module, cls)

        args = spec.pop("$args", None)
        if args is None:
            args = tuple()
        else:
            args = await self._construct(args)
        kwargs = await self._construct(spec)

        instance = cls(*args, **kwargs)
        return instance
