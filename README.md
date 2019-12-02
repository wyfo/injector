# Injector

Typed dependency injection, and that's all.
This Readme has been written in a few minutes, it would be completed and improved later.

# Example
```python
from injector import GlobalInjector, inject

injector = GlobalInjector()

def get_attr():
    ...

class Obj:
    def __init__(self, attr=inject()):
        self.attr = attr
        
def compute_sub_dep():
    ...
        
async def compute_dep(other_dep=inject(compute_sub_dep)) -> int:
    ...


@injector.bind
def bound_func(arg1: str, dep1: int = inject(compute_dep), dep2: Obj = inject())
    ...

bound_func("...")
bound_func(arg1="...")
bound_func("...", dep2=Obj(...))
```

# Features
- Supports sync and async functions, sync and async context managers as well
- Context managers exit are registered into injector (which can be used as a context manager itself) and called with its exit
- Dependency computed by injection must have no free parameters. Bound functions can have free parameters; injected parameters are just handled like default value and can be overriden just by calling the function with them (very easy to test!) 
- Dependecies computed are cached by the injectors. Several injectors can be used (notably to manage context managers), but they can share the same cache if needed. Two default caches are offered : `DictCache` which is not asyncio-context-aware and `ContextCache` which is.

# TODO
- Complete tests (only 95% since the last refacto)
- documentation