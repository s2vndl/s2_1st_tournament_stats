import os
from pathlib import Path


def get_project_root() -> str:
    project_root = None
    path = Path(os.getcwd())
    while project_root is None:
        if path == Path("/"):
            raise RuntimeError(f"Failed to find project root. Started in cwd: {os.getcwd()}")
        if path.joinpath("pyproject.toml").exists():
            project_root = path
        else:
            path = path.parent
    return os.path.realpath(path)
