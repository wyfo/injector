from typing import Callable

from injector.dependency import Dependency
from injector.injector import Injector


class Bound(Dependency):
    def __init__(self, func: Callable, injector: Injector, cached: bool):
        super().__init__(func)
        self.injector = injector
        self._cached = cached

    @property
    def cached(self) -> bool:
        return self._cached

    def __call__(self, *args, **kwargs):
        return self.call(self.injector, *args, **kwargs)
