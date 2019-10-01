from asyncio.tasks import sleep
from time import perf_counter

from pytest import fixture, mark

from injector import Injector, inject


@fixture
def injector() -> Injector:
    return Injector()


@mark.asyncio
async def test_call(injector):
    def dep() -> int:
        return 42

    def async_dep() -> int:
        return 42

    @injector.bind
    def func(i: int = inject(dep)) -> int:
        return i

    @injector.bind
    async def func2(i: int = inject(dep)) -> int:
        return i

    @injector.bind
    async def func3(i: int = inject(async_dep)) -> int:
        return i

    for res in (
            func(), func(42), func(i=42),
            await func2(), await func2(42), await func2(i=42),
            await func3(), await func3(42), await func3(i=42),
    ):
        assert res == 42


@mark.asyncio
async def test_gathering_of_async_dependencies(injector):
    async def dep1():
        await sleep(1)
        return 1

    async def dep2():
        await sleep(1)
        return 2

    @injector.bind
    async def func(d1: int = inject(dep1), d2: int = inject(dep2)):
        return d1 + d2

    start = perf_counter()
    assert await func() == 3
    end = perf_counter()
    assert end - start < 1.5


@mark.asyncio
async def test_locking_of_async_dependencies(injector):
    var = 0

    async def dep1():
        nonlocal var
        var += 1
        await sleep(1)

    async def dep2(_=inject(dep1)):
        pass

    @injector.bind
    async def func(_1=inject(dep1), _2=inject(dep2)):
        pass

    await func()
    assert var == 1
