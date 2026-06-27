# What's actually passive vs one-time

## Agents already did (zero clicks from you)

- Built 2 products, SEO guides, marketing copy
- Deployed permanent site: https://leopreciadov-bit.github.io/seller-tools/
- Meta tag verification live (GSC HTML tag works if you ever click once)
- **IndexNow submitted** — Bing/Yandex will crawl all 6 pages automatically
- License keys generated for Gumroad
- GitHub auto-deploy on every push

## Google Search Console — the one wall

Google **does not allow** bots to verify ownership or submit sitemaps without **your** Google account OAuth. No API key workaround. This is Google's policy, not ours.

**You never need GSC for the site to work or earn money.** It only speeds Google indexing.

Options ranked by effort:
1. **Do nothing** — IndexNow + sitemap in robots.txt still gets you indexed (slower on Google)
2. **One command ever** — `bash scripts/google_once.sh` (opens localhost:8089 once, saves token, auto-submits sitemap forever after)
3. **Ignore Google entirely** — post to Reddit/Etsy, sell on Gumroad (that's the actual money)

## Crypto payments (no Gumroad needed)

```bash
python3 scripts/crypto_setup.py set-wallet --usdt-trc20 YOUR_TRC20_ADDRESS
./scripts/deploy_github_pages.sh
```

Site shows **Pay Crypto** buttons. Buyer sends USDT/BTC/ETH → clicks "I sent payment" → gets license key instantly.

Recommended: **USDT TRC20** (~$1 fees, widely used).

## Actual passive income next (agents can't log into your Gumroad/Reddit)

Money comes from distribution, not GSC. Agents pre-wrote everything in:
- `marketing/ADS_AND_SOCIAL_PACK.md`
- `LAUNCH_PACK.md`

Gumroad + one Reddit post = first sale. That's the passive play after setup.

**Temp-mail autopilot (one CAPTCHA solve):**
```bash
/tmp/seller-venv/bin/python scripts/gumroad_autopilot.py --signup --manual
/tmp/seller-venv/bin/python scripts/gumroad_autopilot.py --products --manual
python3 scripts/gumroad_setup.py set-username YOURNAME
```

Headless signup hits reCAPTCHA — `--manual` opens browser, fills temp mail, you click CAPTCHA once.

**After products exist:** `bash scripts/gumroad_once.sh` wires Buy buttons on site.