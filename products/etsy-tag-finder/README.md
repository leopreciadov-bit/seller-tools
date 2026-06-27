# Etsy Tag Finder

Generate exactly 13 Etsy-ready SEO tags from product name, niche, and seed keywords — built for the Passive Income Agent Factory.

## Run locally

```bash
cd products/etsy-tag-finder
python3 -m http.server 8080
```

Open http://localhost:8080

## Deploy ($0)

**Cloudflare Pages**
1. Push this folder to a GitHub repo
2. Cloudflare Dashboard → Pages → Connect repo
3. Build command: (none) · Output directory: `/`

**Vercel** — same, zero config for static HTML.

## Features

| Feature | Details |
|---------|---------|
| Input | Product name, niche, 3–5 seed keywords |
| Output | Exactly 13 tags, max 20 chars each with live char count |
| Rules engine | No duplicates, Etsy-safe chars only, long-tail prioritized |
| Free tier | 3 generations/day (localStorage) |
| Pro | Unlimited via license key `TAGFINDER-XXXX-XXXX` |
| Offline | 100% client-side — no paid APIs |

## Monetization

| Tier | Price | What |
|------|-------|------|
| Free | $0 | 3 generations/day |
| Pro | $14 lifetime | Unlimited + license key unlock |

Sell on Gumroad. License keys format: `TAGFINDER-XXXX-XXXX` (validate in `app.js` — replace with Gumroad webhook later).

## Next agent tasks

1. **Publisher agent** — finish `GO_TO_MARKET.md`, Reddit launch posts
2. **Builder agent** — add CSV bulk export for Pro users (paste 10 products → export tags)
3. **Monitor agent** — track visitors via Plausible or simple localStorage event counter