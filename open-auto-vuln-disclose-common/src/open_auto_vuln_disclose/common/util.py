from typing import Callable, Any


def callable_not_implemented_exception(message: str) -> Callable[[...], Any]:
    def _callable_not_implemented_exception(*args, **kwargs):
        raise NotImplementedError(message)

    return _callable_not_implemented_exception
