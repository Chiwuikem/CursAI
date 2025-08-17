import time
from typing import List

from rich.console import Console
from rich.table import Table

from .schemas import Plan
from .policies import in_allowed_scopes, requires_extra_confirmation
from .skills.files import find_recent, move_to_trash
from .logging_utils import log_line, log_event
from .config import (
    MAX_DELETE_COUNT, MAX_TOTAL_DELETE_MB,
    EXTRA_CONFIRM_PHRASE, BULK_CONFIRM_PHRASE
)

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

def _summary(chosen) -> tuple[int, int]:
    count = len(chosen)
    total_bytes = sum((h.size or 0) for h in chosen)
    return count, total_bytes

def execute(plan: Plan, do_execute: bool, scopes, run_id: str | None = None):
    console.print(f"[cyan]Plan:[/cyan] {plan.rationale}")
    for s in plan.steps:
        console.print(f" - {s.action}: {s.description}")
    if run_id:
        log_event(run_id, "plan.built", {"steps": [ {"action": s.action, "params": s.params} for s in plan.steps ]})
        log_line(f"Plan: {[ (s.action, s.params) for s in plan.steps ]}", run_id=run_id)

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
            if run_id:
                log_event(run_id, "search.results", {
                    "count": len(hits),
                    "sample": [str(h.path) for h in hits[:5]],
                })

        elif step.action == "select_targets":
            before = len(hits)
            hits = [h for h in hits if in_allowed_scopes(h.path, scopes=scopes)]
            hidden = before - len(hits)
            if hidden > 0:
                console.print(f"[yellow]Note:[/yellow] {hidden} item(s) were out of allowed scopes and hidden.")
            chosen = _interactive_select(hits)
            if not chosen:
                console.print("[yellow]No selection. Exiting.[/yellow]")
                if run_id:
                    log_event(run_id, "selection.empty", {})
                return

            if run_id:
                log_event(run_id, "selection.made", {
                    "count": len(chosen),
                    "paths": [str(c.path) for c in chosen[:50]],  # cap to keep log lines small
                })

            # Extra confirmation for risky/system-like selections
            risky = [h for h in chosen if requires_extra_confirmation(h.path)]
            if risky:
                console.print("[red]Warning:[/red] risky/system-like selections detected.")
                console.print(_tabulate(risky))
                print(f"Type '{EXTRA_CONFIRM_PHRASE}' to proceed: ", end="")
                resp = input().strip().lower()
                ok_risky = (resp == EXTRA_CONFIRM_PHRASE.lower())
                if run_id:
                    log_event(run_id, "confirm.risky", {"accepted": ok_risky, "count": len(risky)})
                if not ok_risky:
                    console.print("[yellow]Aborted.[/yellow]")
                    return

            # Bulk-delete safeguards: large count or large total size
            count, total_bytes = _summary(chosen)
            console.print(f"[bold]Summary:[/bold] {count} item(s), total {_fmt_size(total_bytes)}")
            needs_bulk_confirm = (count > MAX_DELETE_COUNT) or (total_bytes / (1024 * 1024) > MAX_TOTAL_DELETE_MB)
            if needs_bulk_confirm:
                console.print(f"[red]Bulk safeguard:[/red] selection exceeds limits "
                              f"({MAX_DELETE_COUNT} files or {MAX_TOTAL_DELETE_MB} MB).")
                print(f"Type '{BULK_CONFIRM_PHRASE}' to proceed: ", end="")
                resp = input().strip().lower()
                ok_bulk = (resp == BULK_CONFIRM_PHRASE.lower())
                if run_id:
                    log_event(run_id, "confirm.bulk", {
                        "accepted": ok_bulk,
                        "count": count,
                        "total_mb": round(total_bytes / (1024 * 1024), 1)
                    })
                if not ok_bulk:
                    console.print("[yellow]Aborted.[/yellow]")
                    return

        elif step.action == "move_to_trash":
            console.print("[bold]Ready to move to Trash:[/bold]")
            console.print(_tabulate(chosen))
            if not do_execute:
                console.print("[blue]Dry-run[/blue]: re-run with --execute to actually delete.")
                if run_id:
                    log_event(run_id, "execute.dry_run", {"count": len(chosen)})
                return
            print("Type 'yes' to confirm: ", end="")
            if input().strip().lower() != "yes":
                console.print("[yellow]Cancelled.[/yellow]")
                if run_id:
                    log_event(run_id, "confirm.final", {"accepted": False})
                return
            if run_id:
                log_event(run_id, "confirm.final", {"accepted": True})

            ok, errs, outcomes = move_to_trash([c.path for c in chosen])
            if run_id:
                log_event(run_id, "delete.result", {
                    "ok": ok,
                    "errors": errs,
                    "outcomes": outcomes[:200],  # cap to keep line size reasonable
                })
            log_line(f"Deleted {ok}; errors: {errs}", run_id=run_id)
            console.print(f"[green]Moved {ok} item(s) to Trash.[/green]")
            if errs:
                console.print(f"[red]Errors:[/red] {errs}")

        elif step.action == "noop":
            console.print("[yellow]No actionable step parsed.[/yellow]")
            if run_id:
                log_event(run_id, "noop", {})

        else:
            console.print(f"[yellow]Unknown step: {step.action}[/yellow]")
            if run_id:
                log_event(run_id, "error.unknown_step", {"action": step.action})
