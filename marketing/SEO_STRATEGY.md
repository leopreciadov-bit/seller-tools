# SEO Strategy — Seller Tools

## Target keywords (by priority)

### Tier 1 — High intent, rankable
| Keyword | Volume signal | Page |
|---------|---------------|------|
| etsy tag generator | High | /etsy-tag-finder/ |
| etsy listing generator | High | /listing-lab/ |
| etsy tags | High | /guides/how-to-choose-etsy-tags.html |
| shopify product description generator | Medium | /listing-lab/ |
| etsy seo tags | Medium | /etsy-tag-finder/ |

### Tier 2 — Long-tail guides (content SEO)
| Keyword | Page |
|---------|------|
| how many tags on etsy | /guides/how-to-choose-etsy-tags.html |
| etsy listing description template | /guides/etsy-listing-description-template.html |
| shopify product listing seo | /guides/shopify-product-listing-seo.html |
| etsy title generator | /listing-lab/ |
| 13 etsy tags | /etsy-tag-finder/ |

### Tier 3 — Capture later (blog expansion)
- etsy seo 2026
- best etsy tags for [niche]
- shopify dropshipping product description
- print on demand listing template

---

## On-page SEO (done)

- [x] Unique title + meta description per page
- [x] H1 matches primary keyword
- [x] JSON-LD: WebApplication, FAQPage, Article, HowTo
- [x] Internal linking (hub ↔ tools ↔ guides)
- [x] robots.txt + sitemap.xml
- [x] Open Graph + Twitter cards
- [x] Canonical URLs (dynamic via seo.js)

---

## Off-page SEO (your job)

1. **Reddit** — Link guides, not sales pages. r/Etsy, r/shopify, r/ecommerce
2. **Pinterest** — Pin guide graphics → tool landing pages
3. **YouTube Shorts** — "I generated 13 Etsy tags in 10 seconds" screen recording
4. **Product Hunt** — Launch Seller Tools hub
5. **Backlinks** — Guest comment on Etsy seller blogs with tool mention
6. **Etsy digital product** — Sell template pack linking to free tools (Etsy SEO for your Etsy listing)

---

## Technical post-deploy

```bash
# After GitHub Pages live, submit sitemap:
# Google Search Console → Sitemaps → https://YOUR_DOMAIN/sitemap.xml

# Update sitemap absolute URLs:
python3 scripts/build_sitemap.py --base https://YOUR_USER.github.io/seller-tools
```

---

## Monthly SEO checklist

- [ ] Add 1 new guide page targeting a long-tail keyword
- [ ] Check Search Console for impressions → double down on winning pages
- [ ] Update FAQ schema with real user questions from Reddit
- [ ] Refresh meta descriptions if CTR < 2%