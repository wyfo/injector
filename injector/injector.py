from __future__ import annotations

import warnings
from asyncio import Lock
from collections import defaultdict
from typing import (Any, AsyncContextManager, Awaitable, Callable,
                    ContextManager, Dict, List, Mapping, Optional,
                    TYPE_CHECKING, Type, TypeVar, Union, cast, overload)

from mypy.ipc import TracebackType

from injector.errors import AsyncError
from injector.utils import AExit, Exit

if TYPE_CHECKING:
    from injector.dependency import Dependency

T = TypeVar("T")
Func = TypeVar("Func", bound=Callable)


class Injector(Dict['Dependency', Any], ContextManager['Injector'],
               AsyncContextManager['Injector']):
    def __init__(self):
        super().__init__()
        self._lock: Mapping[Dependency, Lock] = defaultdict(Lock)
        self._exit: List[Union[Exit, AExit]] = []
        self._async_exit: Optional[bool] = None
        self._async: Optional[bool] = None

    def bind(self, func: Func) -> Func:
        from injector.bound import Bound
        bound = Bound(func, self)
        if self._async is False and bound.is_async:
            raise AsyncError(func, self)
        return cast(Func, bound)

    @overload  # noqa: F811
    def cache(self, dep: Dependency, res: ContextManager[T]) -> T:
        ...

    @overload  # noqa: F811
    def cache(self, dep: Dependency, res: T) -> T:
        ...

    def cache(self, dep, res):  # noqa: F811
        if isinstance(res, ContextManager):
            self._async_exit = self._async_exit or False
            self._exit.append(res.__exit__)
            res = res.__enter__()
        if dep.cached:
            self[dep] = res
        return res

    @overload  # noqa: F811
    async def acache(self, dep: Dependency, res: Awaitable[T]) -> T:
        ...

    @overload  # noqa: F811
    async def acache(self, dep: Dependency, res: AsyncContextManager[T]
                     ) -> T:
        ...

    async def acache(self, dep, res):  # noqa: F811
        if isinstance(res, Awaitable):
            res = await res
        elif isinstance(res, AsyncContextManager):
            self._async_exit = True
            self._exit.append(res.__aexit__)
            res = await res.__aenter__()
        else:
            raise NotImplementedError()
        if dep.cached:
            self[dep] = res
        return res

    def __enter__(self) -> Injector:
        self._async = False
        return self

    def __exit__(self, exc_type: Optional[Type[BaseException]],
                 exc_value: Optional[BaseException],
                 traceback: Optional[TracebackType]):
        while self._exit:
            ex = self._exit.pop()
            ret = ex(exc_type, exc_value, traceback)
            if isinstance(ret, Awaitable):
                raise NotImplementedError("Cannot exit async context manager"
                                          "in sync exit")
        self._async = None

    async def __aenter__(self) -> Injector:
        self._async = True
        return self

    async def __aexit__(self, exc_type: Optional[Type[BaseException]],
                        exc_value: Optional[BaseException],
                        traceback: Optional[TracebackType]):
        while self._exit:
            ex = self._exit.pop()
            ret = ex(exc_type, exc_value, traceback)
            if isinstance(ret, Awaitable):
                await ret
        self._async = None

    def __del__(self):
        if self._exit:
            warnings.warn("Injection context not exited",
                          RuntimeWarning, source=self)
