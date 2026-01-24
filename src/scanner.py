from pathlib import Path
from typing import Iterable


def scan_directory(root: Path) -> Iterable[Path]:
    """
    Scan a root directory and yield candidate file or folder paths.
    """
    if not root.exists() or not root.is_dir():
        return

    for path in root.rglob("*"):
        yield path


def is_git_repo(folder: Path) -> bool:
    pass


def get_file_size(path: Path) -> int:
    pass


def is_stale(path: Path, days_old: int) -> bool:
    pass


def should_exclude(path: Path, exclude_patterns: Iterable[str]) -> bool:
    pass
