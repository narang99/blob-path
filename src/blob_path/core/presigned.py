from typing import Protocol


class Presigned(Protocol):
    """Interface for `BlobPath` that provide pre-signed URLs.

    A pre-signed URL is an HTTP URL which allows a user to download the content of a file using a normal HTTP GET request.
    """

    def presigned_url(self, expiry_seconds: int) -> str:
        """Generate a pre-signed URL for the underlying file.

        Users should not assume the structure of the pre-signed URL (since this can change between different storage backends).

        Args:
            expiry_seconds: Seconds after which the URL might expire. This is optional behavior. A subclass might ignore `expiry_seconds` and provide URLs that might never expire. Read the subclasses documentation for caveats

        Returns:
            A URL where an HTTP GET would download a file

        Raises:
            `blob_path.core.interface.DoesNotExist`: Raised if the file does not exist
        """
        ...
