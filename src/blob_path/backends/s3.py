"""S3 backend for ``blob_path.core.interface.BlobPath``.

The main class this module provides is ``S3BlobPath``, the main abstraction for talking to S3  
"""

import functools
from contextlib import contextmanager
from pathlib import PurePath
from typing import IO, Any, final

from pydantic import BaseModel
from typing_extensions import Self

from blob_path.core import BlobPath, SerialisedBlobPath
from blob_path.core.interface import DoesNotExist, StrPurePath
from blob_path.core.open_ import generic_open
from blob_path.core.presigned import Presigned
from blob_path.implicit import get_implicit_var, prefix_var


class Payload(BaseModel):
    "The serialised representation for the payload of an ``blob_path.backends.s3.S3BlobPath``."
    bucket: str
    region: str
    object_key: list[str]


IMPLICIT_GEN_BUCKET = prefix_var("GEN_S3_BUCKET")
IMPLICIT_GEN_REGION = prefix_var("GEN_S3_REGION")


@functools.lru_cache(maxsize=1)
def _s3_session():
    import boto3.session
    return boto3.session.Session()


class S3BlobPath(BlobPath, Presigned):
    """``BlobPath`` modeling AWS S3.

    Properties:  

    * Globally Unique: True  

    An S3 blob path is located by three parameters: bucket, object_key and a region  
    You can pass this path around anywhere (any server, lambda, container, etc.) and the correct S3 location will always be uniquely identified (``__eq__``, ``serialise`` and ``deserialise`` also behaves sanely here, that is, no matter the location, same serialised representations point to the same location globally and uniquely)  

    Implements: ``BlobPath``, ``Presigned``

    Apart from the interface exposed by ``BlobPath`` and ``Presigned``, this class provides some extension points users can use to tweak how communication with S3 is done (you should be wholly able to tweak all performance and security params). Its advised to only override the methods below for extending the functionality of a path  
    Methods that are safe to inherit and override: ``download``, ``upload`` and ``session``  

    Usage:  

    .. code-block:: python

        from blob_path.backends.s3 import S3BlobPath

        # the generic way is to use this constructor for defining your path
        p = S3BlobPath(bucket, region, key)
        with p.open("r") as f:
           print(f.read())
        
        # the class also provides a factory `create_default` which can be used as follows:
        # `bucket` and `region` are injected using implicit variables
        p = S3BlobPath.create_default(PurePath("hello") / "world.txt")
        
        # generate a pre-signed url
        url = p.presigned_url()

    This class does not use any implicit variables other than for providing the `create_default` factory function  
    """

    kind = "blob-path-aws"

    def __init__(self, bucket: str, region: str, object_key: PurePath) -> None:
        """Constructor for creating an S3BlobPath.

        Args:
            bucket: S3 bucket name
            region: The region identifier for AWS, like "ap-south-1"
            object_key: A PurePath representing a key in S3 bucket
        """
        self._bucket = bucket
        self._region = region
        self._object_key = object_key

    @property
    def bucket(self) -> str:
        "bucket getter, useful while extending this class"
        return self._bucket

    @property
    def region(self) -> str:
        "region getter, useful while extending this class"
        return self._region

    @property
    def object_key(self) -> PurePath:
        "object_key getter, useful while extending this class"
        return self._object_key

    def _s3_object_key(self) -> str:
        return "/".join(self.object_key.parts)

    def presigned_url(self, expiry_seconds: int) -> str:
        with _wrap_does_not_exist(f"s3-blob {self} does not exist"):
            return self._s3_client().generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket, "Key": str(self._s3_object_key())},
                ExpiresIn=expiry_seconds,
            )

    def exists(self) -> bool:
        """check if the path point to a valid existing object in S3.

        Returns:  
            A boolean representing whether the file exists or not  
        """
        try:
            self._head_object()
            return True
        except DoesNotExist:
            return False

    def _head_object(self):
        import botocore.exceptions
        try:
            client = self._s3_client()
            return client.head_object(Bucket=self.bucket, Key=self._s3_object_key())
        except botocore.exceptions.ClientError as ex:
            if "Error" not in ex.response or "Code" not in ex.response["Error"]:
                raise Exception(
                    "developer exception: unidentified boto3 ClientError response body for `exists`"
                    + f"response={ex.response}"
                ) from ex
            if ex.response["Error"]["Code"] == "404":
                raise DoesNotExist
            else:
                raise ex

    def delete(self) -> bool:
        if self.exists():
            self._s3_client().delete_object(
                Bucket=self.bucket, Key=self._s3_object_key()
            )
            return True
        else:
            return False

    @contextmanager
    def open(self, mode: str = "r"):
        yield from generic_open(self.upload, self.download, mode)

    def download(self, handle: IO[bytes]) -> None:
        """Download data for the given S3 path and write it to the provided binary handle.

        Users can extend this method if they want to change how the download is done  
        This is recommended if you want to tweak your performance etc.  

        Args:  
            handle: An IO byte stream where the downloaded content should be written to  

        Raises:  
            DoesNotExist: exception when the path does not point to any object in S3  
        """
        with _wrap_does_not_exist(f"s3-blob {self} does not exist"):
            s3 = self._s3_client()
            s3.download_fileobj(self.bucket, self._s3_object_key(), handle)

    def upload(self, handle: IO[bytes]):
        """Upload data produced by reading from the given Binary file handle to S3.

        Users can extend this method if they want to change how the upload is done  
        This is recommended if you want to tweak your performance etc.  

        Args:  
            handle: An IO byte stream from where you should read content and upload to S3  
        """
        self._s3_client().upload_fileobj(handle, self.bucket, self._s3_object_key())

    @classmethod
    def create_default(cls, p: PurePath) -> Self:
        """Create a new S3BlobPath, the bucket and region would be injected from implicit variables.

        Args:  
            p: A PurePath which represents the "object_key" that you want to use  

        Returns:  
            An `S3BlobPath`  

        **Implicit variables:**
            * ``bucket``: ``IMPLICIT_BLOB_PATH_GEN_S3_BUCKET``
            * ``region``: ``IMPLICIT_BLOB_PATH_GEN_S3_REGION``

        """
        bucket = get_implicit_var(IMPLICIT_GEN_BUCKET)
        region = get_implicit_var(IMPLICIT_GEN_REGION)
        return cls(bucket, region, p)

    @classmethod
    def session(cls) -> "boto3.session.Session":
        """Get a boto3 session to use for BlobPath.  
        
        Override this if you want to change how your session is created  
        """
        return _s3_session()

    @final
    def serialise(self) -> SerialisedBlobPath:
        payload = Payload(
            bucket=self.bucket,
            region=self.region,
            object_key=list(self.object_key.parts),
        )
        return SerialisedBlobPath(
            kind=self.kind, payload=payload.model_dump(mode="json")
        )

    @final
    @classmethod
    def deserialise(cls, data: SerialisedBlobPath) -> Self:
        p = Payload.model_validate(data["payload"])
        return cls(p.bucket, p.region, PurePath(*p.object_key))

    def _s3_client(self):
        return self.session().client("s3", region_name=self.region)

    def __repr__(self) -> str:
        return f"kind={self.kind} bucket={self.bucket} region={self.region} object_key={self.object_key}"

    def cp(self, destination: "BlobPath") -> None:
        """Copy the content of the current file to the destination.

        This method overrides the default implementation to provide some performance benefits. If the destination is `S3BlobPath`, direct copying is done without downloading the object to the local system  
        """
        if not isinstance(destination, S3BlobPath):
            return super().cp(destination)
        session = destination.session()
        s3 = session.client("s3", destination.region)
        s3.copy_object(
            Bucket=destination.bucket,
            Key=destination._s3_object_key(),
            CopySource={"Bucket": self.bucket, "Key": self._s3_object_key()},
        )

    def __eq__(self, value: Any) -> bool:
        """Check if current blob path is equal to the `value`.

        The equality check does not check the underlying file content. It simply checks whether these two paths point to the same location  
        For S3, this equality check is always correct. Two paths in different environments would always point to the same S3 object if tyhey are equal  
        """
        if not isinstance(value, S3BlobPath):
            return False
        return (
            self.bucket == value.bucket
            and self.region == value.region
            and self.object_key == value.object_key
        )

    def __truediv__(self, other: StrPurePath) -> "S3BlobPath":
        new_key = self.object_key / other
        p = S3BlobPath(self.bucket, self.region, new_key)
        return p

    @property
    def parent(self) -> "S3BlobPath":
        new_key = self.object_key.parent
        return S3BlobPath(self.bucket, self.region, new_key)


@contextmanager
def _wrap_does_not_exist(does_not_exist_msg):
    import botocore.exceptions
    try:
        yield
    except botocore.exceptions.ClientError as ex:
        if "Error" not in ex.response or "Code" not in ex.response["Error"]:
            raise Exception(
                "developer exception: unidentified boto3 ClientError response body for `exists`"
                + f"response={ex.response}"
            ) from ex
        if ex.response["Error"]["Code"] == "404":
            raise DoesNotExist(does_not_exist_msg) from ex
        else:
            raise ex
