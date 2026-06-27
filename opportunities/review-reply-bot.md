# Opportunity: ReviewReply Bot

## Pain
Etsy and Shopify store owners get 5–50 reviews/month. Ignoring them hurts SEO and trust; replying badly looks robotic. Writing unique, on-brand replies takes 2–5 minutes each—30+ minutes/week for active shops. Negative reviews cause panic: owners either ignore them or write defensive replies that make it worse. They already pay for reputation tools ($20–80/mo) but those focus on *getting* reviews, not *replying* to them.

## Who pays
- Shopify merchants with Judge.me, Loox, or Stamped reviews (10k+ SKUs or high order volume)
- Etsy sellers with 100+ reviews who care about star seller badge
- Local service businesses using Google Business reviews (adjacent expansion)
- Willingness to pay: $12–25/mo or $29 lifetime for unlimited reply generation

## Competitors & gaps
- **ChatGPT** — generic tone, no platform rules (Etsy 140-char limits, Shopify HTML)
- **Birdeye, Podium** — enterprise pricing, overkill for solo sellers
- **Shopify app store** — scattered "AI review response" apps ($9–19/mo) with poor UX and API lock-in
- **Gap**: paste-review workflow (no OAuth in v1), tone presets (warm/craft/professional), and platform-specific templates—especially for Etsy negative-review de-escalation scripts

## MVP scope (1–3 days)
**Day 1**: Paste review text + star rating + product niche → 3 reply options (short/medium/detailed). Tone slider: friendly, professional, apologetic. Copy-paste output. Rules baked in: never argue, thank by name, offer offline resolution for 1–2 stars.

**Day 2**: Platform modes—Etsy (plain text, brevity), Shopify (slightly longer, can mention policies), Google (local SEO keywords). Save brand voice snippet in localStorage ("We're a family candle shop in Portland…").

**Day 3**: Bulk mode—paste 10 reviews (CSV or line-separated) → export all replies. Gumroad gate for bulk + negative-review playbook PDF.

## Monetization
- Free: 5 replies/day
- $19 lifetime: unlimited replies + bulk export + tone presets
- $9/mo: "Review Response Playbook" drip + monthly new templates for seasonal shops
- Future: Shopify app listing once OAuth version ships (Lane B MRR)

## Distribution
- r/Etsy, r/shopify, r/ecommerce—post negative-review reply examples (high engagement)
- Etsy seller Facebook groups—share free tool + screenshot of before/after replies
- Partner shoutout from ListingLab users ("complete your listing + review stack")
- AppSumo-style lifetime deal on Indie Hackers once 50+ free users
- SEO: "how to respond to bad Etsy review" → tool CTA

## Score preview
pain 8 | build 7 | distribution 7 | moat 6 → 28/40 backlog