# LAUNCH PACK — Copy, Paste, Ship

**LIVE NOW:** https://leopreciadov-bit.github.io/seller-tools  
- ListingLab: https://leopreciadov-bit.github.io/seller-tools/listing-lab/  
- Etsy Tag Finder: https://leopreciadov-bit.github.io/seller-tools/etsy-tag-finder/  
- GSC verify: https://leopreciadov-bit.github.io/seller-tools/google5ddb8b4ec852634c.html  
- Sitemap: https://leopreciadov-bit.github.io/seller-tools/sitemap.xml  

> Tunnel restarts change the URL. Permanent: `./scripts/deploy_github_pages.sh` after `gh auth login`

---

## Gumroad — ListingLab Pro ($19)

**Title:** ListingLab Pro — Unlimited Etsy & Shopify Listing Generator

**URL slug:** listinglab-pro

**Price:** $19

**Description:**
```
Stop spending an hour per listing.

ListingLab turns product name + niche + keywords into:
✓ Etsy/Shopify-optimized titles
✓ Full descriptions  
✓ 13 Etsy tags or 10 Shopify SEO tags
✓ Bullet points

FREE: 5 generations/day at https://leopreciadov-bit.github.io/seller-tools/listing-lab/
PRO: Unlimited + license key (delivered instantly)

License format: LISTING-XXXX-XXXX
Paste into the app to unlock.
```

---

## Gumroad — Etsy Tag Finder Pro ($14)

**Title:** Etsy Tag Finder Pro — 13 Perfect Tags Every Time

**Price:** $14

**Description:**
```
Etsy's 13-tag limit is brutal. This tool nails it.

✓ Exactly 13 tags, max 20 chars each
✓ Long-tail SEO combos
✓ No duplicates, no rejected characters
✓ Char count per tag

FREE: 3/day at https://leopreciadov-bit.github.io/seller-tools/etsy-tag-finder/
PRO: Unlimited — license TAGFINDER-XXXX-XXXX
```

---

## Gumroad — Seller Kit Bundle ($29)

Both Pro tools. Higher AOV, same buyer.

---

## Reddit — r/Etsy (post when you have URL)

**Title:** I built a free Etsy tag generator (13 tags, 20 char limit enforced) — feedback welcome

**Body:**
```
I got tired of manually counting characters on Etsy tags, so I built a small free tool.

You enter product name, niche, and a few seed keywords. It outputs exactly 13 tags with the char count shown for each.

Free tier is 3/day. If it's useful I added a $14 lifetime unlock for unlimited runs.

Link: https://leopreciadov-bit.github.io/seller-tools/etsy-tag-finder/

What would make this actually useful for your shop? Missing fields? Bad tag suggestions?
```

---

## Reddit — r/sidehustle

**Title:** Free listing copy generator for Etsy/Shopify sellers (5/day)

**Body:**
```
Built a side project for marketplace sellers — paste product basics, get title + description + tags + bullets.

No signup, runs in browser. Trying to validate if people would pay $19 for unlimited + bulk export.

https://leopreciadov-bit.github.io/seller-tools/listing-lab/

Roast the output quality — that's what I need most.
```

---

## X thread

```
1/ Marketplace sellers: listing copy IS your SEO.

2/ I shipped two free tools:
   → ListingLab (full listings)
   → Etsy Tag Finder (13 perfect tags)

3/ Both run in-browser, no signup.
   Free tiers: 5/day and 3/day

4/ Pro is $14–19 lifetime if you want unlimited.

5/ https://leopreciadov-bit.github.io/seller-tools

6/ What tool should I build next for sellers?
```

---

## Product Hunt

**Name:** Seller Tools — ListingLab + Etsy Tag Finder  
**Tagline:** Generate Etsy listings and 13 SEO tags from product basics in one click.  
**Link:** https://leopreciadov-bit.github.io/seller-tools

---

## Deploy (pick one, 5 min)

```bash
cd /root/agent-programs/passive-income-agent-program

# GitHub Pages (free, permanent)
git init && git add . && git commit -m "Launch seller tools"
# Create repo on GitHub, then:
git remote add origin git@github.com:YOU/seller-tools.git
git push -u origin main
# Enable Pages: Settings → Pages → GitHub Actions

# Or Cloudflare Pages
cd site && npx wrangler login && npx wrangler pages deploy . --project-name=seller-tools
```

---

## License keys

Pre-generated in `pipeline/licenses-*.txt`. Paste into Gumroad "content" delivery email:

```
Thanks for purchasing! Your license key:

PASTE_KEY_HERE

Unlock at https://leopreciadov-bit.github.io/seller-tools/listing-lab/ → Pro section
```