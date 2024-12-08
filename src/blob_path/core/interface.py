import shutil
from contextlib import contextmanager
from pathlib import Path, PurePath
from typing import Any, Protocol, TypedDict, Union

from typing_extensions import Self


class SerialisedBlobPath(TypedDict):
    """The top level serialised representation of any `BlobPath`.

    Each `BlobPath` type is represented by the `kind` attribute, a `kind` is unique to every `BlobPath`
    `payload` would be the internal representation of the `BlobPath` implementation. Only the implementation would understand the representation and be able to parse it

    `kind` is used to create a kind of discriminated union between different serialised representations
    """

    kind: str
    payload: Any


class DoesNotExist(Exception):
    "Exception raised when a file does not exist to the location pointed by a `BlobPath`"
    pass


StrPurePath = Union[str, PurePath]


class BlobPath(Protocol):
    """An interface representing a file belonging to any of the supporting storage backends.

    This is the main interface provided by the library, any file in any storage (S3, Azure, etc.) can be modelled using this interface  
    Different storage types are simply implementations of this interface and manage the underlying storage's intricacies  


    There are some strict requirements:  
    - Only functionality supported by every supported backend is added in this interface  
    - `BlobPath` needs to be strictly JSON serialisable and deserialisable, this should allow users to pass around their `BlobPath` instances around their services and it should just work  
    - `BlobPath` does not intend to replace `pathlib.Path`, if a file is only stored in the local FS, do not use this class.  
    - It is immutable  

    Usage:  
    ```python
    from blob_path import BlobPath
    from blob_path.deserialise import deserialise

    def f(p: BlobPath):
        # this method triggers a download from the underlying storage for reading
        # we return a simple file object as returned by python builtin `open`
        # this is the main interface to talk to the file in this path
        # many other methods use this method for providing generic implementations
        with p.open("r") as f:
           content = f.read()

        # you can check if the file exists or not
        # this would generally make some kind of metadata fetch from the underlying storage
        print(p.exists())


        serialised = p.serialise()
        newp = deserialise(serialised)
        assert newp == p
    ```
    """

    kind = "BlobPath"
    """`kind` is a globally unique class variable which uniquely identifies a subtype of `BlobPath`

    Each subtype defines its `kind` which should never clash with any other implementation. `kind` is used for serialisation
    """

    @contextmanager
    def open(self, mode: str = "r"):
        """Open the underlying file in the given mode.

        This function mimics the builtin `open` function. It fetches the file from the underlying storage and opens it. Returns a file handle to the downloaded file.  
        If the file is opened in write mode, it is uploaded back to the cloud when the handle is closed.  
        Currently this function can only be opened with a context manager. (you can't manually call `close` right now)  
        If the file is opened using `w` mode, then the file does not need to exist in the underlying storage  

        Args:
            mode: the mode in which the file should be opened. Currently only `a` is not supported

        Returns:
            a file handle where the user can read/write data. Once the context is finished, the file is uploaded to the backend if file was opened in `w` mode

        Raises:
            `blob_path.core.interface.DoesNotExist`: The file does not exist
        """
        raise NotImplementedError

    def exists(self) -> bool:
        """Check if the file exists.

        Returns:
            a boolean based on whether the file exists or not
        """
        ...

    def delete(self) -> bool:
        """Delete the file if it exists.

        How delete happens is based on the underlying storage and is not important. The file might be accessible through other means if the underlying storage keeps some sort of archive (like S3 versioned buckets), but doing an `exists` should return `False` once delete is called, no matter what how the underlying storage works. A read on the file using `open` will raise `DoesNotExist` if a file is deleted.
  
        Returns:
            `True` if the file existed and was deleted, else `False`
        """
        ...

    def serialise(self) -> SerialisedBlobPath:
        """serialise a `BlobPath` to a JSON-able dict which can be passed around

        Generally, if a `BlobPath` is deserialised from some serialised representation, it should be perfectly reproducible. That is two path representations of the same serialisation anywhere (different process, different server, etc.) should point to the same file if it is accessible. This might not always be true (depending on what storage backend you are using), read the documentation of the underlying backend for caveats
        That said, the library tries to follow this requirement diligently, all paths which can be uniquely pointed from anywhere in the world (S3, Azure Blob Store, etc) always follow this.

        Returns:
            `blob_path.core.interface.SerialisedBlobPath`: A JSON-able `dict`
        """
        ...

    @classmethod
    def deserialise(cls, data: SerialisedBlobPath) -> Self:
        """Deserialise a given serialised representation.

        Do not use this method directly in your code, you should use `blob_path.deserialise.deserialise`

        Args:
            data: A `SerialisedBlobPath` whose `kind` should always be equal to `self.kind`

        Returns:
            A new `BlobPath` instance
        """
        ...

    def cp(self, destination: Union["BlobPath", Path]) -> None:
        """Copy file pointed by self to `destination`.

        The generic implementation is pretty simple, it opens both the current file in read mode, the destination in write mode and copies data there.

        Storage backends are free to optimise this call for special cases (like copying from one S3 Path to another without downloading intermediate data)

        Args:
            destination: a `BlobPath` where the data is copied to

        Raises:
            `blob_path.core.interface.DoesNotExist`: The current file does not exist
        """
        with self.open("rb") as fr:
            if isinstance(destination, Path):
                with open(destination, "wb") as fw:
                    shutil.copyfileobj(fr, fw)
            else:
                with destination.open("wb") as fw:
                    shutil.copyfileobj(fr, fw)

    def __eq__(self, value: Any) -> bool:
        """Check if two paths point to the same location.

        No check is done for the underlying file content, only the location is checked for equality.
        This function follows the principle for `serialise/deserialise`. If a location can be pointed uniquely globally, and two paths point to the same location, they would always be equal.
        The library follows this diligently, but check the underlying storage `BlobPath` documentation for caveats if they exist

        Args:
            value: Any object with which equality is tested

        Returns:
            boolean: `True` if the `self` and `value` point to the same location
        """
        ...

    def __truediv__(self, other: StrPurePath) -> "BlobPath":
        """`pathlib.Path` like semantics for `BlobPath`.

        Usage:
        ```python
        >>> def f(base_p: BlobPath) -> BlobPath:
        >>>    relative_path = PurePath("hello") / "world"
        >>>    return base_p / relative_path / "hey.txt"
        ```

        Note that there might not be a concept of "directory" in the underlying storage
        As an example, standard S3 buckets do not have any concept of "directory" (which is why we do not give an `is_dir` function).
        Regardless, this feature might be useful in situations like this:

        ```python
        def avatar_path(users_base_path: BlobPath) -> BlobPath:
            return users_base_path / "avatar.jpg"
        ```

        Separator used to finally generate the path in the underlying storage depends on the conventions of the underlying storage
        As an example, `/` is used for S3

        Many times, the underlying storage would not make any attempt at resolving your paths, it is your responsibility to provide correct paths (without `.`, `..`, etc.)

        Args:
            `other`: An object of type `str` or `PurePath` which is added to the current `BlobPath`

        Returns:
            the newly generated path with the new component added
        """
        ...

    @property
    def parent(self) -> "BlobPath":
        """The logical parent of the path.

        Behavior is consistent with `pathlib.PurePath.parent`. In case of an empty path/root path, the current path is returned as is

        Returns:
            A new `BlobPath` which is the parent of the current path
        """
        ...
