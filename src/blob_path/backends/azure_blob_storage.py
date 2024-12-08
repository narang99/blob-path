from contextlib import contextmanager
from pathlib import PurePath
from typing import IO, Any, Generator

from azure.storage.blob import BlobServiceClient
from pydantic import BaseModel
from typing_extensions import Self

from blob_path.core import BlobPath, SerialisedBlobPath
from blob_path.core.interface import StrPurePath
from blob_path.core.open_ import generic_open
from blob_path.implicit import get_implicit_var, prefix_var


class Payload(BaseModel):
    storage_account: str
    container: str
    name: list[str]


IMPLICIT_GEN_STORAGE_ACCOUNT = prefix_var("GEN_AZURE_BLOB_STORAGE_ACCOUNT")
IMPLICIT_GEN_CONTAINER = prefix_var("GEN_AZURE_BLOB_CONTAINER")


class AzureBlobPath(BlobPath):
    """BlobPath modeling Azure Blob Storage.  

    Properties:  
    - Globally Unique: True  

    An AzureBlobPath is located by three parameters: storage_account, container and a name  
    You can pass this path around anywhere (any server, lambda, container, etc.) and the correct Azure Blob Store location will always be uniquely identified (`__eq__`, `serialise` and `deserialise` also behaves sanely here, that is, no matter the location, same serialised representations point to the same location globally and uniquely)  

    Implements: `blob_path.core.interface.BlobPath`  

    Apart from the interface exposed by `BlobPath`, this class provides some extension points users can use to tweak how communication with Azure is done (you should be wholly able to tweak all performance and security params). Its advised to only override the methods below for extending the functionality of a path  
    Methods that are safe to inherit and override: `download`, `upload` and `credential`  

    This class does not use any implicit variables other than for providing the `create_default` factory function  
    """

    kind = "blob-store-azure"

    def __init__(self, storage_account: str, container: str, name: PurePath) -> None:
        self._storage_account = storage_account
        self._container = container
        self._name = name

    @property
    def storage_account(self) -> str:
        "getter for storage account"
        return self._storage_account

    @property
    def container(self) -> str:
        "getter for container"
        return self._container

    @property
    def name(self) -> PurePath:
        "getter for object path or name"
        return self._name

    def credential(self):
        """Generate the credential used for authenticating with azure.

        Override this method if you want to change how your credentials are located  
        """
        from azure.identity import DefaultAzureCredential

        default_credential = DefaultAzureCredential()
        return default_credential

    def _get_service_client(self):
        account_url = f"https://{self.storage_account}.blob.core.windows.net"
        return BlobServiceClient(account_url, credential=self.credential())

    def _blob_path(self) -> str:
        return "/".join(self.name.parts)

    def _get_blob_client(self):
        return self._get_service_client().get_blob_client(
            self.container, self._blob_path()
        )

    def exists(self) -> bool:
        return self._get_blob_client().exists()

    def delete(self) -> bool:
        if self.exists():
            self._get_blob_client().delete_blob()
            return True
        else:
            return False

    @contextmanager
    def open(self, mode: str = "r") -> Generator:
        yield from generic_open(self.upload, self.download, mode)

    def upload(self, handle: IO[bytes]) -> None:
        """Upload data to the given Azure Blob Store path.

        Users can extend this method if they want to change how the download is done  
        This is recommended if you want to tweak your performance etc.  
        """
        self._get_blob_client().upload_blob(handle)

    def download(self, handle: IO[bytes]):
        """Download data for the given Azure Blob Store path and write it to the provided binary handle.

        Users can extend this method if they want to change how the download is done  
        This is recommended if you want to tweak your performance etc.  
        """
        client = self._get_service_client().get_container_client(self.container)
        client.download_blob(self._blob_path()).readinto(handle)

    def serialise(self) -> SerialisedBlobPath:
        payload = Payload(
            storage_account=self.storage_account,
            container=self.container,
            name=list(self.name.parts),
        )
        return SerialisedBlobPath(
            kind=self.kind, payload=payload.model_dump(mode="json")
        )

    @classmethod
    def deserialise(cls, data: SerialisedBlobPath) -> Self:
        p = Payload.model_validate(data["payload"])
        return cls(p.storage_account, p.container, PurePath(*p.name))

    @classmethod
    def create_default(cls, p: PurePath) -> Self:
        """Create a new `AzureBlobPath`, the container and storage_account would be injected from implicit variables.

        Implicit variables:  
            storage_account: IMPLICIT_BLOB_PATH_GEN_AZURE_BLOB_STORAGE_ACCOUNT  
            container: IMPLICIT_BLOB_PATH_GEN_AZURE_BLOB_CONTAINER  

        Args:  
            p: A PurePath which represents the "object_key" that you want to use  

        Returns:  
            An `AzureBlobPath`  
        """
        storage_account = get_implicit_var(IMPLICIT_GEN_STORAGE_ACCOUNT)
        container = get_implicit_var(IMPLICIT_GEN_CONTAINER)
        return cls(storage_account, container, p)

    def __repr__(self) -> str:
        return f"kind={self.kind} storage_account={self.storage_account} container={self.container} name={self.name}"

    def __eq__(self, value: Any) -> bool:
        """Check if current blob path is equal to the `value`.

        The equality check does not check the underlying file content. It simply checks whether these two paths point to the same location  
        For Azure, this equality check is always correct. Two paths in different environments would always point to the same Azure object if they are equal  
        """
        if not isinstance(value, AzureBlobPath):
            return False
        return (
            self.container == value.container
            and self.storage_account == value.storage_account
            and self.name == value.name
        )

    @property
    def parent(self) -> "AzureBlobPath":
        new_key = self.name.parent
        return AzureBlobPath(self.storage_account, self.container, new_key)

    def __truediv__(self, other: StrPurePath) -> "AzureBlobPath":
        new_key = self.name / other
        return AzureBlobPath(self.storage_account, self.container, new_key)
