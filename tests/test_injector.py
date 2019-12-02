from pytest import mark

from injector import GlobalInjector, inject


@mark.parametrize("cached, final", [(False, 2), (True, 1)])
def test_bind(cached, final):
    count = 0

    def dep() -> int:
        return 0

    def func(i: int = inject(dep)) -> int:
        nonlocal count
        count += 1
        return i

    inj = GlobalInjector()
    bound = inj.bind(cached=cached)(func)

    assert bound() == 0
    assert count == 1
    assert bound() == 0
    assert count == final
