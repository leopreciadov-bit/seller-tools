/**
 * Shared SEO helpers — sets canonical + OG URLs from current origin.
 * Include in <head> before </head> on every page.
 */
(function () {
  const origin = window.location.origin;
  const path = window.location.pathname.replace(/\/$/, "") || "/";
  const url = origin + path;

  function setMeta(attr, key, value) {
    let el = document.querySelector(`meta[${attr}="${key}"]`);
    if (!el) {
      el = document.createElement("meta");
      el.setAttribute(attr, key);
      document.head.appendChild(el);
    }
    el.setAttribute("content", value);
  }

  function setLink(rel, href) {
    let el = document.querySelector(`link[rel="${rel}"]`);
    if (!el) {
      el = document.createElement("link");
      el.setAttribute("rel", rel);
      document.head.appendChild(el);
    }
    el.setAttribute("href", href);
  }

  setLink("canonical", url);
  setMeta("property", "og:url", url);
  setMeta("name", "twitter:url", url);

  const ogImage = origin + "/assets/og-card.svg";
  setMeta("property", "og:image", ogImage);
  setMeta("name", "twitter:image", ogImage);
})();