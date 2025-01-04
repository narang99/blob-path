====================
Core Data Structures
====================


Core Interfaces
===============


The library currently provides two core interfaces:

* ``BlobPath``: Represent a storage type agnostic path
* ``Presigned``: Represent a ``BlobPath`` which is also capable of generating a pre-signed URL

The core interfaces are all Python ``typing.Protocol`` interfaces. This makes it very easy to compose this interfaces and get type guarantees. You can use ``Union[BlobPath, Presigned]`` to denote types which always implement a `Presigned` interface  

.. autoclass:: blob_path.core::BlobPath
   :members:

.. autoclass:: blob_path.core::Presigned
   :members:


Serialisation
=============

.. autoclass:: blob_path.core::SerialisedBlobPath


Exceptions
==========

.. autoclass:: blob_path.core::DoesNotExist
