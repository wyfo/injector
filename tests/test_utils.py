from contextlib import asynccontextmanager
from inspect import signature

from pytest import mark

from injector.utils import args_to_kwargs, is_async_ctx_mgr


class AsyncCtxMgr:
    def __aenter__(self):
        pass

    def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


@asynccontextmanager
async def async_ctx_mgr():
    yield


def complex_async_ctx_mgr():
    return async_ctx_mgr()


@mark.parametrize("obj, expected", [
    (AsyncCtxMgr, True),
    (async_ctx_mgr, True),
    (complex_async_ctx_mgr, False),
])
def test_is_async_ctx_mgr(obj, expected):
    assert is_async_ctx_mgr(obj) == expected


def func(a, b, c):
    pass


def test_args_to_kwargs():
    parameters = signature(func).parameters
    assert args_to_kwargs(parameters, 0, 1) == {"a": 0, "b": 1}
