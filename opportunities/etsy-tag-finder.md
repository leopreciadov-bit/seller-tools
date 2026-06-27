# Opportunity: Etsy Tag Finder

## Pain
Etsy allows 13 tags per listing; each tag can be 20 characters. Wrong tags = invisible listings. Sellers spend 20–40 minutes per product cross-referencing eRank, Marmalead, and spreadsheets—then still guess. New sellers don't understand long-tail vs. broad tags. Tag mistakes are the #1 fixable SEO error after bad photos. Research tools show *keywords* but not *copy-paste-ready 13-tag sets* optimized for character limits.

## Who pays
- Etsy sellers doing $200–5k/mo (7.5M+ active sellers, majority micro-shops)
- Print-on-demand Etsy shops launching 10+ listings/week
- Digital download sellers in crowded niches (planners, SVGs, wedding invites)
- Willingness to pay: $9–19 one-time or bundled with listing copy tools

## Competitors & gaps
- **eRank** ($6–10/mo) — keyword research, tag *analysis* of existing listings, steep learning curve
- **Marmalead** ($19–49/mo) — powerful, expensive for hobbyists
- **Merch Titans / RankHero tag generators** — free but generic, no niche context, affiliate-heavy spam sites
- **ChatGPT** — invents tags without real search volume or Etsy-specific rules
- **Gap**: instant 13-tag pack from product title + niche, respects 20-char limit, mixes broad + long-tail, explains *why* each tag—pairs naturally with ListingLab

## MVP scope (1–3 days)
**Day 1**: Input—product title, category, 3 seed keywords → output 13 tags with character counts. Rules engine: no duplicates, no repeat words across tags, prioritize multi-word long-tail. One-click copy all tags.

**Day 2**: "Tag strength" heuristic (not real eRank data—pattern-based: word count, specificity score). Compare mode: paste current 13 tags → highlight weak/redundant ones. Save history in localStorage.

**Day 3**: Niche presets (jewelry, digital planners, vintage clothing, POD t-shirts). Gumroad paywall for unlimited + CSV batch (paste 10 titles → 10 tag sets). SEO landing pages per niche.

**No paid APIs in v1**: Use curated tag pattern libraries + keyword expansion from free Etsy autocomplete scrape (public endpoint) or static niche dictionaries agents can update.

## Monetization
- Free: 3 tag sets/day
- $12 lifetime: unlimited + batch CSV + niche presets
- $29 bundle with ListingLab: "Complete Etsy Listing Kit"
- Etsy digital product: "2026 Tag Swipe File for [Niche]" with generator access code

## Distribution
- r/Etsy, r/EtsySellers, r/printondemand—highest-intent audience; tag posts get saved/shared
- Pinterest pins: "13 Etsy tags for wedding invitations" → tool
- YouTube Shorts/TikTok: "Etsy tags in 30 seconds"
- SEO goldmine: "etsy tags for [niche]" pages (programmatic SEO, 50 niches)
- Etsy SEO Facebook groups—free tool demos weekly

## Score preview
pain 9 | build 8 | distribution 9 | moat 7 → 33/40 BUILD NEXT