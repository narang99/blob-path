from pathlib import Path

from blob_path.implicit import get_implicit_var_or_default, prefix_var


def get_tmp_dir() -> Path:
    return Path(
        get_implicit_var_or_default(
            prefix_var("TMPDIR"),
            str(Path.home() / "tmp"),
        )
    )
