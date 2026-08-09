.PHONY: install dry-audit test spikes

install:
	uv venv .venv
	uv pip install -e ".[dev]"

dry-audit:
	.venv/bin/offbook audit --target owned_fix --dry-run --out artifacts/sample_audit

spikes:
	.venv/bin/offbook spike-widget --target owned_fix --dry-run
	.venv/bin/offbook spike-truth --url "https://www.example.com"

test:
	.venv/bin/pytest
