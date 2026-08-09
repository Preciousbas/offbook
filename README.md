# Offbook

> Keep ecommerce chatbots on-script — a [Coasty](https://coasty.ai) computer-use agent that QA-tests live store chat widgets against the business's own website, then ships a severity-ranked, dollarized report of every place the bot is off-book.

- **[Coasty API](https://coasty.ai/developers)**
- **[Demo script](docs/DEMO_SCRIPT.md)** · **[Step map](docs/STEP_MAP.md)**

---

## What This Is

Ecommerce chatbots drift. A returns window changes from 14 days to 30. A promo expires. A bestseller price ticks up. The knowledge base stays stale — and customers get wrong answers at the exact moment they're deciding to buy.

Offbook fixes that with an audit loop, not a toy demo:

1. Opens the live chatbot widget and captures the greeting
2. Crawls pricing / returns / shipping / promo pages → `claims.json` ground truth
3. Asks 30 hand-written ecommerce questions (6 categories × 5)
4. Scores each reply: `match` | `mismatch` | `deflect` | `hallucinate`
5. Emits `report.md` leading with **high-risk, dollarized** errors + evidence
6. You apply KB corrections manually in Chatbase / Tidio / Crisp admin using the report

> Dry-run mode works fully out of the box — no API key required. Planted demo mismatches surface immediately so you can rehearse the full report flow before spending Coasty compute.

All targets are **audit-only**. Offbook never logs into chatbot admin panels or edits a knowledge base.

---

## Commands

| Command | Purpose |
|---|---|
| `offbook list-targets` | List configured demo targets from `targets.yaml` |
| `offbook spike-widget` | Prove widget open → send → capture before a full audit |
| `offbook spike-truth` | Fetch a policy page → structured claims |
| `offbook ground-truth` | Build `claims.json` for a target without running questions |
| `offbook audit` | Full run: ground truth + question loop + severity-first report |

---

## Setup

```bash
# Python 3.11+ (uv recommended)
curl -LsSf https://astral.sh/uv/install.sh | sh
git clone <your-repo-url>
cd offbook
uv venv .venv
source .venv/bin/activate
uv pip install -e .

cp .env.example .env
```

### Enable live Coasty runs

```env
# .env

# Coasty Computer Use API — required for --live audits
COASTY_API_KEY=your_key_here
COASTY_BASE_URL=https://coasty.ai/v1

# Optional: force dry-run even when a key is present
# OFFBOOK_DRY_RUN=1
```

Get a Coasty key at [coasty.ai/developers](https://coasty.ai/developers). Without it, every command still works in dry-run with planted demo mismatches.

---

## Quickstart

```bash
# Dry-run rehearsal (no API spend) — full 30-question scrollable report
offbook list-targets
offbook spike-widget --target owned_fix --dry-run
offbook spike-truth --url "https://site-eight-eosin-21.vercel.app/pages/returns"
offbook audit --target owned_fix --dry-run
```

### Demo choreography (owned store)

```bash
# Tape A — full severity-ranked report (dry-run, planted mismatches)
offbook audit --target owned_fix --dry-run

# Tape B — live money shots only (price / returns / SUMMER20 / FALL15 / tax)
offbook audit --target owned_fix --live --questions questions/demo_money_shots.yaml
```

`--limit 5` alone is not enough for the demo story — the default bank's first five questions are all pricing. Use `questions/demo_money_shots.yaml` so live clips hit the high-risk mismatches.

Live Coasty run (full bank):

```bash
offbook audit --target owned_fix --live

# Custom question bank for a specific site
offbook audit --target jumia_ng --live --questions path/to/my_questions.yaml
```

### Ad-hoc company (no `targets.yaml` edit)

```bash
offbook audit \
  --company "Jumia Nigeria" \
  --url https://www.jumia.com.ng \
  --live \
  --questions questions/jumia.yaml

# Optional policy page overrides when defaults miss:
offbook audit \
  --company "Jumia Nigeria" \
  --url https://www.jumia.com.ng \
  --returns https://www.jumia.com.ng/sp-return-policy \
  --shipping https://www.jumia.com.ng/sp-delivery \
  --live \
  --questions questions/jumia.yaml
```

Ad-hoc `--company` / `--url` audits **never** fall back to the Offbook Demo Store sample claims. If policy pages can't be fetched or yield no claims, the run fails loudly — pass real `--returns` / `--shipping` / `--pricing` / `--promotions` URLs instead of silently scoring against demo-store truth.

Copy `questions/example_custom.yaml` as a starting point for site-specific banks.

Live calls use **retries with exponential backoff** on `429` / `5xx` and network errors. Task creates always send an `Idempotency-Key` so a retry won't double-provision a machine.

---

## How Coasty Powers This

Offbook is built as a Coasty computer-use agent layered with deterministic ground-truth extraction and reply scoring.

### Computer-use loop

For each audit, Coasty drives a real browser session:

1. Navigate to the storefront
2. Open the live chat widget
3. Capture the greeting
4. Ask each question from the bank and wait for a full reply
5. Hand the captured reply back to Offbook for scoring

Prompt templates live in `src/offbook/prompts/` (`open_widget.txt`, `ask_chatbot.txt`, `extract_claims.txt`).

### Ground truth (`claims.json`)

Before questions run, Offbook fetches the target's pricing, returns, shipping, and promo pages and extracts structured claims — the site's source of truth.

- **Heuristics first** on owned-demo prose: 30-day returns, Trail Runner **$128**, **FALL15**, expired **SUMMER20**
- Live Coasty claim extraction **only fills missing IDs** — it never overwrites structured heuristic values (so thin Coasty JSON can't erase the money shots)
- Category hints keep refund "5–10 business days" from being mislabeled as shipping ETA
- Verify before a live demo: `offbook ground-truth --target owned_fix --live` (or `--dry-run` for heuristic-only)

### Scoring

Each bot reply is classified against the claims:

| Result | Meaning |
|---|---|
| `match` | Answer aligns with site policy |
| `mismatch` | Answer contradicts a known claim |
| `deflect` | Bot dodges (agent handoff, "check the FAQ", etc.) |
| `hallucinate` | Invented or stale fact not supported by the site |

Findings carry severity (`high` / `medium` / `low`) and dollarized impact templates from the question bank — so a wrong return window or dead promo ranks above soft deflections.

### Report (`report.md`)

The report is written for non-technical operators: plain-English summary, high-risk findings first, bot quote vs site truth, why it matters, and evidence paths. Vendor noise (Chatbase / Tidio / Crisp labels) is stripped from customer-facing titles. You take `report.md` into the chatbot admin and fix the KB yourself.

### Spikes before polish

1. **Widget** — `offbook spike-widget --target …`
2. **Ground truth** — `offbook spike-truth --url …`
3. **Owned bot** — plant stale FAQ (14-day returns, dead `SUMMER20`) vs 30-day / `FALL15` site truth

If spikes fail, stop and redesign — don't polish the report on sand.

---

## Architecture

```
src/offbook/
  cli.py                 # Click entry — list-targets, spikes, ground-truth, audit
  audit.py               # Full pipeline orchestration
  coasty_client.py       # Coasty task create / poll / result
  ground_truth.py        # Page fetch + claims extraction
  compare.py             # match / mismatch / deflect / hallucinate scoring
  report.py              # Severity-first Markdown for operators
  reply_clean.py         # Strip computer-use / vendor noise from bot replies
  http_retry.py          # Exponential backoff on 429 / 5xx / network blips
  targets.py             # targets.yaml + ad-hoc company resolution
  demo_replies.py        # Dry-run planted mismatches
  config.py              # Paths, env, dry-run flags
  prompts/               # open_widget, ask_chatbot, extract_claims

questions/
  ecommerce.yaml         # 30 hand-written questions + severity + impact templates
  demo_money_shots.yaml  # 5-question live demo bank (price / returns / promos)
  example_custom.yaml    # Starter for site-specific banks

schemas/                 # JSON Schema for claims and findings
targets.yaml             # Public audit targets + owned demo
samples/                 # Demo claims, owned-bot setup, sample report
spikes/                  # Widget + ground-truth spike logs
artifacts/               # Run outputs (gitignored; regenerate locally)
docs/
  STEP_MAP.md            # 50+ step contest / audit map
  DEMO_SCRIPT.md         # Video shot list
```

---

## Key Features

### Audit pipeline
- Live widget open + greeting capture via Coasty computer use
- Ground-truth crawl across pricing, returns, shipping, promotions
- Heuristic money shots for owned_fix ($128, 30-day returns, FALL15, expired SUMMER20)
- 30-question bank across 6 categories: pricing, returns, promotions, shipping, availability, edge
- Short `demo_money_shots.yaml` bank for live clips (5 questions)
- Deterministic scoring with severity ranking and impact templates
- Severity-first `report.md` + structured `findings.json` + evidence files

### Targets
- Configured targets in `targets.yaml` (`public_demo_a`, `public_demo_b`, `owned_fix`)
- Ad-hoc audits via `--company` + `--url` without editing YAML
- Ad-hoc runs refuse silent sample-claim fallback (fail loud instead)
- Optional `--returns` / `--shipping` / `--pricing` / `--promotions` overrides
- Custom question banks via `--questions`

### Dry-run vs live
- Dry-run rehearses the full report path with planted mismatches — zero API spend
- Live mode drives real Coasty browser tasks against the storefront
- Retries with exponential backoff + idempotent task creates

### Operator-ready output
- Plain-English summaries ("what needs attention" / "what looked fine")
- High-risk findings lead; matches are secondary
- Evidence paths for every flagged answer
- Manual KB correction workflow — Offbook audits, you fix

---

## Targets

| Id | Store | Role |
|---|---|---|
| `public_demo_a` | [Olivia Bottega](https://www.oliviabottega.com) | Bridal ecommerce, live Tidio — primary public catch, audit-only |
| `public_demo_b` | [Tidio Live Demo Store](https://tidio-live-demo-store.myshopify.com) | Official Tidio Shopify demo — Spike 1 / widget reliability |
| `owned_fix` | Offbook Demo Store | Owned Chatbase/Tidio bot with planted stale FAQ — see [`samples/owned_bot/SETUP.md`](samples/owned_bot/SETUP.md) |

Never edit a third-party admin panel. Public targets are customer-interaction only.

---

## Sample dry-run result

Against the owned demo profile, Offbook surfaces high-risk rot such as:

- Bot: **14-day** returns → Site: **30 days** (turning away returns you'd honor)
- Bot: **SUMMER20** still valid → Site: expired; **FALL15** is current
- Bot: bestseller **$99** → Site: **$128**

See `samples/findings/` and regenerate with:

```bash
offbook audit --target owned_fix --dry-run
```

---

## Safety

- **Audit-only** — never logs into chatbot admin or edits a knowledge base
- Public audits are read-only customer interactions
- Apply corrections yourself in the chatbot admin using `report.md` guidance
- Idempotent Coasty task creates (`Idempotency-Key`) prevent double-provisioning on retry
- Rate-limit / gateway errors (`429`, `5xx`) retry with exponential backoff

---

## CI & Tests

GitHub Actions runs pytest on Python 3.11 and 3.12 for every push/PR (`.github/workflows/ci.yml`).

```bash
# via Makefile
make install
make test
make dry-audit
make spikes

# or directly
uv pip install -e ".[dev]"
pytest
```

---

## Roadmap

### Short-term
- **Richer claim extraction** — tighter page → claim mapping for multi-SKU catalogs and regional shipping tables
- **Diff-aware re-audits** — re-run only questions tied to claims that changed since the last `claims.json`
- **More widget vendors** — deeper reliability spikes for Intercom, Gorgias, and Shopify Inbox

### Longer-term
- **Scheduled audits** — cron-friendly runs that email high-risk deltas when the site changes and the bot doesn't
- **KB patch suggestions** — generate copy-ready FAQ diffs from findings without ever logging into admin
- **Multi-locale banks** — question packs for non-English storefronts with the same severity / impact model

---

## Documentation

| File | Contents |
|---|---|
| [`docs/STEP_MAP.md`](docs/STEP_MAP.md) | Full organic step map (50+ steps) for one audit run |
| [`docs/DEMO_SCRIPT.md`](docs/DEMO_SCRIPT.md) | 2–4 minute video shot list |
| [`questions/demo_money_shots.yaml`](questions/demo_money_shots.yaml) | 5-question live demo bank (price / returns / promos) |
| [`samples/owned_bot/SETUP.md`](samples/owned_bot/SETUP.md) | Plant stale FAQ on the owned demo bot |
| [`samples/findings/sample_report.md`](samples/findings/sample_report.md) | Example severity-first report |
| [`artifacts/README.md`](artifacts/README.md) | Where run outputs land |

---

## License

MIT
