(function () {
  const SITE = "https://leopreciadov-bit.github.io/seller-tools";
  const ATTRIBUTION = `\n\n— Generated with Seller Tools: ${SITE}/`;

  function appendAttribution(text) {
    if (text.includes("Seller Tools")) return text;
    return text + ATTRIBUTION;
  }

  document.addEventListener("click", (e) => {
    const btn = e.target.closest("#copy-all, .copy-btn");
    if (!btn) return;
    setTimeout(() => {
      const rows = document.querySelectorAll(".tag-text, #listing-title, #listing-description");
      if (!rows.length) return;
    }, 50);
  });

  const orig = navigator.clipboard.writeText.bind(navigator.clipboard);
  navigator.clipboard.writeText = function (text) {
    if (typeof text === "string" && text.length > 20 && !text.includes("Seller Tools")) {
      const path = location.pathname;
      if (path.includes("etsy-tag-finder") || path.includes("listing-lab")) {
        return orig(appendAttribution(text));
      }
    }
    return orig(text);
  };
})();