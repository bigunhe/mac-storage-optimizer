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
            total_size = sum(
                float(item.get("size", 0))
                for item in bucket_files
                if isinstance(item.get("size"), (int, float))
            )

            console.print(
                f"Found {len(bucket_files)} files in '{bucket_name}' "
                f"({_format_bytes(total_size)})."
            )
            confirm = Prompt.ask("Move to staging? (y/n)", choices=["y", "n"], default="n")
            if confirm == "y":
                result = mover.move_files(bucket_files, dry_run=False)
                console.print(
                    f"[green]Moved {result['success_count']} files.[/green] "
                    f"[red]Failed: {result['failed_count']}[/red]"
                )
            else:
                console.print("[cyan]Skipped move.[/cyan]")

            Prompt.ask("Press Enter to return to dashboard", default="")
    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled by user.[/yellow]")
