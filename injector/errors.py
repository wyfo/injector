from __future__ import annotations

from typing import Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from injector.injector import Injector


class InjectionError(Exception):
    def __init__(self, func: Callable):
        self.func = func


class AsyncDependency(InjectionError):
    pass


class DependencyWithFreeParameters(InjectionError):
    pass


class EmptyDependency(InjectionError):
    pass


class InvalidType(InjectionError):
    def __init__(self, func: Callable, error: NameError):
        super().__init__(func)
        self.error = error


class AsyncError(InjectionError):
    def __init__(self, func: Callable, injector: Injector):
        super().__init__(func)
        self.injector = injector
