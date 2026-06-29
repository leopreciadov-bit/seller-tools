const FREE_LIMIT = 3;
const TAG_COUNT = 13;
const MAX_TAG_LEN = 20;
const STORAGE_KEY = "etsy_tagfinder_usage";
const PRO_KEY = "etsy_tagfinder_pro";

const LONG_TAIL_MODIFIERS = [
  "gift",
  "handmade",
  "custom",
  "personalized",
  "unique",
  "vintage",
  "modern",
  "boho",
  "minimalist",
  "rustic",
  "cute",
  "aesthetic",
  "for her",
  "for him",
  "for home",
  "small business",
  "made to order",
  "eco friendly",
];

const ETSY_REJECTED = /[^a-z0-9\s-]/gi;

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

function tokenize(text) {
  return text
    .toLowerCase()
    .split(/[^a-z0-9]+/)
    .filter((w) => w.length >= 2);
}

function sanitizeTag(raw) {
  return raw
    .toLowerCase()
    .replace(ETSY_REJECTED, "")
    .replace(/\s+/g, " ")
    .trim();
}

function truncateTag(tag) {
  if (tag.length <= MAX_TAG_LEN) return tag;
  const cut = tag.slice(0, MAX_TAG_LEN);
  const lastSpace = cut.lastIndexOf(" ");
  if (lastSpace > 8) return cut.slice(0, lastSpace).trim();
  return cut.trim();
}

function normalizeKey(tag) {
  return tag.toLowerCase().replace(/\s+/g, " ");
}

function wordCount(tag) {
  return tag.split(/\s+/).filter(Boolean).length;
}

function isLongTail(tag) {
  return wordCount(tag) >= 2;
}

function scoreTag(tag, seedSet) {
  const words = tag.split(/\s+/);
  const seedHits = words.filter((w) => seedSet.has(w)).length;
  const len = tag.length;
  const lenScore = len >= 12 && len <= MAX_TAG_LEN ? 3 : len >= 8 ? 2 : 1;
  const tailScore = isLongTail(tag) ? 4 : 0;
  const multiScore = words.length >= 3 ? 2 : 0;
  return tailScore + lenScore + seedHits * 2 + multiScore + len * 0.05;
}

function buildCandidates(product, niche, keywords) {
  const productWords = tokenize(product);
  const nicheWords = tokenize(niche);
  const seeds = keywords.map((k) => sanitizeTag(k)).filter(Boolean);
  const seedWords = seeds.flatMap(tokenize);
  const seedSet = new Set(seedWords);

  const candidates = new Set();

  function add(raw) {
    const tag = truncateTag(sanitizeTag(raw));
    if (tag.length < 3) return;
    candidates.add(tag);
  }

  seeds.forEach(add);

  for (const seed of seeds) {
    add(seed);
    for (const mod of LONG_TAIL_MODIFIERS) {
      add(`${seed} ${mod}`);
      add(`${mod} ${seed}`);
    }
    for (const pw of productWords.slice(0, 3)) {
      add(`${pw} ${seed}`);
      add(`${seed} ${pw}`);
    }
    for (const nw of nicheWords.slice(0, 3)) {
      add(`${nw} ${seed}`);
      add(`${seed} ${nw}`);
    }
  }

  for (let i = 0; i < seeds.length; i++) {
    for (let j = i + 1; j < seeds.length; j++) {
      add(`${seeds[i]} ${seeds[j]}`);
      add(`${seeds[j]} ${seeds[i]}`);
    }
  }

  if (productWords.length && nicheWords.length) {
    add(`${productWords[0]} ${nicheWords[0]}`);
    add(`${nicheWords[0]} ${productWords[0]}`);
  }

  const productPhrase = productWords.slice(0, 3).join(" ");
  const nichePhrase = nicheWords.slice(0, 2).join(" ");
  if (productPhrase) add(productPhrase);
  if (nichePhrase) add(nichePhrase);
  if (productPhrase && nichePhrase) add(`${productPhrase} ${nicheWords[0]}`);

  for (const mod of LONG_TAIL_MODIFIERS) {
    if (productWords[0]) add(`${productWords[0]} ${mod}`);
    if (nicheWords[0]) add(`${nicheWords[0]} ${mod}`);
  }

  for (let i = 0; i < seedWords.length; i++) {
    for (let j = i + 1; j < seedWords.length; j++) {
      add(`${seedWords[i]} ${seedWords[j]}`);
    }
  }

  const filler = [
    ...productWords,
    ...nicheWords,
    ...seedWords,
    ...LONG_TAIL_MODIFIERS,
  ];

  for (const a of filler) {
    for (const b of filler) {
      if (a !== b) add(`${a} ${b}`);
    }
  }

  return [...candidates];
}

function selectTags(candidates, seedSet) {
  const seen = new Set();
  const ranked = candidates
    .map((tag) => ({ tag, score: scoreTag(tag, seedSet) }))
    .sort((a, b) => {
      if (b.score !== a.score) return b.score - a.score;
      return b.tag.length - a.tag.length;
    });

  const selected = [];
  for (const { tag } of ranked) {
    const key = normalizeKey(tag);
    if (seen.has(key)) continue;
    if (tag.length > MAX_TAG_LEN) continue;
    if (!/^[a-z0-9]/.test(tag)) continue;
    seen.add(key);
    selected.push(tag);
    if (selected.length >= TAG_COUNT) break;
  }

  if (selected.length < TAG_COUNT) {
    const extras = candidates
      .filter((tag) => !seen.has(normalizeKey(tag)))
      .sort((a, b) => b.length - a.length);
    for (const tag of extras) {
      const key = normalizeKey(tag);
      if (seen.has(key) || tag.length > MAX_TAG_LEN || tag.length < 3) continue;
      seen.add(key);
      selected.push(tag);
      if (selected.length >= TAG_COUNT) break;
    }
  }

  return selected.slice(0, TAG_COUNT);
}

