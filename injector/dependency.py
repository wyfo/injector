from __future__ import annotations

from asyncio import gather
from inspect import Parameter, iscoroutinefunction, signature
from typing import (Any, AsyncContextManager, Awaitable, Callable,
                    ContextManager, Dict, Mapping, Optional, Type, TypeVar,
                    overload)

try:
    from typing import get_type_hints
except ImportError:
    def get_type_hints(*args, **kwargs):  # type: ignore
        raise NotImplementedError("get_type_hints cannot be imported")

from injector.errors import (AsyncDependency, DependencyWithFreeParameters,
                             EmptyDependency, InvalidType)
from injector.injector import Injector
from injector.utils import args_to_kwargs, is_async_ctx_mgr


class Dependency:
    def __init__(self, func: Callable):
        self.func = func
        self.parameters = signature(func).parameters
        type_hints: Optional[Mapping[str, Type]] = None
        tmp: Dict[str, Dependency] = {}
        for param in self.parameters.values():
            if isinstance(param.default, Dependency):
                tmp[param.name] = param.default
            elif isinstance(param.default, TypeDependency):
                if param.annotation is Parameter.empty:
                    raise EmptyDependency(func)
                if isinstance(param.annotation, str):
                    if type_hints is None:
                        try:
                            type_hints = get_type_hints(func)
                        except NameError as err:
                            raise InvalidType(func, err)
                    type_ = type_hints[param.name]
                else:
                    type_ = param.annotation
                tmp[param.name] = Dependency(type_)

        self.dependencies: Mapping[str, Dependency] = tmp
        async_dep = any(d.is_async for d in self.dependencies.values())
        if async_dep and not self.is_async:
            raise AsyncDependency(func)

    def __eq__(self, other):
        assert isinstance(other, Dependency)
        return self.func == other.func

    def __hash__(self):
        return hash(self.func)

    def __repr__(self):
        return repr(self.func)

    @property
    def cached(self) -> bool:
        return True

    @property
    def is_async(self) -> bool:
        return iscoroutinefunction(self.func) or is_async_ctx_mgr(self.func)

    def _sync_call(self, inj: Injector, **kwargs):
        if self in inj:
            return inj[self]
        for name, sub_dep in self.dependencies.items():
            if name in kwargs:
                continue
            kwargs[name] = sub_dep._sync_call(inj)
        return inj.cache(self, self.func(**kwargs))

    async def _async_call(self, inj: Injector, **kwargs):
        if self in inj:
            return inj[self]
        gathered = []
        for name, sub_dep in self.dependencies.items():
            if name in kwargs:
                continue
            elif sub_dep.is_async:
                # noinspection PyShadowingNames
                async def set_param(name: str, sub_dep: Dependency):
                    # noinspection PyProtectedMember
                    async with inj._lock[sub_dep]:
                        kwargs[name] = \
                            await sub_dep._async_call(inj)
                        pass

                gathered.append(set_param(name, sub_dep))
            else:
                kwargs[name] = sub_dep._sync_call(inj)
        if gathered:
            await gather(*gathered)
        return await inj.acache(self, self.func(**kwargs))

    def call(self, inj: Injector, *args, **kwargs):
        kwargs.update(args_to_kwargs(self.parameters, *args))
        if self.is_async:
            return self._async_call(inj, **kwargs)
        else:
            return self._sync_call(inj, **kwargs)


class TypeDependency:
    pass


Injected = TypeVar("Injected")


@overload
def inject(func: Callable[..., ContextManager[Injected]]) -> Injected:
    ...


@overload
def inject(func: Callable[..., Awaitable[Injected]]) -> Injected:
    ...


@overload
def inject(func: Callable[..., AsyncContextManager[Injected]]) -> Injected:
    ...


@overload
def inject(func: Callable[..., Injected]) -> Injected:
    ...


@overload
def inject() -> Any:
    ...


def inject(func: Callable = None):
    if func is None:
        return TypeDependency()
    dep = Dependency(func)
    if len(dep.parameters) != len(dep.dependencies):
        for param in dep.parameters.values():
            if param.default is Parameter.empty:
                raise DependencyWithFreeParameters(func)
    return dep
