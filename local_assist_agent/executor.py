import time
from typing import List

from rich.console import Console
from rich.table import Table

from .schemas import Plan
from .policies import in_allowed_scopes, requires_extra_confirmation
from .skills.files import find_recent, move_to_trash
from .logging_utils import log_line

console = Console()

def _fmt_size(size_bytes: int) -> str:
    if size_bytes is None:
        return "-"
    units = ["KB", "MB", "GB"]
    x = size_bytes / 1024.0
    for u in units:
        if x < 1024:
            return f"{x:.1f} {u}"
        x /= 1024.0
    return f"{x:.1f} TB"

def _tabulate(hits) -> Table:
    t = Table(title="Candidates (newest first)")
    t.add_column("#"); t.add_column("Name"); t.add_column("Path"); t.add_column("Size"); t.add_column("Modified")
    for i, h in enumerate(hits, 1):
        ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(h.mtime))
        t.add_row(str(i), h.path.name, str(h.path), _fmt_size(h.size), ts)
    return t

def _interactive_select(hits):
    if not hits:
        console.print("[yellow]No candidates found.[/yellow]")
        return []
    console.print(_tabulate(hits))
    print("Select numbers (e.g., 1,3-5), type 'all' for everything, or press Enter to cancel: ", end="")
    sel = input().strip()
    if not sel:
        return []
    if sel.lower() == "all":
        return hits[:]
    idxs = set()
    for part in sel.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-", 1)
            if a.isdigit() and b.isdigit():
                idxs.update(range(int(a), int(b) + 1))
        elif part.isdigit():
            idxs.add(int(part))
    return [h for i, h in enumerate(hits, 1) if i in idxs]

def execute(plan: Plan, do_execute: bool, scopes):
    console.print(f"[cyan]Plan:[/cyan] {plan.rationale}")
    for s in plan.steps:
        console.print(f" - {s.action}: {s.description}")
    log_line(f"Plan: {[ (s.action, s.params) for s in plan.steps ]}")

    hits = []
    chosen = []

    for step in plan.steps:
        if step.action == "search_files":
            hits = find_recent(
                roots=scopes,
                patterns=step.params.get("patterns", ["*"]),
                days=step.params.get("days"),
                name_hint=step.params.get("name_hint"),
                newer_than_days=step.params.get("newer_than_days"),
                older_than_days=step.params.get("older_than_days"),
                min_size_kb=step.params.get("min_size_kb"),
                max_size_kb=step.params.get("max_size_kb"),
            )

        elif step.action == "select_targets":
            hits = [h for h in hits if in_allowed_scopes(h.path, scopes=scopes)]
            chosen = _interactive_select(hits)
            if not chosen:
                console.print("[yellow]No selection. Exiting.[/yellow]")
                return
            risky = [h for h in chosen if requires_extra_confirmation(h.path)]
            if risky:
                console.print("[red]Warning: risky selections detected.[/red]")
                console.print(_tabulate(risky))
                print("Type 'I UNDERSTAND' to proceed: ", end="")
                if input().strip() != "I UNDERSTAND":
                    console.print("[yellow]Aborted.[/yellow]")
                    return

        elif step.action == "move_to_trash":
            console.print("[bold]Ready to move to Trash:[/bold]")
            console.print(_tabulate(chosen))
            if not do_execute:
                console.print("[blue]Dry-run[/blue]: re-run with --execute to actually delete.")
                return
            print("Type 'yes' to confirm: ", end="")
            if input().strip().lower() != "yes":
                console.print("[yellow]Cancelled.[/yellow]")
                return
            ok, errs = move_to_trash([c.path for c in chosen])
            log_line(f"Deleted {ok}; errors: {errs}")
            console.print(f"[green]Moved {ok} item(s) to Trash.[/green]")
            if errs:
                console.print(f"[red]Errors:[/red] {errs}")

        elif step.action == "noop":
            console.print("[yellow]No actionable step parsed.[/yellow]")

        else:
            console.print(f"[yellow]Unknown step: {step.action}[/yellow]")
