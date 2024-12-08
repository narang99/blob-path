from contextlib import contextmanager
from pathlib import Path, PurePath
from typing import Any

from pydantic import BaseModel
from typing_extensions import Generator, Self

from blob_path.core import BlobPath, SerialisedBlobPath
from blob_path.core.interface import StrPurePath
from blob_path.implicit import get_implicit_var, prefix_var

BASE_VAR = prefix_var("LOCAL_RELATIVE_BASE_DIR")


class Payload(BaseModel):
    relpath_parts: list[str]


class LocalRelativeBlobPath(BlobPath):
    """BlobPath modeling a file which is always relative to a root directory that is injected using implicit variables.

    Properties:  
    - Globally Unique: False  

    The path is simply composed of `relpath`, a `pathlib.PurePath` which is the relative path from the root directory  

    Usage:  
    ```python
    relpath = PurePath("hello") / "world.txt"
    p = LocalRelativeBlobPath(relpath)
    with p.open("r") as f:
       print(f.read())
    ```

    The path object is a really simple wrapper around `pathlib.PurePath` and `pathlib.Path`.  
    The main use-case of this is to provide an API compatible with other storages.  
    This would enable you to seamlessly use your current FS to do file operations.  

    The path uses an implicit variable `IMPLICIT_BLOB_PATH_LOCAL_RELATIVE_BASE_DIR` which injects the root directory to use for these paths. This variable is required to be present if you want to use this path  
    Injecting this variable makes this path a bit more flexible for using between different processes.  

    - Two docker containers mounting the same volume at different mount points can transparently point to file paths correctly by simply changing their `IMPLICIT_BLOB_PATH_LOCAL_RELATIVE_BASE_DIR` variables  
    - Same for two servers mounted on an NFS  

    Providing relative paths like this makes it easy to access file paths across different processes assuming they can access the file system. There is also a footgun here though, you need to make sure that the environment is correctly configured for every process using this path. In terms of the concepts of `BlobPath`, this path is not "Globally Unique"  
    """

    kind = "blob-store-local-relative"

    def __init__(self, relpath: PurePath) -> None:
        self._relpath = relpath

    @property
    def relpath(self) -> PurePath:
        return self._relpath

    @contextmanager
    def open(self, mode: str = "r") -> Generator:
        p = self._p()
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, mode) as f:
            yield f

    def serialise(self) -> SerialisedBlobPath:
        """Serialise the BlobPath to JSON-able dict.

        The serialisation of LocalRelativeBlobPath is not Globally Unique  
        Due to the path using implicit variables to determine the root directory, two `LocalRelativeBlobPath` path objects might point to different files when their serialisation are the same  
        """
        p = Payload(relpath_parts=list(self._relpath.parts))
        return SerialisedBlobPath(kind=self.kind, payload=p.model_dump(mode="json"))

    def exists(self) -> bool:
        return (self._p()).exists()

    def delete(self) -> bool:
        if self.exists():
            self._p().unlink()
            return True
        else:
            return False

    @classmethod
    def deserialise(cls, data: SerialisedBlobPath) -> Self:
        p = Payload.model_validate(data["payload"])
        return cls(PurePath(*p.relpath_parts))

    def __repr__(self) -> str:
        return (
            f"kind={self.kind} relative_path={self._relpath} ImplicitVars=[{BASE_VAR}]"
        )

    def _p(self) -> Path:
        return _get_implicit_base_path() / self._relpath

    def __eq__(self, value: Any) -> bool:
        if not isinstance(value, LocalRelativeBlobPath):
            return False
        return self.relpath == value.relpath

    @property
    def parent(self) -> "LocalRelativeBlobPath":
        return LocalRelativeBlobPath(self.relpath.parent)

    def __truediv__(self, other: StrPurePath) -> "LocalRelativeBlobPath":
        return LocalRelativeBlobPath(self.relpath / other)


def _get_implicit_base_path() -> Path:
    base_path = Path(get_implicit_var(BASE_VAR))
    base_path.mkdir(exist_ok=True, parents=True)
    return base_path
