from types import FunctionType
from typing import (Any, AsyncContextManager, Callable,
                    Mapping, Type, Union)


def is_async_ctx_mgr(func: Union[Callable, Type]):
    # noinspection PyUnresolvedReferences
    return ((isinstance(func, type) and
             issubclass(func, AsyncContextManager)) or
            (isinstance(func, FunctionType) and
             "_AsyncGeneratorContextManager" in func.__code__.co_names))


Parameters = Mapping[str, Any]  # Parameter are ordered


def args_to_kwargs(parameters: Parameters, *args
                   ) -> Mapping[str, Any]:
    args_mapping = {}
    for arg, param in zip(args, parameters):
        args_mapping[param] = arg
    return args_mapping
