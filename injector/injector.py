from __future__ import annotations

from contextlib import AsyncExitStack, ExitStack
from typing import Callable, TypeVar, overload

from injector.cache import Cache, ContextCache, DictCache
from injector.dependency import bind
from injector.exiter import Exiter

try:
    from dataclasses import is_dataclass
except ImportError:
    def is_dataclass(obj):  # type: ignore
        return False

Func = TypeVar("Func", bound=Callable)
Cls = TypeVar("Cls", bound=type)


class Injector:
    def __init__(self, cache: Cache, exiter: Exiter = None):
        super().__init__()
        self.cache = cache
        self.exiter = exiter

    @overload  # noqa: F811
    def bind(self, func: Func) -> Func:
        ...

    @overload  # noqa: F811
    def bind(self, *, cached: bool) -> Callable[[Func], Func]:
        ...

    @overload  # noqa: F811
    def bind(self, func: Func, *, cached: bool = False) -> Func:
        ...

    def bind(self, func=None, *, cached=False):  # noqa: F811
        decorator = bind(self.cache, self.exiter, cached=cached)
        if func is None:
            return decorator
        else:
            return decorator(func)

    def bind_dataclass(self, cls: Cls) -> Cls:
        assert is_dataclass(cls)
        cls.__init__ = self.bind(cls.__init__,  cached=False)  # type: ignore
        return cls

    def __enter__(self) -> Injector:
        assert self.exiter is None
        self.exiter = ExitStack()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        assert isinstance(self.exiter, ExitStack)
        self.exiter.__exit__(exc_type, exc_val, exc_tb)

    async def __aenter__(self):
        assert self.exiter is None
        self.exiter = AsyncExitStack()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        assert isinstance(self.exiter, AsyncExitStack)
        await self.exiter.__aexit__(exc_type, exc_val, exc_tb)


class GlobalInjector(Injector):
    def __init__(self):
        super().__init__(DictCache())


class ContextInjector(Injector):
    def __init__(self):
        super().__init__(ContextCache())
