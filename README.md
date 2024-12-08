blob-store is a library providing a simple interface to storing your files in a cloud agnostic fashion  

# Features
- Cloud-agnostic storage of files
- Serialisation + De-serialisation: Allowing you to move your path objects around different processes, making it easy to handle remote file locations
- Easy interactions between different kinds of cloud locations
  - You could run `s3_path.cp(azure_blob_path)` and it would just work

# Installation

Downloading the core library.  
```bash
pip install blob-store
```
Cloud storage providers are provided as extra pip installation dependencies. Currently only AWS S3 and Azure Blob Storage are supported.  
```bash
pip install 'blob-store[aws]'
pip install 'blob-store[azure]'
```

The library is under active development and breaking changes are possible.  

# Usage
The main interface this library provides is `BlobPath`, a data structure which tries to mimics `Path`, but for multiple storage types.  

Example usage
```python
def read_file(p: BlobPath):
  # this is the central method each `BlobPath` exposes
  # it downloads your file from the storage provider and provides a file handle for usage
  with p.open("r") as f:
    print(f.read())

# instantiate a BlobPath which is backed by S3
p = S3BlobPath(bucket, region, key)
read_file(p)
```
Check out the usage [notebook](./docs/usage.ipynb) for detailed usage of the library. The notebook is structured as a tutorial covering all features of the library.  

# Roadmap

- [ ] Add other storage backends
  -  [ ] GCP, Minio
- [ ] Tests
- [ ] Caching support
- [ ] Performance
- [ ] More pathlib functions and parity