function parseKeywords(raw) {
  return raw
    .split(",")
    .map((k) => k.trim())
    .filter(Boolean);
}

function validateForm(product, niche, keywords) {
  if (!product) return "Product name is required.";
  if (!niche) return "Niche is required.";
  if (keywords.length < 3) return "Enter at least 3 seed keywords (comma-separated).";
  if (keywords.length > 5) return "Maximum 5 seed keywords allowed.";
  return null;
}

function generateTags(product, niche, keywordsRaw) {
  const keywords = parseKeywords(keywordsRaw);
  const seedSet = new Set(keywords.flatMap(tokenize));
  const candidates = buildCandidates(product, niche, keywords);
  return selectTags(candidates, seedSet);
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

function showError(msg) {
  const el = document.getElementById("form-error");
  if (!msg) {
    el.classList.add("hidden");
    el.textContent = "";
    return;
  }
  el.textContent = msg;
  el.classList.remove("hidden");
}

function renderTags(tags) {
  const grid = document.getElementById("tag-grid");
  grid.innerHTML = "";

  tags.forEach((tag, i) => {
    const row = document.createElement("div");
    row.className = "tag-row" + (isLongTail(tag) ? " long-tail" : "");

    const text = document.createElement("span");
    text.className = "tag-text";
    text.textContent = `${i + 1}. ${tag}`;

    const meta = document.createElement("div");
    meta.className = "tag-meta";

    if (isLongTail(tag)) {
      const badge = document.createElement("span");
      badge.className = "badge";
      badge.textContent = "long-tail";
      meta.appendChild(badge);
    }

    const count = document.createElement("span");
    count.className = "char-count";
    const len = tag.length;
    count.textContent = `${len}/20`;
    if (len === MAX_TAG_LEN) count.classList.add("at-limit");
    if (len > MAX_TAG_LEN) count.classList.add("over-limit");
    meta.appendChild(count);

    const copyBtn = document.createElement("button");
    copyBtn.type = "button";
    copyBtn.className = "copy-btn";
    copyBtn.textContent = "Copy";
    copyBtn.addEventListener("click", () => {
      navigator.clipboard.writeText(tag);
      copyBtn.textContent = "Copied!";
      setTimeout(() => { copyBtn.textContent = "Copy"; }, 1200);
    });
    meta.appendChild(copyBtn);

    row.appendChild(text);
    row.appendChild(meta);
    grid.appendChild(row);
  });

  document.getElementById("results").classList.remove("hidden");
  document.getElementById("regenerate").disabled = false;
}

let lastInputs = null;

function runGeneration() {
  const product = document.getElementById("product-name").value.trim();
  const niche = document.getElementById("niche").value.trim();
  const keywordsRaw = document.getElementById("keywords").value.trim();
  const keywords = parseKeywords(keywordsRaw);

  const err = validateForm(product, niche, keywords);
  if (err) {
    showError(err);
    return;
  }
  showError("");

  const usage = getUsage();
  if (!isPro() && usage.count >= FREE_LIMIT) {
    if (window.SellerToolsPay) window.SellerToolsPay.buy("etsy-tag-finder-pro");
    else alert("Free limit reached. Pay Crypto $14 to unlock Pro.");
    return;
  }

  lastInputs = { product, niche, keywordsRaw };
  const tags = generateTags(product, niche, keywordsRaw);
  renderTags(tags);

  if (!isPro()) {
    setUsage(usage.count + 1);
  }
  updateUsageLabel();
}

document.getElementById("tag-form").addEventListener("submit", (e) => {
  e.preventDefault();
  runGeneration();
});

document.getElementById("regenerate").addEventListener("click", () => {
  if (!lastInputs) return;
  document.getElementById("product-name").value = lastInputs.product;
  document.getElementById("niche").value = lastInputs.niche;
  document.getElementById("keywords").value = lastInputs.keywordsRaw;
  runGeneration();
});

document.getElementById("copy-all").addEventListener("click", () => {
  const rows = document.querySelectorAll(".tag-text");
  const tags = [...rows].map((el) => el.textContent.replace(/^\d+\.\s*/, ""));
  navigator.clipboard.writeText(tags.join(", "));
  const btn = document.getElementById("copy-all");
  btn.textContent = "Copied!";
  setTimeout(() => { btn.textContent = "Copy all tags"; }, 1200);
});

function validLicense(key) {
  return (
    /^TAGFINDER-[A-Z0-9]{4}-[A-Z0-9]{4}$/.test(key) ||
    /^SELLERKIT-[A-Z0-9]{4}-[A-Z0-9]{4}$/.test(key)
  );
}

document.getElementById("unlock").addEventListener("click", () => {
  const key = document.getElementById("license-key").value.trim().toUpperCase();
  if (validLicense(key)) {
    localStorage.setItem(PRO_KEY, "true");
    updateUsageLabel();
    alert("Pro unlocked. Thank you!");
  } else {
    alert("Invalid license key. Pay crypto on site (format: TAGFINDER-XXXX-XXXX).");
  }
});

updateUsageLabel();

(function track() {
  const k = "tagfinder_pageviews";
  const n = (+localStorage.getItem(k) || 0) + 1;
  localStorage.setItem(k, n);
  const el = document.getElementById("analytics");
  if (el) el.textContent = `${n} local pageviews`;
})();