from dataclasses import dataclass

from injector import inject, ContextInjector


def test_dataclass():
    inj = ContextInjector()

    def dep() -> int:
        return 1

    @inj.bind_dataclass
    @dataclass
    class DataClass:
        attr: int = inject(dep)

    assert DataClass().attr == 1
