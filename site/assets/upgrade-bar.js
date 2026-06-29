(function () {
  if (document.getElementById("upgrade-bar")) return;

  const path = location.pathname;
  let product = "";
  let price = "";
  let label = "";

  if (path.includes("etsy-tag-finder")) {
    product = "etsy-tag-finder-pro";
    price = "$14";
    label = "Unlimited tags + CSV export";
  } else if (path.includes("listing-lab")) {
    product = "listinglab-pro";
    price = "$19";
    label = "Unlimited listings + bulk mode";
  } else {
    return;
  }

  const payhip = {
    "etsy-tag-finder-pro": "https://payhip.com/b/1oqbL",
    "listinglab-pro": "https://payhip.com/b/BQIej",
  }[product];

  const bar = document.createElement("div");
  bar.id = "upgrade-bar";
  bar.innerHTML =
    '<div class="upgrade-bar-inner">' +
    `<span class="upgrade-bar-text"><strong>Pro ${price} lifetime</strong> — ${label}. <em>1 free try/day</em> — upgrade for unlimited.</span>` +
    (payhip
      ? `<a class="upgrade-bar-card" href="${payhip}" target="_blank" rel="noopener">Buy with Card ${price}</a>`
      : "") +
    `<span class="upgrade-bar-actions" data-crypto-buy="${product}"></span>` +
    `<a class="upgrade-bar-deal" href="/deals/">All deals</a>` +
    '<button type="button" class="upgrade-bar-close" aria-label="Dismiss">×</button>' +
    "</div>";

  document.body.appendChild(bar);

  const close = bar.querySelector(".upgrade-bar-close");
  const key = "upgrade_bar_dismissed_" + product;
  if (sessionStorage.getItem(key)) bar.classList.add("hidden");
  close.addEventListener("click", () => {
    bar.classList.add("hidden");
    sessionStorage.setItem(key, "1");
  });

  const usage = document.getElementById("usage");
  if (usage) {
    const obs = new MutationObserver(() => {
      const t = usage.textContent || "";
      if (/0 free|no free|limit/i.test(t)) bar.classList.add("urgent");
    });
    obs.observe(usage, { childList: true, characterData: true, subtree: true });
  }
})();