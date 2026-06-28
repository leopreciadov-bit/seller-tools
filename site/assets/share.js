(function () {
  const cfg = window.SEO || {};
  const base = (cfg.baseUrl || window.location.origin + window.location.pathname.replace(/\/[^/]*$/, "/")).replace(/\/$/, "");
  const pageUrl = window.location.href.split("#")[0];
  const title = document.title || "Seller Tools";
  const text = "Free Etsy & Shopify listing generators — no signup";

  const links = {
    twitter: `https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}&url=${encodeURIComponent(pageUrl)}`,
    reddit: `https://www.reddit.com/submit?title=${encodeURIComponent(title)}&url=${encodeURIComponent(pageUrl)}`,
    facebook: `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(pageUrl)}`,
    linkedin: `https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(pageUrl)}`,
    hackernews: `https://news.ycombinator.com/submitlink?u=${encodeURIComponent(pageUrl)}&t=${encodeURIComponent(title)}`,
  };

  function mount(el) {
    if (!el) return;
    el.innerHTML = `
      <div class="share-bar" role="group" aria-label="Share this tool">
        <span class="share-label">Share</span>
        <a class="share-btn" href="${links.twitter}" target="_blank" rel="noopener noreferrer">X</a>
        <a class="share-btn" href="${links.reddit}" target="_blank" rel="noopener noreferrer">Reddit</a>
        <a class="share-btn" href="${links.facebook}" target="_blank" rel="noopener noreferrer">Facebook</a>
        <a class="share-btn" href="${links.linkedin}" target="_blank" rel="noopener noreferrer">LinkedIn</a>
        <a class="share-btn" href="${links.hackernews}" target="_blank" rel="noopener noreferrer">HN</a>
      </div>`;
  }

  document.querySelectorAll("[data-share]").forEach(mount);

  if (!document.querySelector("[data-share]")) {
    const footer = document.querySelector("footer p, footer");
    if (footer) {
      const div = document.createElement("div");
      div.setAttribute("data-share", "");
      footer.parentNode.insertBefore(div, footer);
      mount(div);
    }
  }
})();