import shutil
from pathlib import Path
from typing import Union

from blob_path.core import BlobPath


def cp(src: Union[BlobPath, Path], dest: Union[BlobPath, Path]) -> None:
    """Copy `src` to `dest`, a shortcut to handle `Path` along with `blob_path.core.interface.BlobPath` objects  

    You could use `blob_path.core.interface.BlobPath.cp` directly (this shortcut does that), but they don't handle the case where both args can be `Union[Path, BlobPath]`, this is just a convenient function
    """
    if isinstance(src, Path):
        if isinstance(dest, Path):
            shutil.copy(src, dest)
        else:
            with dest.open("wb") as fw:
                with open(src, "rb") as fr:
                    shutil.copyfileobj(fr, fw)
    else:
        src.cp(dest)
