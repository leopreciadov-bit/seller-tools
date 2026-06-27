# ListingLab

Etsy & Shopify listing generator — first product from the Passive Income Agent Factory.

## Run locally

```bash
cd products/listing-lab
python3 -m http.server 8080
```

Open http://localhost:8080

## Deploy ($0)

**Cloudflare Pages**
1. Push this folder to a GitHub repo
2. Cloudflare Dashboard → Pages → Connect repo
3. Build command: (none) · Output directory: `/`

**Vercel** — same, zero config for static HTML.

## Monetization

| Tier | Price | What |
|------|-------|------|
| Free | $0 | 5 generations/day |
| Pro | $19 lifetime | Unlimited + license key unlock |

Sell on Gumroad. License keys format: `LISTING-XXXX-XXXX` (validate in `app.js` — replace with Gumroad webhook later).

## Next agent tasks

1. **Publisher agent** — finish `GO_TO_MARKET.md`, Reddit launch posts
2. **Builder agent** — add CSV bulk export for Pro users
3. **Monitor agent** — track visitors via Plausible or simple `/api/event`