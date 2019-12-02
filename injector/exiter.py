from contextlib import AsyncExitStack, ExitStack
from typing import (AsyncContextManager, Awaitable, Callable, ContextManager,
                    Optional, TypeVar, Union, overload)

from injector.errors import ExitError
from injector.types import Kwargs

Exiter = Optional[Union[ExitStack, AsyncExitStack]]

T = TypeVar("T")


@overload
def sync_handle_result(func: Callable[..., ContextManager[T]], kwargs: Kwargs,
                       exiter: Exiter) -> T:
    ...


@overload
def sync_handle_result(func: Callable[..., T], kwargs: Kwargs,
                       exiter: Exiter) -> T:
    ...


def sync_handle_result(func: Callable, kwargs: Kwargs, exiter: Exiter):
    res = func(**kwargs)
    if isinstance(res, ContextManager):
        if not isinstance(exiter, ExitStack):
            raise ExitError(func, exiter)
        return exiter.enter_context(res)
    return res


@overload
async def async_handle_result(func: Callable[..., AsyncContextManager[T]],
                              kwargs: Kwargs, exiter: Exiter) -> T:
    ...


@overload
async def async_handle_result(func: Callable[..., Awaitable[T]],
                              kwargs: Kwargs, exiter: Exiter) -> T:
    ...


async def async_handle_result(func: Callable, kwargs: Kwargs, exiter: Exiter):
    res = func(**kwargs)
    if isinstance(res, Awaitable):
        return await res
    if isinstance(res, AsyncContextManager):
        if not isinstance(exiter, AsyncExitStack):
            raise ExitError(func, exiter)
        return await exiter.enter_async_context(res)
    raise NotImplementedError()
