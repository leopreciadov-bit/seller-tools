(function () {
  const SITE = "https://leopreciadov-bit.github.io/seller-tools";
  const TAG_TOOL = SITE + "/etsy-tag-finder/";
  const LIST_TOOL = SITE + "/listing-lab/";

  function textOf(sel) {
    const el = document.querySelector(sel);
    return el ? (el.value || el.textContent || "").trim() : "";
  }

  function scrapeListing() {
    const title =
      textOf('input[name="title"]') ||
      textOf("#title") ||
      textOf('[data-testid="title-input"]') ||
      textOf('textarea[name="title"]') ||
      "";
    const description =
      textOf('textarea[name="description"]') ||
      textOf("#description") ||
      textOf('[data-testid="description-textarea"]') ||
      "";
    const tags = [];
    document.querySelectorAll('input[name*="tag"], [data-testid*="tag"] input, .tag-input input').forEach((inp) => {
      const v = (inp.value || "").trim();
      if (v) tags.push(v);
    });
    return { title, description, tags };
  }

  function buildTagUrl(data) {
    const product = data.title.split(/[|\-–]/)[0].trim().slice(0, 80) || "handmade product";
    const niche = data.description.split(/[.!?]/)[0].trim().slice(0, 60) || "etsy handmade";
    const seeds = data.tags.length
      ? data.tags.slice(0, 5).join(", ")
      : product.split(/\s+/).slice(0, 4).join(", ");
    const q = new URLSearchParams({ product, niche, keywords: seeds });
    return TAG_TOOL + "?" + q.toString();
  }

  function buildListingUrl(data) {
    const q = new URLSearchParams({
      product: data.title.slice(0, 80) || "product",
      niche: "etsy shop",
      keywords: data.tags.slice(0, 5).join(", ") || "handmade gift",
    });
    return LIST_TOOL + "?" + q.toString();
  }

  function pasteTags(tags) {
    const inputs = document.querySelectorAll(
      'input[name*="tag"], [data-testid*="tag"] input, .tag-input input, input[placeholder*="tag" i]'
    );
    if (!inputs.length) return false;
    tags.slice(0, 13).forEach((tag, i) => {
      if (inputs[i]) {
        inputs[i].value = tag.slice(0, 20);
        inputs[i].dispatchEvent(new Event("input", { bubbles: true }));
        inputs[i].dispatchEvent(new Event("change", { bubbles: true }));
      }
    });
    return true;
  }

  function panel() {
    if (document.getElementById("seller-tools-panel")) return;
    const data = scrapeListing();
    const wrap = document.createElement("div");
    wrap.id = "seller-tools-panel";
    wrap.innerHTML = `
      <div class="st-header">Seller Tools</div>
      <button type="button" id="st-tags">13 SEO Tags</button>
      <button type="button" id="st-listing">Full Listing</button>
      <button type="button" id="st-paste">Paste Tags</button>
      <a href="${SITE}/deals/" target="_blank" rel="noopener" class="st-pro">Pro $14</a>
    `;
    document.body.appendChild(wrap);

    wrap.querySelector("#st-tags").addEventListener("click", () => {
      window.open(buildTagUrl(scrapeListing()), "_blank");
    });
    wrap.querySelector("#st-listing").addEventListener("click", () => {
      window.open(buildListingUrl(scrapeListing()), "_blank");
    });
    wrap.querySelector("#st-paste").addEventListener("click", async () => {
      try {
        const raw = await navigator.clipboard.readText();
        const tags = raw.split(/[,\n]/).map((t) => t.trim()).filter(Boolean);
        if (pasteTags(tags)) {
          wrap.querySelector("#st-paste").textContent = "Pasted!";
          setTimeout(() => { wrap.querySelector("#st-paste").textContent = "Paste Tags"; }, 1500);
        } else {
          alert("Copy tags from Seller Tools first, then click Paste Tags on Etsy listing editor.");
        }
      } catch (_) {
        alert("Allow clipboard access, copy tags from Seller Tools, then click Paste.");
      }
    });
  }

  if (/etsy\.com\/your\/shops/i.test(location.href) || /listing-editor/i.test(location.href)) {
    panel();
  }
})();