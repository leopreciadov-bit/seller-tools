# Opportunity: InvoiceForge

## Pain
Freelancers and Etsy sellers invoice clients manually in Google Docs or Excel—ugly, unprofessional, and easy to forget. Chasing unpaid invoices costs 5–10 hours/month. QuickBooks and FreshBooks feel like overkill at $15–30/mo for someone sending 5–15 invoices/month. They want: branded PDF in 60 seconds, payment link, and a "who owes me?" list.

## Who pays
- Freelancers on Upwork/Fiverr ($2k–10k/mo) who invoice 3–20 clients/month
- Etsy custom-order sellers who need one-off invoices outside Etsy Payments
- Indie consultants and designers who refuse subscription accounting software
- Willingness to pay: $9–29 one-time or $5/mo for unlimited + reminders

## Competitors & gaps
- **Wave, Zoho Invoice** — free but heavy onboarding, US-centric tax features nobody uses
- **Invoice Ninja, Invoice Simple** — mobile-first, cluttered upsells
- **Notion/Google Docs templates** — no PDF math, no status tracking
- **Gap**: zero-login invoice builder that remembers clients in localStorage, exports clean PDF, and emails a payment reminder template—no accounting suite baggage

## MVP scope (1–3 days)
**Day 1**: Single-page form—your logo, client name, line items, tax, due date → branded PDF download (jsPDF or html2pdf). Save drafts to localStorage.

**Day 2**: Client list + invoice status (draft / sent / paid). Copy-paste email reminder templates. 3 preset themes (minimal, bold, Etsy-craft).

**Day 3**: Gumroad paywall for unlimited invoices + custom logo upload + CSV export of invoice history. Optional BYOK Stripe payment link field (no Stripe integration needed).

## Monetization
- Free: 3 invoices/month, watermark on PDF
- $15 lifetime (Gumroad): unlimited invoices, no watermark, all themes
- $5/mo (Lemon Squeezy): reminders pack + recurring invoice templates
- Bundle: "Freelancer Starter Kit" on Etsy—invoice templates + generator access code

## Distribution
- r/freelance, r/Upwork, r/smallbusiness—"I built a free invoice PDF tool, no signup"
- Indie Hackers "Show IH" with revenue transparency post
- YouTube Short: "Stop using Word for invoices" → tool link
- SEO: "free invoice generator for freelancers" (low competition long-tail)
- Cross-sell from ListingLab and Freelance Proposal Kit email footers

## Score preview
pain 8 | build 8 | distribution 7 | moat 7 → 30/40 backlog