"""Strip Coasty / computer-use transcripts down to customer-facing text."""

from __future__ import annotations

import re

_MARKER_SPLIT = re.compile(
    r"(?:BOT_REPLY|Bot reply|Assistant)\s*:\s*",
    re.I,
)
# Non-greedy body; apostrophes inside words (don't / bot's) are allowed.
# Closing quote must be followed by end-of-capture punctuation, not more prose.
_CAPTURED_REPLY_SINGLE = re.compile(
    r"(?:Full )?bot reply(?: text)? captured:\s*'"
    r"((?:[^']|'(?=[A-Za-z]))*?)"
    r"'(?=\s*[\"\)\,\]]|\s*$)",
    re.I | re.S,
)
_CAPTURED_REPLY_DOUBLE = re.compile(
    r'(?:Full )?bot reply(?: text)? captured:\s*"'
    r'((?:[^"]|"(?=[A-Za-z]))*?)'
    r'"(?=\s*[\'\)\,\]]|\s*$)',
    re.I | re.S,
)
_CUA_CUT = re.compile(
    r"(?:</?\s*cua-section\b|</?\s*cua-|^\s*cua-section\b|\n\s*agent\.)",
    re.I | re.M,
)
_TAG = re.compile(r"<[^>]+>")
_AGENT_LINE = re.compile(
    r"^(?:"
    r"agent\.|"
    r"\d+\.\s*(?:complete subtask|the (?:site|chatbot|question|bot|full conversation)\b)|"
    r"complete subtask|"
    r"Ran a UI|"
    r"no screen change|"
    r"Task (?:completed|reported)|"
    r"Please review the result|"
    r"The (?:screenshot|task|chat|bot)\b|"
    r"All (?:tasks|subtasks)|"
    r"Finish the task|"
    r"Giving the page|"
    r"Import time|"
    r"Waiting about|"
    r"Remember\b.*BOT_REPLY|"
    r"powered by Chatbase"
    r")",
    re.I,
)
_NAV_CHROME = re.compile(
    r"(?:←\s*)?Back to store|Skip to (?:content|main)|powered by Chatbase",
    re.I,
)
_NOISE_PHRASE = re.compile(
    r"(?:"
    r"complete[_\s-]?subtask|"
    r"cua-section|"
    r"agent\.(?:done|complete_subtask|save_to_knowledge)|"
    r"the bot'?s reply is fully captured|"
    r"all subtasks are complete|"
    r"finish the task|"
    r"ran a ui script|"
    r"no screen change detected|"
    r"task (?:completed successfully|reported complete)|"
    r"unresolved checklist|"
    r"for later, then finish|"
    r"the screenshot clearly shows|"
    r"grounded-action|"
    r"action-result|"
    r"next-action"
    r")",
    re.I,
)
_TRAILING_AGENT_TAIL = re.compile(
    r"""["']?\s+for later,.*$"""
    r"""|["']\s*(?:</?cua-section\b).*$"""
    r"""|\s*</?cua-section\b.*$""",
    re.I | re.S,
)


def clean_bot_reply(text: str | None) -> str:
    """Return only the chatbot's customer-facing answer.

    If nothing usable remains after stripping Coasty/computer-use noise, return "".
    Callers should substitute a human fallback such as "_No clear answer captured._".
    """
    if not text:
        return ""
    raw = text.strip()

    captured = _extract_captured_reply(raw)
    if captured:
        finalized = _finalize_reply(captured)
        if finalized and not _looks_like_agent_noise(finalized):
            return finalized

    parts = _MARKER_SPLIT.split(raw, maxsplit=1)
    candidate = parts[-1] if len(parts) > 1 else raw

    candidate = _CUA_CUT.split(candidate, maxsplit=1)[0]
    candidate = _TAG.sub(" ", candidate)

    lines: list[str] = []
    for line in candidate.splitlines():
        s = line.strip()
        if not s:
            continue
        if "complete_subtask" in s or "grounded-action" in s or "action-result" in s:
            inner = _extract_captured_reply(s)
            if inner:
                finalized = _finalize_reply(inner)
                if finalized and not _looks_like_agent_noise(finalized):
                    return finalized
            continue
        if _AGENT_LINE.match(s):
            continue
        if s.startswith("BOT_REPLY"):
            continue
        if _looks_like_agent_noise(s):
            continue
        lines.append(s)

    joined = " ".join(lines) if lines else ""
    finalized = _finalize_reply(joined)
    if finalized and not _looks_like_agent_noise(finalized):
        return finalized
    return ""


