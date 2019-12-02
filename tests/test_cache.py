from unittest.mock import MagicMock

from injector.cache import DictCache


def test_cache():
    cache = DictCache()
    dep = MagicMock()
    assert cache.lock(dep) == cache.lock(dep)


