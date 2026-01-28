"""CLI entry point for Mac-Storage-Optimizer."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table

from mac_optimizer.core import FileMover, RuleEngine, Scanner


def _format_bytes(size_bytes: float) -> str:
    """Return a human-readable size string."""
    if size_bytes < 0:
        return "0 B"
    units = ["B", "KB", "MB", "GB", "TB"]
    value = float(size_bytes)
    unit_index = 0
    while value >= 1024 and unit_index < len(units) - 1:
        value /= 1024
        unit_index += 1
    return f"{value:.1f} {units[unit_index]}"


def _build_dashboard_table(buckets: dict[str, list[dict[str, object]]]) -> tuple[Table, list[str]]:
    """Create a dashboard table and ordered bucket list."""
    table = Table(title="Storage Buckets", show_header=True, header_style="bold")
    table.add_column("ID", justify="right", style="cyan", no_wrap=True)
    table.add_column("Bucket Name", style="magenta")
    table.add_column("File Count", justify="right")
    table.add_column("Total Size", justify="right")

    bucket_names = list(buckets.keys())
    for index, bucket_name in enumerate(bucket_names, start=1):
        items = buckets.get(bucket_name, [])
        total_size = sum(
            float(item.get("size", 0))
            for item in items
            if isinstance(item.get("size"), (int, float))
        )
        table.add_row(
            str(index),
            bucket_name,
            str(len(items)),
            _format_bytes(total_size),
        )

    return table, bucket_names


def _review_bucket(
    console: Console,
    mover: FileMover,
    bucket_name: str,
    bucket_files: list[dict[str, object]],
) -> None:
    """Review and act on a selected bucket."""
    if not bucket_files:
        console.print("[yellow]This bucket is empty.[/yellow]")
        Prompt.ask("Press Enter to return to dashboard", default="")
        return

    total_size = sum(
        float(item.get("size", 0))
        for item in bucket_files
        if isinstance(item.get("size"), (int, float))
    )

    while True:
        console.clear()
        console.rule("[bold]Mac Storage Optimizer")
        console.print(
            f"[bold]Reviewing Bucket:[/bold] {bucket_name} "
            f"({len(bucket_files)} files, {_format_bytes(total_size)})"
        )
        console.print("[L] List Files   [M] Move to Staging   [B] Back")
        choice = Prompt.ask("Choose an option").strip().lower()

        if choice == "l":
            lines = []
            for item in bucket_files:
                size_value = item.get("size", 0)
                size_bytes = float(size_value) if isinstance(size_value, (int, float)) else 0.0
                path_value = item.get("path", "")
                path_str = str(path_value) if path_value else "Unknown path"
                formatted_size = _format_bytes(size_bytes)
                lines.append(f"{formatted_size:>10} | {path_str}")
            with console.pager():
                console.print("\n".join(lines) if lines else "No files to display.")
            continue

        if choice == "m":
            confirm = Prompt.ask(
                f"Are you sure you want to move {len(bucket_files)} files? (y/n)",
                choices=["y", "n"],
                default="n",
            )
            if confirm == "y":
                result = mover.move_files(bucket_files, dry_run=False)
                console.print(
                    f"[green]Moved {result['success_count']} files.[/green] "
                    f"[red]Failed: {result['failed_count']}[/red]"
                )

                bucket_files.clear()

                Prompt.ask("Press Enter to return to dashboard", default="")
                return

            console.print("[cyan]Move cancelled.[/cyan]")
            Prompt.ask("Press Enter to continue", default="")
            continue

        if choice == "b":
            return

        console.print("[yellow]Please choose L, M, or B.[/yellow]")
        Prompt.ask("Press Enter to continue", default="")


def main() -> None:
    """Run the CLI entry point."""
    console = Console()
    scanner = Scanner()
    rules = RuleEngine(min_size_mb=0)
    mover = FileMover()

    try:
        default_path = Path.home() / "Documents"
        directory_input = Prompt.ask("Directory to scan", default=str(default_path))
        root_path = Path(directory_input).expanduser()
        if not root_path.exists():
            console.print(f"[red]Directory not found:[/red] {root_path}")
            return

        with console.status("Scanning..."):
            candidates = scanner.scan(root_path)

        buckets = rules.organize(candidates)

        while True:
            console.clear()
            console.rule("[bold]Mac Storage Optimizer")
            table, bucket_names = _build_dashboard_table(buckets)
            console.print(table)

            choice = Prompt.ask("Select a Bucket ID (or 'q' to quit)").strip().lower()
            if choice == "q":
                break

            if not choice.isdigit():
                console.print("[yellow]Please enter a valid bucket ID.[/yellow]")
                continue

            selected_index = int(choice) - 1
            if selected_index < 0 or selected_index >= len(bucket_names):
                console.print("[yellow]Bucket ID out of range.[/yellow]")
                continue

            bucket_name = bucket_names[selected_index]
            bucket_files = buckets.get(bucket_name, [])
            _review_bucket(console, mover, bucket_name, bucket_files)
    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled by user.[/yellow]")

if __name__ == "__main__":
    main()