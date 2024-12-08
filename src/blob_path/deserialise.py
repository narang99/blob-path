from blob_path.backends.azure_blob_storage import AzureBlobPath
from blob_path.backends.local_relative import LocalRelativeBlobPath
from blob_path.backends.s3 import S3BlobPath
from blob_path.core import BlobPath, SerialisedBlobPath

KIND_BY_BACKEND = {
    S3BlobPath.kind: S3BlobPath,
    LocalRelativeBlobPath.kind: LocalRelativeBlobPath,
    AzureBlobPath.kind: AzureBlobPath,
}


def _get_backend(kind: str) -> BlobPath:
    if kind not in KIND_BY_BACKEND:
        raise Exception(
            "failed in deserialising SerialisedBlobPath, "
            + f"unknown kind={kind}\n"
            + f"allowed values={list(KIND_BY_BACKEND.keys())}"
        )
    return KIND_BY_BACKEND[kind]


def deserialise(payload: SerialisedBlobPath) -> BlobPath:
    """The main function to deserialise any serialised representation of a `BlobPath`

    You can pass serialisation of any subclass of `BlobPath` (S3, Azure, LocalRelative) and this would generate the correct class for you

    Args:
        payload: the serialised representation of `BlobPath` object of type `SerialisedBlobPath`

    Returns:
        A fully instantiated `BlobPath` subclass instance

    Raises:
        Exception: If payload["kind"] is not in any of the supported kinds

    Usage:
    ```python
    from blob_path.deserialise import deserialise

    # deserialisation takes a dict payload, which is generally the output of the `serialise` function of the underlying path
    payload = {
        "kind": "blob-store-aws",
        "payload": {
            "bucket": "some-bucket-name",
            "region": "us-east-1",
            "object_key": "hello_world.txt",
        },
    }

    # call deserialise
    deserialised_s3_blob = deserialise(payload)

    from blob_path.backends.s3 import S3BlobPath
    assert isinstance(deserialised_s3_blob, S3BlobPath)


    # test the reserialisation is same as the original payload
    assert deserialised_s3_blob.serialise() == payload
    ```

    You should generally never use the function `deserialise` in your code base. Always create a wrapper around it. This will allow you to create your own `BlobPath` definitions, or override existing ones

    Example:
    ```python
    from blob_path.backends.s3 import S3BlobPath
    import blob_path.deserialise.deserialise

    class MyFancyS3BlobPath(S3BlobPath):
        def __repr__(self):
            return "hehe"


    def deserialise(payload):
        if payload["kind"] == MyFancyS3BlobPath.kind:
            return MyFancyS3BlobPath.deserialise(payload)
        else:
            return blob_path.deserialise.deserialise(payload)
    ```
    """
    backend = _get_backend(payload["kind"])
    return backend.deserialise(payload)



__all__ = ["deserialise"]
