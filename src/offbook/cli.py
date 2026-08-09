"""Offbook CLI."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from offbook import __version__
from offbook.audit import run_audit
from offbook.config import ARTIFACTS_DIR, ROOT, SPIKES_DIR, dry_run_enabled
from offbook.coasty_client import CoastyClient
from offbook.ground_truth import (
    build_ground_truth_for_target,
    claims_to_markdown,
    extract_claims_heuristic,
    fetch_page_text,
)
from offbook.targets import get_target, load_targets, resolve_audit_target

console = Console()


@click.group()
@click.version_option(__version__, prog_name="offbook")
def main() -> None:
    """Offbook — keep ecommerce chatbots on-script with Coasty."""


@main.command("list-targets")
def list_targets() -> None:
    """List configured demo targets."""
    table = Table(title="Offbook targets")
    table.add_column("id")
    table.add_column("role")
    table.add_column("status")
    table.add_column("base_url")
    for t in load_targets():
        table.add_row(
            str(t.get("id")),
            str(t.get("role")),
            str(t.get("status")),
            str(t.get("base_url")),
        )
    console.print(table)


@main.command("spike-widget")
@click.option("--target", "target_id", required=True, help="Target id from targets.yaml")
@click.option("--dry-run/--live", default=None, help="Force dry-run or live Coasty task")
def spike_widget(target_id: str, dry_run: bool | None) -> None:
    """Spike 1: open widget, send one message, capture reply."""
    target = get_target(target_id)
    use_dry = dry_run_enabled(dry_run)
    client = CoastyClient()
    prompt = (ROOT / "src/offbook/prompts/open_widget.txt").read_text(encoding="utf-8")
    ask = (ROOT / "src/offbook/prompts/ask_chatbot.txt").read_text(encoding="utf-8")
    open_task = prompt.format(base_url=target["base_url"])
    ask_task = ask.format(
        base_url=target["base_url"],
        question="Hi — what is your return policy window in days?",
    )

    console.print(f"[bold]Spike widget[/bold] target={target_id} dry_run={use_dry}")
    open_res = client.run_task(
        open_task,
        dry_run=use_dry,
        dry_run_result="BOT_REPLY: Hi! Thanks for visiting — how can we help?",
        max_steps=40,
        metadata={"offbook": "spike_widget_open", "target": target_id},
    )
    ask_res = client.run_task(
        ask_task,
        dry_run=use_dry,
        dry_run_result="BOT_REPLY: You can return items within 14 days of delivery.",
        max_steps=40,
        metadata={"offbook": "spike_widget_ask", "target": target_id},
    )

    SPIKES_DIR.mkdir(parents=True, exist_ok=True)
    results_path = SPIKES_DIR / "widget_results.md"
    entry = (
        f"\n## {target_id} — {datetime.now(timezone.utc).isoformat()}\n\n"
        f"- dry_run: `{use_dry}`\n"
        f"- base_url: `{target.get('base_url')}`\n"
        f"- open_run: `{open_res.run_id}` status=`{open_res.status}`\n"
        f"- ask_run: `{ask_res.run_id}` status=`{ask_res.status}`\n"
        f"- greeting: {open_res.result_text}\n"
        f"- reply: {ask_res.result_text}\n"
        f"- verdict: {'PASS (dry-run simulated)' if use_dry else 'RECORD manually after reviewing screenshots'}\n"
    )
    if results_path.exists():
        results_path.write_text(results_path.read_text(encoding="utf-8") + entry, encoding="utf-8")
    else:
        results_path.write_text(
            "# Spike 1 — Widget reliability\n\n"
            "Goal: open live chat widget → send one message → capture reply.\n"
            + entry,
            encoding="utf-8",
        )
    console.print(f"Wrote {results_path}")
    console.print(open_res.result_text)
    console.print(ask_res.result_text)


@main.command("spike-truth")
@click.option("--url", required=True, help="Pricing or returns page URL")
@click.option("--category", default=None, help="Optional category hint")
@click.option("--dry-run/--live", default=None)
def spike_truth(url: str, category: str | None, dry_run: bool | None) -> None:
    """Spike 2: page → structured claims."""
    use_dry = dry_run_enabled(dry_run)
    console.print(f"[bold]Spike truth[/bold] url={url} dry_run={use_dry}")
    try:
        final_url, text = fetch_page_text(url)
        claims = extract_claims_heuristic(
            page_url=final_url, page_text=text, category_hint=category
        )
        source = "live_fetch+heuristic"
    except Exception as exc:  # noqa: BLE001
        console.print(f"[yellow]Fetch failed ({exc}); using sample demo claims.[/yellow]")
        from offbook.ground_truth import _default_demo_claims

        claims = _default_demo_claims()
        source = f"sample_fallback ({exc})"

    SPIKES_DIR.mkdir(parents=True, exist_ok=True)
    out_json = SPIKES_DIR / "truth_claims.json"
    out_json.write_text(json.dumps(claims, indent=2), encoding="utf-8")
    results_path = SPIKES_DIR / "truth_results.md"
    md = claims_to_markdown(claims)
    entry = (
        f"\n## {url} — {datetime.now(timezone.utc).isoformat()}\n\n"
        f"- source: `{source}`\n"
        f"- claims_extracted: **{len(claims)}**\n"
        f"- output: `{out_json.relative_to(ROOT)}`\n\n"
        f"{md}\n"
    )
    if results_path.exists():
        results_path.write_text(results_path.read_text(encoding="utf-8") + entry, encoding="utf-8")
    else:
        results_path.write_text(
            "# Spike 2 — Ground truth extraction\n\n"
            "Goal: turn policy/pricing prose into checkable claims with source quotes.\n"
            + entry,
            encoding="utf-8",
        )
    console.print(f"Extracted {len(claims)} claims → {out_json}")


@main.command("audit")
@click.option("--target", "target_id", default=None, help="Target id from targets.yaml")
@click.option("--company", default=None, help="Company display name for ad-hoc audits (use with --url)")
@click.option("--url", "site_url", default=None, help="Company website URL for ad-hoc public audit")
@click.option("--returns", "returns_url", default=None, help="Optional returns/refund policy URL or path")
@click.option("--shipping", "shipping_url", default=None, help="Optional shipping policy URL or path")
@click.option("--pricing", "pricing_url", default=None, help="Optional pricing/catalog URL or path")
@click.option("--promotions", "promotions_url", default=None, help="Optional promotions/deals URL or path")
@click.option("--dry-run/--live", default=None)
@click.option(
    "--questions",
    "questions_path",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help="Custom questions YAML (default: questions/ecommerce.yaml)",
)
@click.option("--limit", "question_limit", type=int, default=None, help="Limit questions (dev)")
@click.option("--out", "out_dir", type=click.Path(path_type=Path), default=None)
def audit_cmd(
    target_id: str | None,
    company: str | None,
    site_url: str | None,
    returns_url: str | None,
    shipping_url: str | None,
    pricing_url: str | None,
    promotions_url: str | None,
    dry_run: bool | None,
    questions_path: Path | None,
    question_limit: int | None,
    out_dir: Path | None,
) -> None:
    """Run full audit (ground truth + question loop + report)."""
    try:
        target = resolve_audit_target(
            target_id=target_id,
            company=company,
            url=site_url,
            returns=returns_url,
            shipping=shipping_url,
            pricing=pricing_url,
            promotions=promotions_url,
        )
    except (ValueError, KeyError) as exc:
        raise click.ClickException(str(exc)) from exc

    use_dry = dry_run_enabled(dry_run)
    label = f"{target.get('name')} ({target.get('id')})"
    console.print(
        f"[bold]Audit[/bold] {label} dry_run={use_dry}"
        + (f" questions={questions_path}" if questions_path else "")
    )
    if target.get("role") == "public_audit":
        console.print("[dim]Public audit only — apply KB corrections manually in the chatbot admin.[/dim]")
    try:
        run_dir = run_audit(
            target,
            dry_run=use_dry,
            question_limit=question_limit,
            questions_path=questions_path,
            out_dir=out_dir,
        )
    except RuntimeError as exc:
        raise click.ClickException(str(exc)) from exc
    console.print(f"[green]Done.[/green] Artifacts: {run_dir}")
    console.print(f"Report: {run_dir / 'report.md'}")


@main.command("ground-truth")
@click.option("--target", "target_id", required=True)
@click.option("--dry-run/--live", default=None)
@click.option("--out", "out_dir", type=click.Path(path_type=Path), default=None)
def ground_truth_cmd(target_id: str, dry_run: bool | None, out_dir: Path | None) -> None:
    """Build claims.json for a target without running questions."""
    target = get_target(target_id)
    use_dry = dry_run_enabled(dry_run)
    claims = build_ground_truth_for_target(target, dry_run=use_dry)
    dest = out_dir or (ARTIFACTS_DIR / f"claims_{target_id}")
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "claims.json").write_text(json.dumps(claims, indent=2), encoding="utf-8")
    (dest / "claims.md").write_text(claims_to_markdown(claims), encoding="utf-8")
    console.print(f"Wrote {len(claims)} claims to {dest}")


if __name__ == "__main__":
    main()
