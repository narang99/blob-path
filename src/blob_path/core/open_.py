from typing import IO, Callable, Generator
from uuid import uuid4

from blob_path.tmpdir import get_tmp_dir


def generic_open(
    upload_fn: Callable[[IO[bytes]], None],
    download_fn: Callable[[IO[bytes]], None],
    mode: str,
) -> Generator:
    tmp_path = get_tmp_dir() / str(uuid4())
    if "r" in mode:
        with open(tmp_path, "wb") as tmpf:
            download_fn(tmpf)
    with open(tmp_path, mode) as f:
        yield f
    if "w" in mode:
        with open(tmp_path, "rb") as tmpf:
            upload_fn(tmpf)
    tmp_path.unlink()
