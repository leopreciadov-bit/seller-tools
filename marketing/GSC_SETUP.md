# Google Search Console Setup

## Quick start (3 commands)

```bash
cd /root/agent-programs/passive-income-agent-program

# 1. Set your live URL (GitHub Pages, Cloudflare, etc.)
python3 scripts/gsc_setup.py init --url https://YOUR_USER.github.io/seller-tools

# 2. After Google gives you the meta tag token:
python3 scripts/gsc_setup.py set-token PASTE_TOKEN_HERE

# 3. Deploy site, click Verify in GSC, then:
python3 scripts/gsc_setup.py mark-verified --sitemap-submitted
```

Check status anytime:
```bash
python3 scripts/gsc_setup.py status
```

---

## Step-by-step (first time)

### 1. Deploy your site first
GSC needs a **public** URL. Options:
- GitHub Pages (workflow already in `.github/workflows/deploy-pages.yml`)
- Cloudflare Pages: `npx wrangler pages deploy site --project-name=seller-tools`

### 2. Open Search Console
Go to [Google Search Console](https://search.google.com/search-console/welcome)

### 3. Add property
- Choose **URL prefix** (easier than Domain)
- Enter your live URL, e.g. `https://you.github.io/seller-tools/`

### 4. Verify ownership

**Option A — HTML meta tag (recommended)**

Google shows something like:
```html
<meta name="google-site-verification" content="aBcDeFg123456789" />
```

Copy only the `content` value (`aBcDeFg123456789`), then:
```bash
python3 scripts/gsc_setup.py set-token aBcDeFg123456789
```

Redeploy → click **Verify** in GSC.

**Option B — HTML file upload**

Google gives a filename like `google1234567890abcdef.html`

```bash
python3 scripts/gsc_setup.py set-html-file google1234567890abcdef.html
```

Redeploy → Verify.

### 5. Submit sitemap
In GSC left sidebar: **Sitemaps** → Add new sitemap:
```
sitemap.xml
```
(Full URL will be `https://YOUR_DOMAIN/sitemap.xml`)

### 6. Request indexing (optional but speeds up)
**URL Inspection** → paste each URL → **Request indexing**:
- `/`
- `/listing-lab/`
- `/etsy-tag-finder/`
- `/guides/how-to-choose-etsy-tags.html`
- `/guides/etsy-listing-description-template.html`
- `/guides/shopify-product-listing-seo.html`

---

## What’s already configured on the site

| Asset | Purpose |
|-------|---------|
| `site/sitemap.xml` | All pages listed for Google |
| `site/robots.txt` | Points to sitemap |
| `site/assets/gsc-config.js` | Verification token (set via script) |
| Meta tags on all pages | Injected by `gsc_setup.py set-token` |
| `pipeline/gsc.json` | Tracks verification + sitemap status |

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Verification failed | Redeploy after `set-token`. View page source — meta tag must be in `<head>`. |
| Sitemap couldn’t fetch | URL must be public. Run `init --url` with exact deployed base. |
| Wrong property type | Use URL prefix matching deploy path (include `/seller-tools` if GitHub project site). |
| Tunnel URL (trycloudflare) | Don’t use for GSC — tunnels die. Deploy permanent URL first. |

---

## After verification (week 1)

1. **Performance** tab — watch impressions for `etsy tag generator`, `listing generator`
2. **Pages** — see which guides get traffic first
3. **Sitemaps** — confirm "Success" status
4. Fix any **Coverage** errors (usually 404s or redirect issues)