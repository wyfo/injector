from __future__ import annotations

import warnings
from asyncio import Lock
from collections import defaultdict
from functools import wraps
from typing import (Any, AsyncContextManager, Awaitable, Callable,
                    ContextManager, Dict, List, Mapping, Optional,
                    TYPE_CHECKING, Type, TypeVar, Union, cast, overload)

from mypy.ipc import TracebackType

from injector.errors import AsyncError
from injector.utils import AExit, Exit

if TYPE_CHECKING:
    from injector.dependency import Dependency

try:
    from dataclasses import is_dataclass
except ImportError:
    def is_dataclass(obj):  # type: ignore
        return False

T = TypeVar("T")
Func = TypeVar("Func", bound=Callable)
Cls = TypeVar("Cls", bound=type)


class Injector(Dict['Dependency', Any], ContextManager['Injector'],
               AsyncContextManager['Injector']):
    def __init__(self):
        super().__init__()
        self._lock: Mapping[Dependency, Lock] = defaultdict(Lock)
        self._exit: List[Union[Exit, AExit]] = []
        self._async: Optional[bool] = None

    def lock(self, dep: Dependency) -> Lock:
        return self._lock[dep]

    @overload  # noqa: F811
    def bind(self, *, cached: bool) -> Callable[[Func], Func]:
        ...

    @overload  # noqa: F811
    def bind(self, func: Func, *, cached: bool = False) -> Func:
        ...

    def bind(self, func=None, *, cached=False):  # noqa: F811
        # noinspection PyShadowingNames
        def decorator(func: Func) -> Func:
            assert not isinstance(func, type), \
                "cannot bind class"
            from injector.dependency import Dependency
            bound = Dependency(func, cached=cached)
            if self._async is False and bound.is_async:
                raise AsyncError(func, self)

            @wraps(func)
            def wrapper(*args, **kwargs):
                return bound.call(self, args, kwargs)

            return cast(Func, wrapper)

        if func is None:
            return decorator
        else:
            return decorator(func)

    def bind_dataclass(self, cls: Cls) -> Cls:
        cls.__init__ = self.bind(cls.__init__)  # type: ignore
        return cls

    def register_exit(self, exit_: Union[Exit, AExit]):
        self._exit.append(exit_)

    def __enter__(self) -> Injector:
        self._async = False
        return self

    def __exit__(self, exc_type: Optional[Type[BaseException]],
                 exc_value: Optional[BaseException],
                 traceback: Optional[TracebackType]):
        while self._exit:
            ex = self._exit.pop()
            ret = ex(exc_type, exc_value, traceback)
            assert not isinstance(ret, Awaitable), \
                "Cannot exit async context manager in sync injector"
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
