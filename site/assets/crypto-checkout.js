(function () {
  const cfg = window.CRYPTO || {};
  const payout = cfg.payout_address || "";
  const methods = cfg.methods || {};
  const products = cfg.products || {};
  const keyPool = cfg.keyPool || {};
  const preferred = cfg.preferred || "usdc_sol";

  let rates = {};

  async function fetchRates() {
    const ids = [...new Set(Object.values(methods).map((m) => m.coingecko).filter(Boolean))];
    if (!ids.length) return;
    try {
      const r = await fetch(
        `https://api.coingecko.com/api/v3/simple/price?ids=${ids.join(",")}&vs_currencies=usd`
      );
      const data = await r.json();
      for (const [key, m] of Object.entries(methods)) {
        if (m.coingecko && data[m.coingecko]?.usd) rates[key] = data[m.coingecko].usd;
      }
    } catch (_) {
      for (const [key, m] of Object.entries(methods)) {
        if (m.stablecoin) rates[key] = 1;
      }
    }
  }

  function methodLabel(key) {
    const m = methods[key];
    if (!m) return key;
    return m.sublabel ? `${m.label} (${m.sublabel})` : m.label;
  }

  function orderRef(slug) {
    const k = `crypto_order_${slug}`;
    let ref = localStorage.getItem(k);
    if (!ref) {
      ref = Math.random().toString(36).slice(2, 8).toUpperCase();
      localStorage.setItem(k, ref);
    }
    return ref;
  }

  function nextKey(slug) {
    const pool = keyPool[slug] || [];
    if (!pool.length) return null;
    const idxKey = `crypto_key_idx_${slug}`;
    const idx = parseInt(localStorage.getItem(idxKey) || "0", 10);
    if (idx >= pool.length) return null;
    localStorage.setItem(idxKey, String(idx + 1));
    return pool[idx];
  }

  function copyText(text) {
    navigator.clipboard.writeText(text).catch(() => {});
  }

  function cryptoAmount(usd, key) {
    const m = methods[key];
    const rate = rates[key] || (m?.stablecoin ? 1 : 0);
    if (m?.stablecoin || rate <= 0) return usd.toFixed(2);
    return (usd / rate).toFixed(8).replace(/\.?0+$/, "");
  }

  function solanaPayUrl(key, amount, ref) {
    const m = methods[key];
    if (!payout || !m?.direct) return null;
    const params = new URLSearchParams();
    params.set("label", `SellerTools ${ref}`);
    if (m.spl_mint) {
      params.set("spl-token", m.spl_mint);
      params.set("amount", amount);
    } else if (key === "sol") {
      params.set("amount", amount);
    }
    return `solana:${payout}?${params.toString()}`;
  }

  function openModal(slug) {
    const prod = products[slug];
    if (!prod || !payout) return;

    const overlay = document.createElement("div");
    overlay.className = "crypto-overlay";
    const modal = document.createElement("div");
    modal.className = "crypto-modal";

    let active = methods[preferred] ? preferred : Object.keys(methods)[0];
    const ref = orderRef(slug);
    const usd = prod.price_usd;

    function render() {
      const m = methods[active] || {};
      const amt = cryptoAmount(usd, active);
      const label = methodLabel(active);
      const direct = !!m.direct;
      const payUrl = solanaPayUrl(active, amt, ref);

      modal.innerHTML = `
        <h3>${prod.title || slug} — $${usd}</h3>
        <p class="muted">All payments settle to one Solana wallet.</p>
        <div class="crypto-tabs" id="crypto-tabs"></div>
        <p class="crypto-amount">${amt} ${m.label || active}${m.sublabel ? ` <span class="muted">on ${m.sublabel}</span>` : ""}</p>
        <p class="crypto-ref">Order ref: <strong>${ref}</strong></p>
        ${
          direct
            ? `<p class="crypto-settle">Send directly to Solana address:</p>`
            : `<div class="crypto-bridge-notice">
                 <strong>Cross-chain:</strong> Don't send ${m.label} to this Solana address.
                 <a href="${m.bridge_url || "#"}" target="_blank" rel="noopener">Swap → USDC on Solana</a>
                 (auto-delivers to seller wallet) or send equivalent USDC/SOL below.
               </div>`
        }
        <div class="crypto-wallet" id="wallet-addr">${payout}</div>
        <div class="crypto-row">
          <button type="button" id="copy-addr">Copy Solana address</button>
          <button type="button" id="copy-amt">Copy amount</button>
          ${payUrl ? `<a class="btn-crypto" id="open-wallet" href="${payUrl}">Open wallet</a>` : ""}
          ${m.bridge_url && !direct ? `<a class="secondary" href="${m.bridge_url}" target="_blank" rel="noopener" style="display:inline-block;padding:0.55rem 0.9rem;border-radius:8px;border:1px solid #2a3142;text-decoration:none;color:#e8ecf4">Swap & pay</a>` : ""}
        </div>
        <p class="crypto-settle-foot">Payout wallet: <code>${payout.slice(0, 8)}…${payout.slice(-6)}</code></p>
        <div class="crypto-row">
          <button type="button" class="btn-crypto" id="confirm-paid">I sent payment — get license key</button>
          <button type="button" class="secondary" id="crypto-close">Close</button>
        </div>
        <div id="key-reveal"></div>
      `;

      const tabs = modal.querySelector("#crypto-tabs");
      Object.keys(methods).forEach((key) => {
        const b = document.createElement("button");
        b.type = "button";
        const meta = methods[key];
        b.textContent = meta.sublabel ? `${meta.label} · ${meta.sublabel}` : meta.label;
        b.title = meta.direct ? "Direct to Solana" : "Swap to Solana";
        if (key === active) b.classList.add("active");
        b.addEventListener("click", () => {
          active = key;
          render();
        });
        tabs.appendChild(b);
      });

      modal.querySelector("#copy-addr")?.addEventListener("click", () => copyText(payout));
      modal.querySelector("#copy-amt")?.addEventListener("click", () => copyText(amt));
      modal.querySelector("#crypto-close")?.addEventListener("click", () => overlay.remove());
      modal.querySelector("#confirm-paid")?.addEventListener("click", () => {
        const paidKey = `crypto_paid_${slug}`;
        const last = parseInt(localStorage.getItem(paidKey) || "0", 10);
        const now = Date.now();
        if (now - last < 86400000 && localStorage.getItem(`crypto_license_${slug}`)) {
          showKey(localStorage.getItem(`crypto_license_${slug}`));
          return;
        }
        const key = nextKey(slug);
        if (!key) {
          modal.querySelector("#key-reveal").innerHTML =
            `<p class="muted">Contact ${cfg.contact || "seller"} with ref ${ref} for your key.</p>`;
          return;
        }
        localStorage.setItem(paidKey, String(now));
        localStorage.setItem(`crypto_license_${slug}`, key);
        showKey(key);
      });
    }

    function showKey(key) {
      modal.querySelector("#key-reveal").innerHTML = `
        <div class="crypto-key-reveal">
          <p><strong>Your license key:</strong></p>
          <code>${key}</code>
          <div class="crypto-row" style="margin-top:0.5rem">
            <button type="button" id="copy-key">Copy key</button>
            <button type="button" id="apply-key">Unlock now</button>
          </div>
        </div>`;
      modal.querySelector("#copy-key").addEventListener("click", () => copyText(key));
      modal.querySelector("#apply-key").addEventListener("click", () => {
        const input = document.getElementById("license-key");
        const unlock = document.getElementById("unlock");
        if (input) input.value = key;
        if (unlock) unlock.click();
        overlay.remove();
      });
    }

    overlay.addEventListener("click", (e) => {
      if (e.target === overlay) overlay.remove();
    });

    overlay.appendChild(modal);
    document.body.appendChild(overlay);
    render();
  }

  function buyButton(slug) {
    const prod = products[slug];
    if (!prod || !payout) return null;
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "btn buy-crypto";
    btn.textContent = `Pay Crypto — $${prod.price_usd}`;
    btn.addEventListener("click", () => openModal(slug));
    return btn;
  }

  fetchRates();

  document.querySelectorAll("[data-crypto]").forEach((el) => {
    const slug = el.getAttribute("data-crypto");
    const btn = buyButton(slug);
    if (btn) el.prepend(btn);
  });

  document.querySelectorAll("[data-crypto-bundle]").forEach((el) => {
    const btn = buyButton("seller-kit-bundle");
    if (btn) {
      btn.textContent = `Bundle — $${products["seller-kit-bundle"]?.price_usd || 29} crypto`;
      el.appendChild(btn);
    }
  });
})();