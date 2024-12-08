"""Module to interact with implicit variables"""

import os
from typing import Callable, Optional

VarName = str
ImplicitVarProvider = Callable[[VarName], Optional[str]]


def _default_env_provider(var: VarName) -> Optional[str]:
    return os.environ.get(var)


_PROVIDER = _default_env_provider


def register_implicit_variable_provider(provider: ImplicitVarProvider):
    """a custom function to fetch the implicit arguments of blob paths

    This is NOT THREAD SAFE. It should always be called before you start using BlobPath
    Preferable at the top of your main module
    """
    global _PROVIDER
    _PROVIDER = provider


def get_implicit_var(var: VarName) -> str:
    result = _PROVIDER(var)
    if result is None:
        raise Exception(
            "tried fetching implicit variable from environment "
            + f"but the var os.environ['{var}'] does not exist"
        )
    return result


def get_implicit_var_or_default(var: VarName, default: str) -> str:
    result = _PROVIDER(var)
    if result is None:
        return default
    return result


def prefix_var(var: VarName) -> VarName:
    return f"IMPLICIT_BLOB_PATH_{var}"


__all__ = ["register_implicit_variable_provider"]
