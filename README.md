# Mac Storage Optimizer

A modular Python CLI utility designed to analyze local storage on macOS, categorize files by last-modified age into structured review buckets, and safely move selected files to a mirrored staging directory with audit logging.

---

## Overview

Unlike standard disk-cleaning scripts that delete files directly, **Mac Storage Optimizer** acts as an inspection and staging tool:

1. **Scans** a target directory recursively while ignoring hidden files and treating Git repositories as atomic units.
2. **Classifies** files into 6 time-based age buckets while preventing access to protected macOS system directories (`/System`, `/Applications`, `/Library`).
3. **Presents** an interactive terminal dashboard using `rich`.
4. **Stages** selected files into `~/Mac_Optimizer_Staging`, preserving their original folder structure, preventing filename collisions, and writing a `move_log.json` audit trail.

---

## Directory Structure

```text
mac-storage-optimizer/
├── mac_optimizer/
│   ├── __init__.py
│   ├── main.py              # CLI interface and interactive terminal dashboard
│   └── core/
│       ├── __init__.py      # Package export for Scanner, RuleEngine, FileMover
│       ├── scanner.py       # Recursive directory traversal and POSIX metadata extraction
│       ├── rules.py         # Age-based bucketing and protected system path guard
│       └── actions.py       # Safe staging, collision prevention, and JSON logging
└── requirements.txt
```

## Core Mechanics & Architecture
### 1. File Scanner (mac_optimizer/core/scanner.py)

- Recursively walks the directory tree using pathlib.Path.

- Skips hidden files and directories (names starting with .).

- Git Repository Detection: Identifies directories containing a .git folder and treats the repository root as a single unit without scanning internal .git objects.

- Extracts metadata for each item: absolute path, size in bytes (st_size), last modified timestamp (st_mtime), and file extension.

- Gracefully handles PermissionError and FileNotFoundError.

### 2. Rules Engine (mac_optimizer/core/rules.py)

Evaluates file age against the current UTC timestamp:

- 1_Year+: Modified > 365 days ago

- 6_Months+: Modified > 180 days ago

- 3_Months+: Modified > 90 days ago

- 1_Month+: Modified > 30 days ago

- 2_Weeks+: Modified > 14 days ago

- Recent: Modified ≤ 14 days ago

Safety Filter: Discards any path located inside macOS protected roots (/System, /Applications, /Library).

### 3. File Mover & Staging (mac_optimizer/core/actions.py)

- Target staging location defaults to ~/Mac_Optimizer_Staging.

- Hierarchy Mirroring: Recreates the relative path of the source file inside the staging directory.

- Collision Protection: If a file with the same name already exists in staging, appends an incrementing counter suffix (e.g., filename_1.ext).

- Audit Trail: Appends a JSON record of all successful moves (original_path and staged_path) to ~/Mac_Optimizer_Staging/move_log.json.

- Supports dry-run validation to test moves before disk execution.

### 4. Interactive CLI (mac_optimizer/main.py)

- Built with rich for formatting, tables, prompts, and paged listings.

- Displays a summary table of all buckets with file counts and human-readable byte formatting (B, KB, MB, GB, TB).


## Prerequisites

- macOS (Darwin)
- Python 3.10 or higher

## Installation & Setup

1. Clone the repository:
```
git clone [https://github.com/bigunhe/mac-storage-optimizer.git](https://github.com/bigunhe/mac-storage-optimizer.git)
cd mac-storage-optimizer
```

2. Create and activate a virtual environment:
```
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies:
```pip install rich```
(Or ```pip install -r requirements.txt``` if available)

## Usage

1. Launch the CLI:
  ```python3 -m mac_optimizer.main```

2. Enter the directory to Scan:
   Enter an absolute or relative path, or press ```Enter``` to use the default (```~/Documents```).
   
3. Dashboard Navigation:

- Enter the ID of any bucket to inspect its files.

- Enter ```q``` to exit.


#### Bucket Review Options:

- ```[L] List Files```: Opens a scrollable terminal pager showing individual file sizes and full paths.

- ```[M] Move to Staging```: Prompts for confirmation (y/n) and moves all files in that bucket to ~/Mac_Optimizer_Staging.

- ```[B] Back```: Returns to the main dashboard table.


## Safety Features
- No Direct Deletion: Files are never permanently deleted by this tool; they are moved to a staging folder for manual review.

- Protected System Paths: Scans ignore ```/System```, ```/Applications```, and ```/Library``` to prevent system file corruption.

- Collision Guard: Existing files in the staging area are never overwritten.

- JSON Audit Trail: Every move operation is logged with timestamped source and destination paths in ```~/Mac_Optimizer_Staging/move_log.json```.
   
