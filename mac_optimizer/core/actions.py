"""Move and archive actions."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any


class FileMover:
    """Move selected files into a staging area with safety logging."""

    def __init__(self, staging_path: Path | None = None) -> None:
        """Initialize the file mover and ensure staging exists.

        Args:
            staging_path: Optional path for the staging directory.
        """
        default_path = Path.home() / "Mac_Optimizer_Staging"
        self.staging_path = (staging_path or default_path).expanduser()
        self.staging_path.mkdir(parents=True, exist_ok=True)
        self._log_path = self.staging_path / "move_log.json"

    def move_files(self, files: list[dict[str, Any]], dry_run: bool = True) -> dict[str, Any]:
        """Move files into staging with collision protection.

        Args:
            files: List of metadata dictionaries containing "path".
            dry_run: When True, do not move or log files.

        Returns:
            Summary dictionary with success/failed counts and errors list.
        """
        success_count = 0
        failed_count = 0
        errors: list[dict[str, str]] = []
        move_log: list[dict[str, str]] = []

        for metadata in files:
            path_value = metadata.get("path")
            if not isinstance(path_value, str) or not path_value:
                failed_count += 1
                errors.append({"path": str(path_value), "error": "Missing or invalid path"})
                continue

            source_path = Path(path_value)
            if not source_path.exists():
                failed_count += 1
                errors.append({"path": str(source_path), "error": "Source does not exist"})
                continue

            try:
                destination_path = self._staged_path_for(source_path)
                destination_path.parent.mkdir(parents=True, exist_ok=True)
                destination_path = self._unique_destination(destination_path)

                if not dry_run:
                    shutil.move(str(source_path), str(destination_path))
                    move_log.append(
                        {
                            "original_path": str(source_path),
                            "staged_path": str(destination_path),
                        }
                    )

                success_count += 1
            except (PermissionError, FileNotFoundError, OSError) as exc:
                failed_count += 1
                errors.append({"path": str(source_path), "error": str(exc)})

        if not dry_run and move_log:
            self._append_move_log(move_log)

        return {
            "success_count": success_count,
            "failed_count": failed_count,
            "errors": errors,
        }

    def _staged_path_for(self, source_path: Path) -> Path:
        """Return the mirrored staging path for a source file."""
        relative = source_path.relative_to(source_path.anchor)
        return self.staging_path / relative

    def _unique_destination(self, destination_path: Path) -> Path:
        """Return a destination path that does not overwrite existing files."""
        if not destination_path.exists():
            return destination_path

        stem, suffix = self._split_name(destination_path.name)
        counter = 1
        while True:
            candidate_name = f"{stem}_{counter}{suffix}"
            candidate_path = destination_path.with_name(candidate_name)
            if not candidate_path.exists():
                return candidate_path
            counter += 1

    def _split_name(self, filename: str) -> tuple[str, str]:
        """Split filename into stem and full suffix string."""
        path = Path(filename)
        suffixes = "".join(path.suffixes)
        if not suffixes:
            return filename, ""
        stem = filename[: -len(suffixes)]
        return stem, suffixes

    def _append_move_log(self, entries: list[dict[str, str]]) -> None:
        """Append entries to the move log JSON file."""
        existing: list[dict[str, str]] = []
        if self._log_path.exists():
            try:
                existing = json.loads(self._log_path.read_text())
            except json.JSONDecodeError:
                existing = []

        existing.extend(entries)
        self._log_path.write_text(json.dumps(existing, indent=2))
