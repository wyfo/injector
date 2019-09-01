from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from inspect import Parameter, signature
from typing import (Any, Callable, ContextManager, Dict, Mapping, Optional,
                    Tuple, Type, TypeVar, Union, cast)

from mypy.ipc import TracebackType

Injected = TypeVar("Injected")
Func = Union[Type[Injected],
             Callable[..., ContextManager[Injected]],
             Callable[..., Injected]]


@dataclass
class Dependency:
    func: Func


def inject(func: Func) -> Injected:
    return cast(Injected, Dependency(func))


Exit = Callable[[Optional[Type[BaseException]],
                 Optional[BaseException],
                 Optional[TracebackType]], Optional[bool]]
Resolved = TypeVar("Resolved")


class Unresolved(Exception):
    def __init__(self, name: str, func: Callable):
        self.name = name
        self.func = func


class MergeParameterError(Exception):
    def __init__(self, param1: Parameter, param2: Parameter):
        self.param1 = param1
        self.param2 = param2


class Injector(ABC):
    _prefix = "_"

    @abstractmethod
    def __contains__(self, item: str):
        ...

    @abstractmethod
    def __getitem__(self, item: str):
        ...

    @abstractmethod
    def __setitem__(self, key: str, value: Any):
        ...

    def _register_exit(self, exit_: Exit):
        pass

    @staticmethod
    @abstractmethod
    def merge_parameters(param1: Parameter, param2: Parameter) -> Parameter:
        assert param1.name == param2.name
        if param1.annotation != param2.annotation:
            raise MergeParameterError(param1, param2)
        if param1.default is Parameter.empty:
            return param2
        elif param2.default is Parameter.empty:
            return param1
        elif param1.default == param2.default:
            return param1
        else:
            raise MergeParameterError(param1, param2)

    def _add_param(self, params: Dict[str, Parameter], param: Parameter):
        if param.name not in params:
            params[param.name] = param
        else:
            params[param.name] = self.merge_parameters(params[param.name],
                                                       param)

    def resolve(self, func: Callable[..., Resolved]
                ) -> Tuple[Callable[[], Resolved], Mapping[str, Parameter]]:
        remaining_params: Dict[str, Parameter] = {}
        parameters = signature(func).parameters
        resolved = {}
        for param in parameters.values():
            if isinstance(param.default, Dependency):
                dep, params = self.resolve(param.default.func)
                resolved[param.name] = dep
                for p in params.values():
                    self._add_param(remaining_params, p)
            else:
                self._add_param(remaining_params, param)

        # noinspection PyShadowingNames
        def wrapper() -> Resolved:
            kwargs = {}
            for name, param in parameters.items():
                if name in self:
                    kwargs[name] = self[name]
                elif name in resolved:
                    if self._prefix + name in self:
                        kwargs[name] = self[self._prefix + name]
                    else:
                        tmp = resolved[name]()
                        if isinstance(tmp, ContextManager):
                            self._register_exit(tmp.__exit__)
                            tmp = tmp.__enter__()
                        self[self._prefix + name] = tmp
                        kwargs[name] = tmp
                else:
                    raise Unresolved(name, func)
            return func(**kwargs)

        return wrapper, remaining_params
