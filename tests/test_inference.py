from contextlib import asynccontextmanager, contextmanager
from typing import AsyncIterator, Iterator

from injector import inject


class User:
    pass


def func() -> str:
    return ""


@contextmanager
def ctx_mgr() -> Iterator[str]:
    yield ""


async def afunc() -> str:
    return ""


@asynccontextmanager
async def actx_mgr() -> AsyncIterator[str]:
    yield ""


# check editor and mypy inference in these tests
test0 = inject(User)
test0 = 0
test1 = inject(func)
test1 = 0
test2 = inject(ctx_mgr)
test2 = 0
test3 = inject(afunc)
test3 = 0
test4 = inject(actx_mgr)
test4 = 0
# We can see that MyPy is able to infer type of injected func without
# annotation, but Pycharm isn't
