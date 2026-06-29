const FREE_LIMIT = 1;
const STORAGE_KEY = "listinglab_usage";
const PRO_KEY = "listinglab_pro";

function today() {
  return new Date().toISOString().slice(0, 10);
}

function getUsage() {
  const raw = localStorage.getItem(STORAGE_KEY);
  const data = raw ? JSON.parse(raw) : { date: today(), count: 0 };
  if (data.date !== today()) return { date: today(), count: 0 };
  return data;
}

function isPro() {
  return localStorage.getItem(PRO_KEY) === "true";
}

function setUsage(count) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify({ date: today(), count }));
}

function slugWords(text) {
  return text
    .toLowerCase()
    .split(/[^a-z0-9]+/)
    .filter(Boolean);
}

function uniqueTags(words, max = 13) {
  const seen = new Set();
  const tags = [];
  for (const w of words) {
    if (w.length < 3 || seen.has(w)) continue;
    seen.add(w);
    tags.push(w.slice(0, 20));
    if (tags.length >= max) break;
  }
  return tags;
}

function capitalize(s) {
  return s.charAt(0).toUpperCase() + s.slice(1);
}

function buildTitle(platform, product, niche, keywords) {
  const kw = keywords.split(",").map((k) => k.trim()).filter(Boolean);
  const lead = kw[0] || niche.split(",")[0]?.trim() || product;
  if (platform === "etsy") {
    const parts = [product, lead, "Gift", niche.split(",")[0]?.trim()].filter(Boolean);
    let title = parts.join(" | ");
    return title.length > 140 ? title.slice(0, 137) + "..." : title;
  }
  return `${product} — ${capitalize(lead)} | ${capitalize(niche.split(",")[0]?.trim() || "Premium")}`;
}

function buildDescription(platform, product, niche, buyer, features, keywords) {
  const kw = keywords.split(",").map((k) => k.trim()).filter(Boolean).join(", ");
  const feat = features.trim() || "Premium quality materials and careful craftsmanship.";
  const audience = buyer.trim() || "customers who appreciate quality";

  if (platform === "etsy") {
    return `✨ ${product}

Perfect for ${audience}. Designed for ${niche}.

${feat}

• Thoughtfully made with attention to detail
• Ideal gift or everyday essential
• Ships carefully packaged

Keywords: ${kw || niche}

Questions? Message us anytime — we reply within 24 hours.`;
  }

  return `${product}

Built for ${audience} in the ${niche} space.

${feat}

Why customers choose this:
• Reliable quality you can feel
• Fits modern ${niche.toLowerCase()} lifestyles
• Backed by responsive support

SEO focus: ${kw || niche}`;
}

function buildBullets(features, keywords) {
  const lines = features
    .split(/[\n,]+/)
    .map((f) => f.trim())
    .filter(Boolean)
    .slice(0, 5)
    .map((f) => `• ${f}`);
  const kw = keywords.split(",").map((k) => k.trim()).filter(Boolean)[0];
  if (kw) lines.push(`• Optimized for search: ${kw}`);
  if (lines.length === 0) lines.push("• High-quality build and fast shipping");
  return lines.join("\n");
}

function generateListing(data) {
  const { platform, product, niche, buyer, features, keywords } = data;
  const title = buildTitle(platform, product, niche, keywords);
  const description = buildDescription(platform, product, niche, buyer, features, keywords);
  const tagSource = slugWords(`${product} ${niche} ${keywords} ${features}`);
  const maxTags = platform === "etsy" ? 13 : 10;
  const tags = uniqueTags(tagSource, maxTags);
  const bullets = buildBullets(features, keywords);
  return { title, description, tags: tags.join(", "), bullets };
}

function updateUsageLabel() {
  const el = document.getElementById("usage");
  if (isPro()) {
    el.textContent = "Pro unlocked — unlimited generations.";
    return;
  }
  const { count } = getUsage();
  const left = Math.max(0, FREE_LIMIT - count);
  el.textContent = `${left} free generation${left === 1 ? "" : "s"} left today. Upgrade for unlimited.`;
}

function copyText(text) {
  navigator.clipboard.writeText(text);
}

document.getElementById("listing-form").addEventListener("submit", (e) => {
  e.preventDefault();
  const usage = getUsage();
  if (!isPro() && usage.count >= FREE_LIMIT) {
    alert("Free limit reached today. Unlock Pro on Gumroad for unlimited use.");
    return;
  }

  const data = {
    platform: document.getElementById("platform").value,
    product: document.getElementById("product-name").value.trim(),
    niche: document.getElementById("niche").value.trim(),
    buyer: document.getElementById("buyer").value.trim(),
    features: document.getElementById("features").value.trim(),
    keywords: document.getElementById("keywords").value.trim(),
  };

  const out = generateListing(data);
  document.getElementById("out-title").textContent = out.title;
  document.getElementById("out-description").textContent = out.description;
  document.getElementById("out-tags").textContent = out.tags;
  document.getElementById("out-bullets").textContent = out.bullets;

  document.getElementById("results").classList.remove("hidden");
  document.getElementById("copy-all").disabled = false;

  if (!isPro()) {
    setUsage(usage.count + 1);
  }
  updateUsageLabel();
});

document.querySelectorAll(".copy-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    const id = btn.dataset.target;
    copyText(document.getElementById(id).textContent);
    btn.textContent = "Copied!";
    setTimeout(() => { btn.textContent = "Copy"; }, 1200);
  });
});

document.getElementById("copy-all").addEventListener("click", () => {
  const blocks = ["out-title", "out-description", "out-tags", "out-bullets"];
  const all = blocks.map((id) => document.getElementById(id).textContent).join("\n\n---\n\n");
  copyText(all);
});

function validLicense(key) {
  return (
    (key.startsWith("LISTING-") && key.length >= 12) ||
    (key.startsWith("SELLERKIT-") && key.length >= 14)
  );
}

document.getElementById("unlock").addEventListener("click", () => {
  const key = document.getElementById("license-key").value.trim().toUpperCase();
  if (validLicense(key)) {
    localStorage.setItem(PRO_KEY, "true");
    updateUsageLabel();
    alert("Pro unlocked. Thank you!");
  } else {
    alert("Invalid license key. Purchase at Gumroad to get yours.");
  }
});

updateUsageLabel();

(function track() {
  const k = "listinglab_pageviews";
  const n = (+localStorage.getItem(k) || 0) + 1;
  localStorage.setItem(k, n);
  const el = document.getElementById("analytics");
  if (el) el.textContent = `${n} local pageviews`;
})();