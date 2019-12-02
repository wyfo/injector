from __future__ import annotations

from typing import Callable, TYPE_CHECKING

from injector.exiter import Exiter

if TYPE_CHECKING:
    pass


class InjectionError(Exception):
    def __init__(self, func: Callable):
        self.func = func


class AsyncDependency(InjectionError):
    pass


class Uncachable(InjectionError):
    pass


class EmptyDependency(InjectionError):
    pass


class InvalidType(InjectionError):
    def __init__(self, func: Callable, error: NameError):
        super().__init__(func)
        self.error = error


class ExitError(InjectionError):
    def __init__(self, func: Callable, exiter: Exiter):
        super().__init__(func)
        self.exiter = exiter
