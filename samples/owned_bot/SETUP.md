# Offbook Demo Store — owned bot setup (audit target)

Use this checklist to stand up a **free-tier** Chatbase or Tidio bot you own for audit rehearsal.
Offbook is audit-only: apply KB corrections yourself in the chatbot admin using `report.md`.

## Demo storefront (already hosted)

Static site source: `samples/owned_bot/site/`  
Live URL: **https://site-eight-eosin-21.vercel.app**

Published site truth:

- Returns: **30 days**
- Promo: **FALL15** (15% off full-price); SUMMER20 expired
- Free shipping over **$75** (full-price)
- Bestseller: **Trail Runner — $128**

`targets.yaml` → `owned_fix.base_url` already points here.

## 1. Create the bot

1. Sign up at [Chatbase](https://www.chatbase.co/) or [Tidio](https://www.tidio.com/).
2. Create a bot named `offbook-demo-store`.
3. When asked for the company website, use:
   `https://site-eight-eosin-21.vercel.app`
4. Embed the chat widget: paste the Chatbase snippet into
   `samples/owned_bot/site/assets/site.js`, redeploy the site
   (`cd samples/owned_bot/site && vercel --prod`).

## 2. Plant stale FAQ (intentional rot)

In the bot knowledge base, add entries that **disagree** with the page:

| Topic | Plant in KB (wrong) | Site truth |
| --- | --- | --- |
| Returns | "Returns within **14 days**" | 30 days |
| Promo | "Use **SUMMER20** for 20% off" | Expired; FALL15 is current |
| Holiday sale | "Holiday sale is live" | Ended |
| Price | "Bestseller is **$99**" | $128 |

## 3. Verify (audit)

```bash
offbook spike-widget --target owned_fix --live
offbook audit --target owned_fix --live
```

Open `artifacts/<run>/report.md` and apply the suggested corrections manually in Chatbase/Tidio admin. Optionally re-run the audit to confirm.

Dry-run mode simulates the planted mismatches so you can rehearse without burning credits:

```bash
offbook audit --target owned_fix --dry-run
```

## Redeploy storefront

```bash
cd samples/owned_bot/site
vercel --prod
```

`netlify.toml` at the repo root is also configured to publish this folder if you prefer Netlify later.