def _extract_captured_reply(text: str) -> str | None:
    for pattern in (_CAPTURED_REPLY_SINGLE, _CAPTURED_REPLY_DOUBLE):
        match = pattern.search(text)
        if match:
            return match.group(1).strip()
    return None


def clean_greeting(text: str | None) -> str:
    """Greeting may share the same Coasty transcript noise."""
    cleaned = clean_bot_reply(text)
    if cleaned and not _looks_like_agent_noise(cleaned):
        return cleaned
    # Prefer an explicit BOT_REPLY marker when present.
    m = _MARKER_SPLIT.search(text or "")
    if m:
        after = (text or "")[m.end() :]
        after = _CUA_CUT.split(after, maxsplit=1)[0]
        after = _TRAILING_AGENT_TAIL.sub("", after)
        # Take through first closing quote if the greeting was quoted in agent prose.
        qm = re.match(r"\s*([^\"'\n][^\"'\n]{3,160})", after)
        if qm:
            candidate = _finalize_reply(qm.group(1))
            if candidate and not _looks_like_agent_noise(candidate):
                return candidate
    # Fallback: first short quoted greeting-like string
    m = re.search(r"greeting[^'\"]*['\"]([^'\"]{8,160})['\"]", text or "", re.I)
    if m:
        candidate = _finalize_reply(m.group(1))
        if candidate and not _looks_like_agent_noise(candidate):
            return candidate
    m = re.search(
        r"BOT_REPLY:\s*['\"]?([^'\"\n]{8,160})['\"]?",
        text or "",
        re.I,
    )
    if m:
        candidate = _finalize_reply(m.group(1))
        if candidate and not _looks_like_agent_noise(candidate):
            return candidate
    return ""


def clean_policy_text(text: str | None) -> str:
    """Normalize site policy snippets used as ground truth."""
    if not text:
        return ""
    t = _TAG.sub(" ", text)
    t = _NAV_CHROME.sub(" ", t)
    t = re.sub(r"\s+", " ", t).strip()
    # Drop leading mid-word fragments from bad scrape windows
    t = re.sub(r"^[a-z]{1,3}\s+", "", t)
    t = re.sub(r"\s*[.…]{2,}\s*$", ".", t)
    return t.strip(" -•|\t")


def _finalize_reply(text: str) -> str:
    t = re.sub(r"\s+", " ", text or "").strip()
    t = _TRAILING_AGENT_TAIL.sub("", t).strip()
    t = t.strip(" \"'`")
    t = re.sub(r'["\')\]]+$', "", t).strip()
    t = _NAV_CHROME.sub("", t).strip()
    t = _CUA_CUT.split(t, maxsplit=1)[0].strip()
    t = _TAG.sub(" ", t)
    t = re.sub(r"\s+", " ", t).strip(" \"'`")
    # If noise still dominates, try a quoted customer sentence with $ or days
    if _looks_like_agent_noise(t):
        m = re.search(
            r"['\"]([^'\"]{20,400}(?:\$\d+|\d+\s*days?|promo|return|shipping|tax)[^'\"]{0,200})['\"]",
            text or "",
            re.I,
        )
        if m:
            t = re.sub(r"\s+", " ", m.group(1)).strip()
    if _looks_like_agent_noise(t):
        return ""
    return t


def _looks_like_agent_noise(text: str) -> bool:
    if not text:
        return True
    lower = text.lower()
    if _NOISE_PHRASE.search(lower):
        return True
    if lower.startswith("the screenshot") or lower.startswith("the task is complete"):
        return True
    if lower.count("subtask") >= 1:
        return True
    # Numbered computer-use checklist about the page/widget state
    if re.search(
        r"\b1\.\s*the site is loaded\b.*\b2\.\s*",
        lower,
        re.S,
    ):
        return True
    # Broken cua open tags without angle brackets
    if "cua-section" in lower or lower.startswith("cua-section"):
        return True
    return False
