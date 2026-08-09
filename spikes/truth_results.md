# Spike 2 — Ground truth extraction

Goal: turn policy/pricing prose into checkable claims with source quotes.

## How to run

```bash
offbook spike-truth --url "https://example.com/pages/returns"
offbook spike-truth --url "https://example.com/pages/shipping"
offbook ground-truth --target owned_fix --dry-run
```

If the URL is unreachable or yields no patterned facts, Offbook falls back to the demo claim set (`samples/claims/demo_store_claims.json`) so the rest of the pipeline stays testable.

## Quality checklist

For each page, confirm claims have:

- stable `id`
- `claim_text` that is checkable (numbers, codes, yes/no policy)
- `source_url`
- verbatim `source_quote`
- `checked_at`

## Results

### Demo store fallback (owned_fix dry-run)

- claims_extracted: **30**
- output: `samples/claims/demo_store_claims.json`
- covers returns window (30 days), FALL15 promo, $75 free shipping, Trail Runner $128, etc.

### Live page fetches

Append dated entries below as you spike real pricing/returns URLs. Prefer list/table-heavy pages over marketing prose.

## Gate

If heuristic/Coasty extraction is noisy on marketing prose, restrict Phase A crawl to list/table-heavy pages (price tables, numbered return bullets) before expanding.

## https://www.oliviabottega.com/pages/returns-refunds — 2026-08-06T15:11:13.144482+00:00

- source: `live_fetch+heuristic`
- claims_extracted: **1**
- output: `spikes/truth_claims.json`

# Ground truth claims

## returns

- **returns_final_sale**: $) Uruguay (USD $) Vanuatu (USD $) Vietnam (USD $) Final Sale Wedding Dresses All Wedding Dresses NEW IN Short & Midi Convertible/2 in 1 Long Sleeve Summer 2026 Drop Waistline Court
  - source: https://www.oliviabottega.com/pages/returns-refunds
  - quote: $) Uruguay (USD $) Vanuatu (USD $) Vietnam (USD $) Final Sale Wedding Dresses All Wedding Dresses NEW IN Short & Midi Convertible/2 in 1 Long Sleeve Summer 2026 Drop Waistline Court


## https://site-eight-eosin-21.vercel.app/ — 2026-08-09T16:02:57.958542+00:00

- source: `live_fetch+heuristic`
- claims_extracted: **2**
- output: `spikes/truth_claims.json`

# Ground truth claims

## promotions

- **promo_current_code**: Current promo code mentioned: FALL15.
  - source: https://site-eight-eosin-21.vercel.app/
  - quote: Runner — $128.00 before tax and shipping. In stock for sizes 8–12. Free standard shipping on orders over $75 · Current code FALL15 Quick policies Returns: unused items within 30 days of delivery Shipp
- **promo_summer20_status**: Page mentions SUMMER20.
  - source: https://site-eight-eosin-21.vercel.app/
  - quote: days of delivery Shipping: US & Canada , free over $75 (full-price) Promos: active code on the sale page — SUMMER20 has expired Offbook Demo Store — owned Chatbase/Tidio target for Phase C. Terms · Gi


## https://site-eight-eosin-21.vercel.app/pages/returns — 2026-08-09T16:06:01.432953+00:00

- source: `live_fetch+heuristic`
- claims_extracted: **2**
- output: `spikes/truth_claims.json`

# Ground truth claims

## returns

- **returns_final_sale**: Final-sale and clearance items are non-refundable.
  - source: https://site-eight-eosin-21.vercel.app/pages/returns
  - quote: condition. Shipping & exceptions Customers are responsible for return shipping on change-of-mind returns. Final sale items are non-refundable. Gift returns accepted with packing slip; merchandise cred

## shipping

- **shipping_standard_days**: Standard shipping takes 5-10 business days.
  - source: https://site-eight-eosin-21.vercel.app/pages/returns
  - quote: non-refundable. Gift returns accepted with packing slip; merchandise credit issued. Refund timing Refunds appear in 5–10 business days after we receive the return.


## https://site-eight-eosin-21.vercel.app/pages/shipping — 2026-08-09T16:06:23.911680+00:00

- source: `live_fetch+heuristic`
- claims_extracted: **3**
- output: `spikes/truth_claims.json`

# Ground truth claims

## pricing

- **tax_policy**: Applicable sales tax is calculated at checkout.
  - source: https://site-eight-eosin-21.vercel.app/pages/shipping
  - quote: Canada. Orders placed before 12 PM ship same business day. Carriers & tax Standard: USPS. Expedited: UPS. Applicable sales tax is calculated at checkout.

## shipping

- **shipping_free_threshold**: Free shipping on orders over $75.
  - source: https://site-eight-eosin-21.vercel.app/pages/shipping
  - quote: policy Delivery windows, carriers, and free-shipping rules. Free shipping Free standard shipping on orders over $75. Free shipping over $75 applies to full-price merchandise only. Timing & destination
- **shipping_standard_days**: Standard shipping takes 3-7 business days.
  - source: https://site-eight-eosin-21.vercel.app/pages/shipping
  - quote: rders over $75. Free shipping over $75 applies to full-price merchandise only. Timing & destinations Standard delivery: 3–7 business days after shipment. We currently ship to the United States and Can


## https://site-eight-eosin-21.vercel.app/pages/sale — 2026-08-09T16:07:07.099518+00:00

- source: `live_fetch+heuristic`
- claims_extracted: **0**
- output: `spikes/truth_claims.json`

# Ground truth claims


## https://site-eight-eosin-21.vercel.app/products/trail-runner — 2026-08-09T16:07:37.173897+00:00

- source: `live_fetch+heuristic`
- claims_extracted: **0**
- output: `spikes/truth_claims.json`

# Ground truth claims

