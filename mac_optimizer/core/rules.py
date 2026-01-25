"""Rules engine for bucketing files by age."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class RuleEngine:
    """Organize candidates into time-based buckets for review.

    The engine is an organizer: large files are always shown,
    including recent ones, unless blocked by safety rules.
    """

    min_size_mb: float = 50.0
    protected_paths: tuple[str, ...] = ("/System", "/Applications", "/Library")

    def analyze_candidates(self, candidates: Iterable[dict[str, object]]) -> dict[str, list[dict[str, object]]]:
        """Bucket candidates by age after size and safety checks.

        Args:
            candidates: Iterable of metadata dictionaries from the scanner.

        Returns:
            Mapping of bucket name to list of metadata dictionaries.
        """
        buckets: dict[str, list[dict[str, object]]] = {
            "1_Year+": [],
            "6_Months+": [],
            "3_Months+": [],
            "1_Month+": [],
            "2_Weeks+": [],
            "Recent": [],
        }

        now = datetime.now(timezone.utc).timestamp()
        min_size_bytes = self.min_size_mb * 1024 * 1024

        for metadata in candidates:
            if not metadata:
                continue

            path_value = metadata.get("path")
            if not isinstance(path_value, str) or not path_value:
                continue

            if self._is_protected_path(path_value):
                continue

            size_value = metadata.get("size", 0)
            size_bytes = float(size_value) if isinstance(size_value, (int, float)) else 0.0
            if size_bytes < min_size_bytes:
                continue

            modified_value = metadata.get("modified", now)
            modified_ts = float(modified_value) if isinstance(modified_value, (int, float)) else now
            age_days = max(0.0, (now - modified_ts) / 86400)

            bucket = self._bucket_for_age(age_days)
            buckets[bucket].append(dict(metadata))

        return buckets

    def _is_protected_path(self, path_str: str) -> bool:
        """Return True if the path is within a protected root."""
        normalized = Path(path_str).as_posix()
        for protected in self.protected_paths:
            protected_norm = Path(protected).as_posix().rstrip("/")
            if normalized == protected_norm:
                return True
            if normalized.startswith(f"{protected_norm}/"):
                return True
        return False

    def _bucket_for_age(self, age_days: float) -> str:
        """Return bucket name for a given age in days."""
        if age_days > 365:
            return "1_Year+"
        if age_days > 180:
            return "6_Months+"
        if age_days > 90:
            return "3_Months+"
        if age_days > 30:
            return "1_Month+"
        if age_days > 14:
            return "2_Weeks+"
        return "Recent"


# --- MANUAL TEST BENCH ---
if __name__ == "__main__":
    import time
    from pathlib import Path
    
    # 1. Setup: Create the Judge with a small 10MB limit for testing
    print("--- TESTING RULE ENGINE ---")
    engine = RuleEngine(min_size_mb=10)
    
    # 2. Mock Data: Create "Fake" files to test the logic
    # We use raw timestamps (time.time()) to simulate what scanner.py sends
    now_ts = time.time()
    day_seconds = 86400
    
    mock_candidates = [
        # Case A: Ancient File (2 Years old) -> Should go to "1_Year+"
        {
            "path": "/Users/bigun/Movies/old_movie.mp4",
            "size": 100 * 1024 * 1024,  # 100 MB
            "modified": now_ts - (700 * day_seconds),
            "tags": [],
            "is_project_root": False
        },
        # Case B: Recent File (Yesterday) -> Should go to "Recent"
        # (This proves we are NOT hiding new big files)
        {
            "path": "/Users/bigun/Downloads/fresh_download.zip",
            "size": 500 * 1024 * 1024,  # 500 MB
            "modified": now_ts - (1 * day_seconds),
            "tags": ["Red"],
            "is_project_root": False
        },
        # Case C: Small File -> Should be IGNORED (Filtered out)
        {
            "path": "/Users/bigun/Documents/notes.txt",
            "size": 1 * 1024 * 1024,    # 1 MB (Too small)
            "modified": now_ts - (700 * day_seconds),
            "tags": [],
            "is_project_root": False
        }
    ]

    # 3. Run the Logic
    results = engine.analyze_candidates(mock_candidates)

    # 4. Print the Verdict
    for bucket, items in results.items():
        if items:
            print(f"\n📁 Bucket: {bucket}")
            for item in items:
                # Convert bytes to MB for display
                size_mb = item['size'] / (1024 * 1024)
                name = Path(item['path']).name
                print(f"   - {name} ({size_mb:.2f} MB)")
                if item['tags']:
                    print(f"     [TAGGED: {item['tags']}]")

    # 5. Quick Auto-Check
    has_recent = any(x['path'].endswith('fresh_download.zip') for x in results['Recent'])
    if has_recent:
        print("\n✅ SUCCESS: Recent files are visible.")
    else:
        print("\n❌ FAILURE: Recent files were hidden!")