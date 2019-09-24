from pytest import raises

from injector import inject
from injector.dependency import Dependency
from injector.errors import (AsyncDependency, DependencyWithFreeParameters,
                             EmptyDependency, InvalidType)


def test_dependency():
    def dependency() -> int:
        return 42

    dep = Dependency(dependency)
    assert repr(dep) == repr(dependency)
    assert hash(dep) == hash(dependency)
    assert dep == Dependency(dependency)
    assert not dep.is_async


def test_async_dependency():
    async def sub_dep():
        pass

    def dep(_=inject(sub_dep)):
        pass

    with raises(AsyncDependency):
        Dependency(dep)


def test_dependency_with_free_parameters():
    def dep(_: int):
        pass

    with raises(DependencyWithFreeParameters):
        inject(dep)

    def dep_with_default(_: int = 0):
        pass

    inject(dep_with_default)


def test_empty_dependency():
    def dep(_=inject()):
        pass

    with raises(EmptyDependency):
        inject(dep)


class Global:
    pass


def test_type_dependency():
    def dep1(_: Global = inject()):
        pass

    def dep2(_: 'Global' = inject()):
        pass

    assert Dependency(dep1).dependencies["_"].func == Global
    assert Dependency(dep2).dependencies["_"].func == Global


def test_invalid_type():
    class Local:
        pass

    def dep(_: 'Local' = inject()):
        pass

    with raises(InvalidType):
        Dependency(dep)
