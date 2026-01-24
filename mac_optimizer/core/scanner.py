"""File system scanning for Mac-Storage-Optimizer.

Skeleton only; implement traversal and metadata extraction later.
"""

from pathlib import Path


class FileScanner:
    """Locate candidate files and detect Git repositories."""

    def scan_directory(self, root: Path) -> list[Path]:
        """Scan a directory tree and collect candidate file paths.

        Requirements:
        - Must recursively walk the directory tree under `root`.
        - Must skip hidden files/folders (names starting with ".").
        - Must avoid staging destinations (e.g., *_REVIEW, Staging_Area).
        - Must preserve the source hierarchy for sparse mirroring.
        - Must identify repository roots via `is_git_repo` and treat them
          as special candidates (zipped later, not moved directly).
        """

        pass

    def is_git_repo(self, path: Path) -> bool:
        """Return True if `path` is a Git repository root.

        Requirements:
        - A repository is any directory containing a `.git` folder.
        - Do not treat nested files as repositories; only directories.
        - Should be robust against symlinks and permissions errors.
        """

        pass

    def get_file_metadata(self, file_path: Path) -> dict[str, object]:
        """Gather metadata needed for rules and actions.

        Requirements:
        - Must include size, last modified time, and extension.
        - Should capture full absolute path and parent directory.
        - Must avoid following broken symlinks.
        - Keep keys stable so rules can classify files reliably.
        """

        pass
