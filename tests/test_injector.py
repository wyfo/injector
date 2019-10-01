from unittest.mock import Mock

from pytest import raises, mark

from injector import Injector, inject
from injector.errors import AsyncError


def test_inj_sync():
    var = 0
    def exit_(*args):
        nonlocal var
        var += 1
    with Injector() as inj:
        assert not inj._async
        inj.register_exit()
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
    inj = Injector()
    inj.register_exit(Mock())
    warn = mocker.patch('warnings.warn')
    del inj
    warn.assert_called_once()


def test_async_error():
    async def func():
        return 0

    with Injector() as inj:
        with raises(AsyncError):
            inj.bind(func)


@mark.parametrize("cached, final", [(False, 2), (True, 1)])
def test_bind(cached, final):
    count = 0

    def dep() -> int:
        return 0

    def func(i: int = inject(dep)) -> int:
        nonlocal count
        count += 1
        return i

    inj = Injector()
    bound = inj.bind(func, cached=cached)

    assert bound() == 0
    assert count == 1
    assert bound() == 0
    assert count == final

