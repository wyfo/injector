from contextlib import contextmanager, asynccontextmanager
from unittest.mock import Mock

from pytest import mark, raises

from injector.exiter import DefaultExiter


@mark.asyncio
async def test_exiter(mocker):
    @contextmanager
    def ctx():
        nonlocal var
        var += 1
        yield
        var -= 1

    @asynccontextmanager
    async def actx():
        nonlocal var
        var += 1
        yield
        var -= 1

    var = 0
    with raises(AssertionError):
        with DefaultExiter() as sync_exiter:
            assert sync_exiter._async is False
            ctx_, actx_ = ctx(), actx()
            ctx_.__enter__(), await actx_.__aenter__()
            assert var == 2
            sync_exiter.register_exit(ctx_.__exit__)
            sync_exiter.register_exit(actx_.__aexit__)
    var = 0
    async with DefaultExiter() as async_exiter:
        assert async_exiter._async is True
        ctx_, actx_ = ctx(), actx()
        ctx_.__enter__(), await actx_.__aenter__()
        assert var == 2
        async_exiter.register_exit(ctx_.__exit__)
        async_exiter.register_exit(actx_.__aexit__)
    assert var == 0

    exiter = DefaultExiter()
    exiter.register_exit(Mock())
    warn = mocker.patch("warnings.warn")
    del exiter
    warn.assert_called_once()