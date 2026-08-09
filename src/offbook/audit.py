"""Widget audit loop + report emission."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from offbook.compare import compare_reply
from offbook.config import ARTIFACTS_DIR, PROMPTS_DIR
from offbook.coasty_client import CoastyClient
from offbook.demo_replies import dry_run_reply
from offbook.ground_truth import build_ground_truth_for_target, claims_to_markdown
from offbook.reply_clean import clean_bot_reply, clean_greeting
from offbook.report import render_report
from offbook.targets import load_questions


def run_audit(
    target: dict[str, Any],
    *,
    dry_run: bool = True,
    question_limit: int | None = None,
    questions_path: Path | None = None,
    out_dir: Path | None = None,
) -> Path:
    client = CoastyClient()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = out_dir or (ARTIFACTS_DIR / f"{target['id']}_{stamp}")
    run_dir.mkdir(parents=True, exist_ok=True)
    evidence_dir = run_dir / "evidence"
    evidence_dir.mkdir(exist_ok=True)

    # Ad-hoc --company/--url audits must never silently score against demo-store sample claims.
    use_sample_fallback = target.get("status") != "adhoc"
    claims = build_ground_truth_for_target(
        target,
        client=client,
        dry_run=dry_run,
        use_sample_fallback=use_sample_fallback,
    )
    (run_dir / "claims.json").write_text(json.dumps(claims, indent=2), encoding="utf-8")
    (run_dir / "claims.md").write_text(claims_to_markdown(claims), encoding="utf-8")
    claims_by_id = {c["id"]: c for c in claims}

    questions = load_questions(questions_path)
    if question_limit is not None:
        questions = questions[:question_limit]

    greeting = _capture_greeting(target, client=client, dry_run=dry_run, evidence_dir=evidence_dir)
    (run_dir / "greeting.txt").write_text(greeting, encoding="utf-8")

    findings: list[dict[str, Any]] = []
    for idx, question in enumerate(questions, start=1):
        reply, shot = _ask_question(
            target,
            question,
            client=client,
            dry_run=dry_run,
            evidence_dir=evidence_dir,
            index=idx,
        )
        findings.append(
            compare_reply(
                question=question,
                bot_reply=reply,
                claims_by_id=claims_by_id,
                evidence_screenshot=shot,
            )
        )

    (run_dir / "findings.json").write_text(json.dumps(findings, indent=2), encoding="utf-8")
    (run_dir / "report.md").write_text(
        render_report(
            target=target,
            findings=findings,
            run_meta={
                "target_id": target.get("id"),
                "dry_run": dry_run,
                "questions": len(questions),
                "claims": len(claims),
                "questions_path": str(questions_path) if questions_path else "questions/ecommerce.yaml",
            },
        ),
        encoding="utf-8",
    )
    (run_dir / "steps.json").write_text(
        json.dumps(_step_log(len(questions), bool(greeting)), indent=2),
        encoding="utf-8",
    )
    return run_dir


def _capture_greeting(
    target: dict[str, Any],
    *,
    client: CoastyClient,
    dry_run: bool,
    evidence_dir: Path,
) -> str:
    prompt = (PROMPTS_DIR / "open_widget.txt").read_text(encoding="utf-8")
    task = prompt.format(base_url=target.get("base_url"))
    dry_text = (
        "Hi! Welcome to Offbook Demo Store — ask us about orders, returns, or promos."
        if target.get("role") == "owned_fix" or target.get("id") == "owned_fix"
        else "[dry-run] Widget greeting captured (replace with live Coasty output)."
    )
    result = client.run_task(
        task,
        dry_run=dry_run,
        dry_run_result=dry_text,
        max_steps=40,
        metadata={"offbook": "open_widget", "target": target.get("id")},
    )
    text = clean_greeting(result.result_text or dry_text)
    if not text and dry_run:
        text = dry_text
    if not text:
        text = "_No clear greeting captured._"
    (evidence_dir / "greeting.txt").write_text(text, encoding="utf-8")
    return text


def _ask_question(
    target: dict[str, Any],
    question: dict[str, Any],
    *,
    client: CoastyClient,
    dry_run: bool,
    evidence_dir: Path,
    index: int,
) -> tuple[str, str]:
    prompt = (PROMPTS_DIR / "ask_chatbot.txt").read_text(encoding="utf-8")
    task = prompt.format(base_url=target.get("base_url"), question=question.get("question"))
    canned = dry_run_reply(str(target.get("id")), target.get("role"), str(question.get("id")))
    result = client.run_task(
        task,
        dry_run=dry_run,
        dry_run_result=canned,
        max_steps=40,
        metadata={
            "offbook": "ask_chatbot",
            "target": target.get("id"),
            "question_id": question.get("id"),
        },
    )
    raw = result.result_text or canned
    reply = clean_bot_reply(raw)
    if not reply and dry_run and canned:
        # Canned dry-run answers are already customer-facing.
        reply = re.sub(r"^\[dry-run\]\s*", "", canned.strip())
        reply = clean_bot_reply(reply) or reply
    evidence_name = f"{index:02d}_{question['id']}.txt"
    evidence_path = evidence_dir / evidence_name
    evidence_path.write_text(reply or "_No clear answer captured._", encoding="utf-8")
    return reply, str(evidence_path.relative_to(evidence_dir.parent))


def _step_log(question_count: int, has_greeting: bool) -> dict[str, Any]:
    phase1, phase2, phase3 = 8, question_count * 6, 8
    return {
        "phase1_baseline_steps": phase1,
        "phase2_test_loop_steps": phase2,
        "phase3_report_steps": phase3,
        "total_estimated_steps": phase1 + phase2 + phase3,
        "greeting_captured": has_greeting,
        "questions": question_count,
    }
