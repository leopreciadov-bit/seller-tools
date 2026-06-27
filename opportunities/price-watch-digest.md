# Opportunity: PriceWatch Digest

## Pain
Dropshippers and small Shopify sellers manually check competitor prices 2–3×/week—opening 15 tabs, screenshotting, forgetting what changed. A $2 price drop on a hero SKU can kill margins; missing a competitor's sale means lost Buy Box or Etsy search rank. Enterprise tools (Prisync, Competera) start at $50–200/mo. Solo sellers want a weekly "what moved?" email, not a dashboard they'll never open.

## Who pays
- Shopify dropshippers monitoring 5–20 competitor URLs
- Etsy sellers watching similar listings in their niche (handmade has fewer tools)
- Amazon FBA side-hustlers tracking 10 ASINs (adjacent, higher complexity)
- Indie hackers doing competitive intel on rival SaaS pricing pages
- Willingness to pay: $7–15/mo for 20 URLs or $25 lifetime for weekly digest

## Competitors & gaps
- **Prisync, Visualping, Keepa** — accurate but expensive or technical (Keepa = Amazon-only)
- **Visualping / Distill.io** — per-page change alerts, noisy, no price-specific parsing
- **Spreadsheets + manual checks** — what 80% of micro-sellers actually do
- **Gap**: dead-simple "add URL → get Friday email with old price, new price, % change"—no login required in v1 (email + magic link), optimized for Shopify product pages and Etsy listings

## MVP scope (1–3 days)
**Day 1**: Form to add up to 5 URLs + email. Cron job (GitHub Actions or Cloudflare Worker cron) fetches pages, regex/scrape price from JSON-LD `offers.price` or common Shopify `product.price` patterns. Store last-seen price in SQLite/Turso free tier.

**Day 2**: Weekly digest email via Buttondown—table of changes only (skip unchanged). "No changes this week" still builds habit. Unsubscribe link.

**Day 3**: Paid tier—20 URLs, daily digest option, CSV history export. Landing page with sample digest screenshot. Handle fetch failures gracefully (retry, mark "price not found").

**Build caveat**: Scraping breaks; MVP targets Shopify `.myshopify.com` and Etsy listing pages only. Document limitations honestly.

## Monetization
- Free: 3 URLs, weekly digest
- $9/mo or $29 lifetime: 20 URLs + daily option + 90-day history
- Gumroad "Competitor Price Tracker Template" (Google Sheet + tool access bundle)
- B2B stretch: agency white-label digest for $49/mo (Lane B)

## Distribution
- r/dropshipping, r/shopify, r/FulfillmentByAmazon—"I email you when competitors change prices"
- Indie Hackers—competitive intel angle for SaaS founders watching pricing pages
- Twitter/X build-in-public: weekly digest open rates as metric
- SEO: "shopify competitor price tracker cheap" (long-tail)
- Cross-promote in ListingLab post-build email list

## Score preview
pain 7 | build 6 | distribution 6 | moat 5 → 24/40 backlog