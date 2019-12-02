from __future__ import annotations

from abc import ABC
from asyncio import Lock
from collections import defaultdict
from contextvars import ContextVar
from typing import (Any, Dict,
                    Iterator, Mapping, MutableMapping, TYPE_CHECKING)

if TYPE_CHECKING:
    from injector.dependency import Dependency


class Cache(ABC, MutableMapping["Dependency", Any]):
    def __init__(self):
        self._lock: Mapping[Dependency, Lock] = defaultdict(Lock)

    def lock(self, dep: Dependency) -> Lock:
        return self._lock[dep]


class DictCache(Dict["Dependency", Any], Cache):
    def __init__(self):
        dict.__init__(self)
        Cache.__init__(self)


default_context_cache: ContextVar[Dict["Dependency", Any]] = \
    ContextVar("default_context_cache")
default_context_cache.set({})


class ContextCache(Cache):
    def __init__(self, ctx_var: ContextVar[Dict["Dependency", Any]]
    = default_context_cache):  # noqa
        super().__init__()
        self.ctx_var = ctx_var

    @property
    def _dict(self) -> Dict[Dependency, Any]:
        return self.ctx_var.get()

    def __setitem__(self, key: Dependency, value) -> None:
        self._dict[key] = value

    def __delitem__(self, key: Dependency) -> None:
        del self._dict[key]

    def __getitem__(self, key: Dependency):
        return self._dict[key]

    def __len__(self) -> int:
        return len(self._dict)

    def __iter__(self) -> Iterator[Dependency]:
        return iter(self._dict)
