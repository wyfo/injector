from contextlib import asynccontextmanager, contextmanager
from unittest.mock import MagicMock

from pytest import mark, raises

from injector import Injector
from injector.errors import AsyncError


def test_inj_sync():
    def dep():
        pass

    dep_ = MagicMock()
    with Injector() as inj:
        assert dep_ not in inj
        inj.cache(dep_, dep())
        assert inj[dep_] is None
    var = 0

    @contextmanager
    def ctx_dep():
        nonlocal var
        var += 1
        yield
        var -= 1

    ctx_dep_ = MagicMock()
    with Injector() as inj:
        assert ctx_dep_ not in inj
        assert var == 0
        inj.cache(ctx_dep_, ctx_dep())
        assert var == 1
        assert inj[ctx_dep_] is None
    assert var == 0


@mark.asyncio
async def test_inj_async():
    async def dep():
        pass

    dep_ = MagicMock()
    async with Injector() as inj:
        assert dep_ not in inj
        await inj.acache(dep_, dep())
        assert inj[dep_] is None
    var = 0

    @asynccontextmanager
    async def ctx_dep():
        nonlocal var
        var += 1
        yield
        var -= 1

    ctx_dep_ = MagicMock()
    async with Injector() as inj:
        assert ctx_dep_ not in inj
        assert var == 0
        await inj.acache(ctx_dep_, ctx_dep())
        assert var == 1
        assert inj[ctx_dep_] is None
    assert var == 0


def test_del(mocker):
    @contextmanager
    def dep():
        yield

    inj = Injector()
    inj.cache(MagicMock(), dep())
    warn = mocker.patch('warnings.warn')
    del inj
    warn.assert_called_once()


def test_async_error():
    async def func():
        return 0

    with Injector() as inj:
        with raises(AsyncError):
            inj.bind(func)
