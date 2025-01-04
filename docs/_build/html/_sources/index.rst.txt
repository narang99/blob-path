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

Motivation
==========
The library is meant for developers maintaining services in multiple clouds (or on-premise).
Storing files in a way that works across clouds always generally requires developers to come up with some abstraction. The easiest way to do it is to create interfaces which would abstract away certain abstractions (like upload, download, etc.). This becomes slightly cumbersome when you want to move your file paths around in different services across HTTP calls. Now you need to share some implicit environment between these services (like which S3 bucket to use), to reliably do any serialisation/de-serialisation operations on your file paths.  
We provide a central interface ``BlobPath``, it contains all abstracted functionality for working with different clouds, while giving an intuitive interface (bits of which are copied from ``pathlib``). You can throw around this abstraction everywhere and it should just work.  

Installation
============

Downloading the core library.  

.. code-block:: shell

  pip install blob-path

Cloud storage providers are provided as extra pip installation dependencies. Currently only AWS S3 and Azure Blob Storage are supported.  

.. code-block:: shell

  pip install 'blob-path[aws]'
  pip install 'blob-path[azure]'


Usage
=====

Basic example usage

.. code-block:: python

  from blob_path.backends.s3 import S3BlobPath
  from pathlib import PurePath

  bucket_name = "my-bucket"
  object_key = PurePath("hello_world.txt")
  region = "us-east-1"
  blob_path = S3BlobPath(bucket_name, region, object_key)

  # check if the file exists
  blob_path.exists()

  # read the file
  with blob_path.open("rb") as f:
      # a file handle is returned here, just like `open`
      print(f.read())

.. toctree::
   :maxdepth: 1

   Basic Usage <notebooks/00_usage.ipynb>

Code Documentation
==================

Core Interfaces
~~~~~~~~~~~~~~~

.. toctree::
   :maxdepth: 1

   code/core.rst

Storage Backends
~~~~~~~~~~~~~~~~

The documentation here is useful to find all the methods supported by your storage backend, their implicit variables, etc.

.. toctree::
   :maxdepth: 1

   code/s3.rst
   code/azure.rst
   code/local_relative.rst

Indices and tables
==================
* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
