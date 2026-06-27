(function () {
  const cfg = window.GUMROAD || {};
  const products = cfg.products || {};

  function buyLink(slug) {
    const p = products[slug];
    if (!p || !p.url) return null;
    const a = document.createElement("a");
    a.className = "btn buy-pro";
    a.href = p.url;
    a.target = "_blank";
    a.rel = "noopener";
    a.textContent = `Buy Pro — $${p.price}`;
    return a;
  }

  document.querySelectorAll("[data-gumroad]").forEach((el) => {
    const slug = el.getAttribute("data-gumroad");
    const link = buyLink(slug);
    if (link) el.prepend(link);
  });

  const bundle = products["seller-kit-bundle"];
  if (bundle && bundle.url) {
    document.querySelectorAll("[data-gumroad-bundle]").forEach((el) => {
      const a = document.createElement("a");
      a.href = bundle.url;
      a.target = "_blank";
      a.rel = "noopener";
      a.textContent = `Seller Kit — $${bundle.price}`;
      el.appendChild(a);
    });
  }
})();