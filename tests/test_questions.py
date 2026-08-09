"""Tests for custom question bank loading."""

from __future__ import annotations

from pathlib import Path

import pytest

from offbook.config import ROOT
from offbook.targets import load_questions


def test_default_questions_load():
    questions = load_questions()
    assert len(questions) >= 30
    assert questions[0]["id"]
    assert questions[0]["question"]


def test_custom_questions_path():
    path = ROOT / "questions" / "example_custom.yaml"
    questions = load_questions(path)
    assert len(questions) == 3
    assert questions[0]["id"] == "custom_returns_01"


def test_missing_questions_file_raises():
    with pytest.raises(FileNotFoundError):
        load_questions(Path("/tmp/offbook-does-not-exist-questions.yaml"))
