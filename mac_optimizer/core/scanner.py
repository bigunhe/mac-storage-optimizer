"""File system scanning for Mac-Storage-Optimizer.
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
        root = root.resolve()
        candidates: list[Path] = []

        try:
            for entry in root.iterdir():
                if entry.name.startswith("."):
                    continue

                if entry.is_dir():
                    if (entry / ".git").is_dir():
                        if self.is_git_repo(entry):
                            candidates.append(entry.resolve())
                        continue

                    candidates.extend(self.scan_directory(entry))
                    continue

                candidates.append(entry.resolve())
        except (PermissionError, FileNotFoundError):
            return candidates

        return candidates

    def is_git_repo(self, path: Path) -> bool:
        """Return True if `path` is a Git repository root.

        Requirements:
        - A repository is any directory containing a `.git` folder.
        - Do not treat nested files as repositories; only directories.
        - Should be robust against symlinks and permissions errors.
        """
        # Check if the .git folder exists inside this path
        return (path / ".git").is_dir()

    def get_file_metadata(self, file_path: Path) -> dict[str, object]:
        """Gather metadata needed for rules and actions.

        Requirements:
        - Must include size, last modified time, and extension.
        - Should capture full absolute path and parent directory.
        - Must avoid following broken symlinks.
        - Keep keys stable so rules can classify files reliably.
        """
        try:
            stats = file_path.stat()
        except FileNotFoundError:
            return {}

        return {
            "path": str(file_path.resolve()),
            "size": stats.st_size,
            "modified": stats.st_mtime,
            "extension": file_path.suffix.lower(),
        }



# --- MANUAL TEST BENCH ---
if __name__ == "__main__":
    my_scanner = FileScanner()
    # test_path = Path("/Users/bigunhettiarachchi/Downloads") 
    test_path = Path("/Users/bigunhettiarachchi/Desktop") 
    
    print(f"Testing scanner on: {test_path}")
    
    found_files = my_scanner.scan_directory(test_path)
    
    print(f"\n--- Result: Found {len(found_files)} items ---")
    for path in found_files:
        # Print a tag so you know WHY it was picked
        if (path / ".git").is_dir():
            print(f"[CODING - PROJECT] {path.name}")
        else:
            meta = my_scanner.get_file_metadata(path)
            size_mb = meta.get('size',0) / (1024 * 1024) # convert bytes to MB
            print(f"[FILE] {path.name} ({size_mb:.2f} MB)")

    #  --- to run the test, run -> python3 mac_optimizer/core/scanner.py