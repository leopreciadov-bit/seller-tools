# Passive Income Agent Program

**Purpose**: Multi-agent factory that discovers, validates, builds, publishes, and monitors income-generating products.

**Constraints**: $0 upfront budget. Dev-first. Maximize revenue potential across micro-SaaS, digital products, and marketplace listings.

---

## Reality Check

| Channel | Time to $1 | Ceiling | Passivity | Fit for dev + $0 |
|---------|------------|---------|-----------|------------------|
| Micro-SaaS | 2–6 weeks | High (MRR) | Medium | **Best** |
| Gumroad/Etsy digital products | 3–7 days | Medium | High | **Fastest first dollar** |
| SEO content sites | 3–6 months | Medium | High | Slow start |
| Crypto/trading bots | Days | High risk | Low | Not recommended |
| Lead gen / outreach | 1–2 weeks | Medium | Low | Legal/ops overhead |

**Strategy**: Run two lanes in parallel.
1. **Lane A (cash now)** — Ship digital products + free tools that funnel to paid.
2. **Lane B (MRR)** — Turn validated tools into micro-SaaS once people pay once.

---

## Agent Roster

| Agent | Persona | Job | Output |
|-------|---------|-----|--------|
| **Orchestrator** | (you / main session) | Pick lane, assign work, review revenue | `pipeline/state.json` |
| **Scout** | `income-scout` | Find pain points, trends, competitors | `opportunities/*.md` |
| **Validator** | `income-validator` | Score ideas: demand, build time, monetization | `opportunities/scored.json` |
| **Builder** | `income-builder` | Ship MVP in `products/<name>/` | Working code + README |
| **Publisher** | `income-publisher` | Landing page, Gumroad copy, Etsy listing, deploy | `products/<name>/GO_TO_MARKET.md` |
| **Monitor** | `income-monitor` | Track metrics, suggest experiments | `pipeline/weekly-report.md` |

---

## $0 Stack (use until revenue)

| Need | Free option |
|------|-------------|
| Hosting | Cloudflare Pages, Vercel, GitHub Pages |
| Domain | Use `*.pages.dev` until first sale |
| Payments | Gumroad (pay when you earn), Lemon Squeezy |
| Auth | Skip until needed; or Clerk free tier |
| Database | SQLite, localStorage, Turso free tier |
| Email | Buttondown free tier, Gumroad built-in |
| Analytics | Plausible self-host skip → use `/api/event` + JSON file |

---

## Pipeline (repeat weekly)

```
Scout → Validator → Builder → Publisher → Monitor
         ↓ kill bad ideas
```

### Phase 1 — Scout (30 min)
Prompt the scout agent:
> Research 5 monetizable micro-product ideas for a solo developer with $0 budget. Focus on Etsy sellers, Shopify store owners, or indie hackers. For each: pain point, willingness to pay, competitor gaps, build estimate.

### Phase 2 — Validate (15 min)
Score each idea 1–10 on:
- **Pain** — do people already pay for workarounds?
- **Build** — can MVP ship in < 3 days?
- **Distribution** — can you reach buyers without paid ads?
- **Moat** — can agents maintain/improve it?

Kill anything scoring < 24/40.

### Phase 3 — Build (1–3 days)
Rules:
- Works with zero user data (see app-dev-agent-program patterns)
- One core job, done well
- Free tier + obvious paid upgrade
- No paid APIs in v1 — templates + BYOK optional

### Phase 4 — Publish (same day as build)
Ship three surfaces minimum:
1. **Live demo** (free tier on static hosting)
2. **Gumroad product** ($9–29 one-time OR template pack)
3. **Etsy digital listing** (if visual/template product)

### Phase 5 — Monitor (15 min/week)
Track: visitors, signups, sales, which channel converted.
Double down on what sells. Kill what doesn't after 30 days.

---

## First Product: ListingLab

**Problem**: Etsy/Shopify sellers waste hours writing titles, descriptions, tags, and SEO copy.

**Solution**: Input product basics → get platform-optimized listings in seconds.

**Monetization**:
- Free: 5 generations/day (localStorage counter)
- Gumroad: $19 lifetime — unlimited + bulk CSV export
- Future: $12/mo SaaS with saved listings + A/B variants

**Location**: `products/listing-lab/`

---

## Grok Commands

Run the full pipeline:
```bash
cd /root/agent-programs/passive-income-agent-program
python pipeline/run.py status
python pipeline/run.py init-product listing-lab
```

Spawn agents manually in Grok:
```
/income-scout — find 5 new product ideas in [niche]
/income-builder — implement the top-scored idea from opportunities/scored.json
/income-publisher — write Gumroad + landing page copy for products/listing-lab
```

---

## Revenue Targets

| Milestone | Target | Timeline |
|-----------|--------|----------|
| First sale | $9+ | Week 1–2 |
| $100/mo | 5–10 sales or 1 SaaS sub | Month 1–2 |
| $1k/mo | 1 winning product + upsell | Month 3–6 |

Passive income is real but not magic. These agents reduce build/publish time ~80%. You still need distribution (Reddit, X, Etsy SEO, Product Hunt).