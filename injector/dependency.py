from __future__ import annotations

from asyncio import gather
from inspect import Parameter, iscoroutinefunction, signature
from typing import (Any, AsyncContextManager, Awaitable, Callable,
                    ContextManager, Dict, Mapping, Optional, TYPE_CHECKING,
                    Tuple, Type, TypeVar, overload)

from injector.errors import (AsyncDependency, DependencyWithFreeParameters,
                             EmptyDependency, InvalidType)
from injector.utils import args_to_kwargs, is_async_ctx_mgr

try:
    from typing import get_type_hints
except ImportError:
    def get_type_hints(*args, **kwargs):  # type: ignore
        raise NotImplementedError("get_type_hints cannot be imported")

if TYPE_CHECKING:
    from injector.injector import Injector

Kwargs = Dict[str, Any]


class Dependency:
    def __init__(self, func: Callable, *, cached: bool):
        assert callable(func)
        self.func = func
        self.cached = cached
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
                tmp[param.name] = Dependency(type_, cached=True)
            elif param.default is Parameter.empty and cached:
                raise DependencyWithFreeParameters(func)
        self.dependencies: Mapping[str, Dependency] = tmp
        async_dep = any(d.is_async for d in self.dependencies.values())
        if async_dep and not self.is_async:
            raise AsyncDependency(func)

    def __eq__(self, other):
        assert isinstance(other, Dependency)
        return self.func == other.func

    def __hash__(self):
        return hash(self.func)

    @property
    def is_async(self) -> bool:
        return iscoroutinefunction(self.func) or is_async_ctx_mgr(self.func)

    def _sync_call(self, inj: Injector, kwargs: Kwargs = None):
        kwargs = kwargs or {}
        assert not self.is_async
        if self in inj:
            return inj[self]
        for name, sub_dep in self.dependencies.items():
            if name in kwargs:
                continue
            kwargs[name] = sub_dep._sync_call(inj)
        res = self.func(**kwargs)
        if isinstance(res, ContextManager):
            inj.register_exit(res.__exit__)
            res = res.__enter__()
        if self.cached:
            inj[self] = res
        return res

    async def _async_call(self, inj: Injector, kwargs: Kwargs = None):
        kwargs = kwargs or {}
        assert self.is_async
        if self in inj:
            return inj[self]
        gathered = []
        for name, sub_dep in self.dependencies.items():
            if name in kwargs:
                continue
            elif sub_dep.is_async:
                # noinspection PyShadowingNames
                async def set_param(name: str, sub_dep: Dependency):
                    async with inj.lock(sub_dep):
                        kwargs[name] = (  # type: ignore
                            await sub_dep._async_call(inj))

                gathered.append(set_param(name, sub_dep))
            else:
                kwargs[name] = sub_dep._sync_call(inj)
        if gathered:
            await gather(*gathered)
        res = self.func(**kwargs)
        if isinstance(res, Awaitable):
            res = await res
        elif isinstance(res, AsyncContextManager):
            inj.register_exit(res.__aexit__)
            res = await res.__aenter__()
        else:
            raise NotImplementedError()
        if self.cached:
            inj[self] = res
        return res

    def call(self, inj: Injector, args: Tuple = (), kwargs: Kwargs = None):
        kwargs = kwargs or {}
        kwargs.update(args_to_kwargs(self.parameters, *args))
        if self.is_async:
            return self._async_call(inj, kwargs)
        else:
            return self._sync_call(inj, kwargs)


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
    else:
        return Dependency(func, cached=True)
