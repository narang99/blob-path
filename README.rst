=========
blob-path
=========

A library providing a simple interface to storing your files in a cloud agnostic fashion  

Features
========
* Cloud-agnostic storage of files
* Serialisation + De-serialisation: Allowing you to move your path objects around different processes, making it easy to handle remote file locations
* Easy interactions between different kinds of cloud locations

  * You could run ``s3_path.cp(azure_blob_path)`` and it would just work

Installation
============

Downloading the core library.  

.. code-block:: shell

  pip install blob-path

Cloud storage providers are provided as extra pip installation dependencies. Currently only AWS S3 and Azure Blob Storage are supported.  

.. code-block:: shell

  pip install 'blob-path[aws]'
  pip install 'blob-path[azure]'

The library is under active development and breaking changes are possible.  

Usage
=====
The main interface this library provides is `BlobPath`, a data structure which tries to mimics `Path`, but for multiple storage types.  

Example usage

.. code-block:: python

  from blob_path.core import BlobPath
  from blob_path.backends.s3 import S3BlobPath
  
  def read_file(p: BlobPath):
    # this is the central method each `BlobPath` exposes
    # it downloads your file from the storage provider and provides a file handle for usage
    with p.open("r") as f:
      print(f.read())

  # instantiate a BlobPath which is backed by S3
  p = S3BlobPath(bucket, region, key)
  read_file(p)

Check out the :doc:`/docs/notebooks/00_usage.ipynb` for detailed usage of the library. The notebook is structured as a tutorial covering all features of the library.  

Roadmap
=======

* Add other storage backends (GCP, Minio)
* Tests
* Caching support
* Performance
* More pathlib functions and parity
