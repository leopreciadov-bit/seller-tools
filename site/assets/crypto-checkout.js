(function () {
  const cfg = window.CRYPTO || {};
  const payout = cfg.payout_address || "";
  const methods = cfg.methods || {};
  const products = cfg.products || {};
  const keyPool = cfg.keyPool || {};
  const cardCfg = cfg.card || {};
  const preferred = cfg.preferred || "usdc_sol";

  let rates = {};
  let helioScriptLoaded = false;

  async function fetchRates() {
    const ids = [...new Set(
      Object.entries(methods)
        .filter(([k]) => k !== "card")
        .map(([, m]) => m.coingecko)
        .filter(Boolean)
    )];
    if (!ids.length) return;
    try {
      const r = await fetch(
        `https://api.coingecko.com/api/v3/simple/price?ids=${ids.join(",")}&vs_currencies=usd`
      );
      const data = await r.json();
      for (const [key, m] of Object.entries(methods)) {
        if (key === "card") continue;
        if (m.coingecko && data[m.coingecko]?.usd) rates[key] = data[m.coingecko].usd;
      }
    } catch (_) {
      for (const [key, m] of Object.entries(methods)) {
        if (m.stablecoin) rates[key] = 1;
      }
    }
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

  function grantKey(slug, ref) {
    const paidKey = `crypto_paid_${slug}`;
    const last = parseInt(localStorage.getItem(paidKey) || "0", 10);
    const now = Date.now();
    if (now - last < 86400000 && localStorage.getItem(`crypto_license_${slug}`)) {
      return localStorage.getItem(`crypto_license_${slug}`);
    }
    const key = nextKey(slug);
    if (!key) return null;
    localStorage.setItem(paidKey, String(now));
    localStorage.setItem(`crypto_license_${slug}`, key);
    return key;
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
    if (!payout || !m?.direct || m.card) return null;
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

  function cardProvider() {
    const p = cardCfg.provider || "auto";
    if (p !== "auto") return p;
    if (cardCfg.helio_paylink_id) return "helio";
    if (cardCfg.transak_api_key) return "transak";
    if (cardCfg.moonpay_publishable_key) return "moonpay";
    return null;
  }

  function transakUrl(usd, ref) {
    const key = cardCfg.transak_api_key;
    if (!key) return null;
    const params = new URLSearchParams({
      apiKey: key,
      walletAddress: payout,
      cryptoCurrencyCode: "USDC",
      network: "solana",
      fiatCurrency: "USD",
      fiatAmount: String(usd),
      disableWalletAddressForm: "true",
      hideMenu: "true",
      partnerOrderId: ref,
      productsAvailed: "BUY",
      referrerDomain: location.hostname,
    });
    return `https://global.transak.com/?${params}`;
  }

  function moonpayUrl(usd, ref) {
    const key = cardCfg.moonpay_publishable_key;
    if (!key) return null;
    const params = new URLSearchParams({
      apiKey: key,
      currencyCode: "usdc_sol",
      walletAddress: payout,
      baseCurrencyAmount: String(usd),
      externalTransactionId: ref,
      showWalletAddressForm: "false",
    });
    return `https://buy.moonpay.com?${params}`;
  }

  function loadHelioScript() {
    return new Promise((resolve, reject) => {
      if (helioScriptLoaded && window.helioCheckout) return resolve();
      const s = document.createElement("script");
      s.src = "https://embed.hel.io/assets/index-vanilla.js";
      s.type = "module";
      s.onload = () => {
        helioScriptLoaded = true;
        resolve();
      };
      s.onerror = reject;
      document.head.appendChild(s);
    });
  }

  function mountHelio(container, usd, ref, onSuccess) {
    const id = cardCfg.helio_paylink_id;
    if (!id) return false;
    container.innerHTML = `<div id="helio-root-${ref}" style="min-height:420px"></div>`;
    const root = container.querySelector(`#helio-root-${ref}`);

    const config = {
      paylinkId: id,
      amount: String(usd),
      primaryPaymentMethod: "fiat",
      display: "inline",
      theme: { themeMode: "dark" },
      additionalJSON: { orderRef: ref, payout },
      onSuccess: () => onSuccess(),
      onError: (e) => console.warn("Helio error", e),
    };

    const tryMount = () => {
      const fn = window.helioCheckout || window.MoonpayCommerceCheckout || window.checkout;
      if (typeof fn === "function") {
        fn(root, config);
        return true;
      }
      return false;
    };

    if (tryMount()) return true;

    loadHelioScript()
      .then(() => {
        if (!tryMount()) {
          root.innerHTML = `<a class="btn-crypto" href="https://moonpay.hel.io/pay/${id}?amount=${usd}" target="_blank" rel="noopener">Pay $${usd} with card →</a>
            <p class="muted">Opens secure checkout. USDC sent to seller Solana wallet.</p>`;
        }
      })
      .catch(() => {
        root.innerHTML = `<a class="btn-crypto" href="https://moonpay.hel.io/pay/${id}?amount=${usd}" target="_blank" rel="noopener">Pay $${usd} with card →</a>`;
      });
    return true;
  }

  function cardSetupHtml() {
    return `<div class="crypto-bridge-notice">
      <strong>One-time setup</strong> (5 min) to accept cards → USDC on your Solana wallet:
      <ol style="margin:0.5rem 0 0 1rem;padding:0">
        <li>Create free account at <a href="https://moonpay.hel.io" target="_blank" rel="noopener">moonpay.hel.io</a></li>
        <li>Connect payout wallet: <code>${payout.slice(0, 12)}…</code></li>
        <li>Create <strong>Dynamic</strong> pay link (USDC on Solana)</li>
        <li>Run: <code>python3 scripts/crypto_setup.py set-card --helio YOUR_PAYLINK_ID</code></li>
      </ol>
      <p style="margin-top:0.5rem">Or use Transak: <code>set-card --transak YOUR_API_KEY</code></p>
    </div>`;
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

    function showKey(key) {
      const el = modal.querySelector("#key-reveal");
      if (!el) return;
      el.innerHTML = `
        <div class="crypto-key-reveal">
          <p><strong>Your license key:</strong></p>
          <code>${key}</code>
          <div class="crypto-row" style="margin-top:0.5rem">
            <button type="button" id="copy-key">Copy key</button>
            <button type="button" id="apply-key">Unlock now</button>
          </div>
        </div>`;
      el.querySelector("#copy-key").addEventListener("click", () => copyText(key));
      el.querySelector("#apply-key").addEventListener("click", () => {
        const input = document.getElementById("license-key");
        const unlock = document.getElementById("unlock");
        if (input) input.value = key;
        if (unlock) unlock.click();
        overlay.remove();
      });
    }

    function onPaid() {
      const key = grantKey(slug, ref);
      if (key) showKey(key);
      else {
        modal.querySelector("#key-reveal").innerHTML =
          `<p class="muted">Contact ${cfg.contact || "seller"} with ref ${ref}.</p>`;
      }
    }

    function render() {
      const m = methods[active] || {};
      const isCard = active === "card";
      modal.classList.toggle("crypto-modal-wide", isCard);

      if (isCard) {
        const provider = cardProvider();
        modal.innerHTML = `
          <h3>${prod.title || slug} — $${usd}</h3>
          <p class="muted">Pay with card · USDC settles to seller Solana wallet</p>
          <div class="crypto-tabs" id="crypto-tabs"></div>
          <p class="crypto-amount">$${usd} USD <span class="muted">→ USDC on Solana</span></p>
          <p class="crypto-ref">Order ref: <strong>${ref}</strong></p>
          <p class="crypto-settle-foot">Your payout: <code>${payout.slice(0, 8)}…${payout.slice(-6)}</code></p>
          <div id="card-widget"></div>
          <div class="crypto-row">
            <button type="button" class="btn-crypto" id="confirm-paid">Payment complete — get license key</button>
            <button type="button" class="secondary" id="crypto-close">Close</button>
          </div>
          <div id="key-reveal"></div>`;

        const widget = modal.querySelector("#card-widget");
        let mounted = false;

        if (provider === "helio") {
          mounted = mountHelio(widget, usd, ref, onPaid);
        } else if (provider === "transak") {
          const url = transakUrl(usd, ref);
          widget.innerHTML = `<iframe class="crypto-card-iframe" src="${url}" allow="camera;microphone;payment"></iframe>`;
          mounted = true;
        } else if (provider === "moonpay") {
          const url = moonpayUrl(usd, ref);
          widget.innerHTML = `<iframe class="crypto-card-iframe" src="${url}" allow="payment"></iframe>`;
          mounted = true;
        }

        if (!mounted) widget.innerHTML = cardSetupHtml();
      } else {
        const amt = cryptoAmount(usd, active);
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
                 </div>`
          }
          <div class="crypto-wallet" id="wallet-addr">${payout}</div>
          <div class="crypto-row">
            <button type="button" id="copy-addr">Copy Solana address</button>
            <button type="button" id="copy-amt">Copy amount</button>
            ${payUrl ? `<a class="btn-crypto" id="open-wallet" href="${payUrl}">Open wallet</a>` : ""}
            ${m.bridge_url && !direct ? `<a class="secondary" href="${m.bridge_url}" target="_blank" rel="noopener" style="display:inline-block;padding:0.55rem 0.9rem;border-radius:8px;border:1px solid #2a3142;text-decoration:none;color:#e8ecf4">Swap & pay</a>` : ""}
          </div>
          <p class="crypto-settle-foot">Payout: <code>${payout.slice(0, 8)}…${payout.slice(-6)}</code></p>
          <div class="crypto-row">
            <button type="button" class="btn-crypto" id="confirm-paid">I sent payment — get license key</button>
            <button type="button" class="secondary" id="crypto-close">Close</button>
          </div>
          <div id="key-reveal"></div>`;

        modal.querySelector("#copy-addr")?.addEventListener("click", () => copyText(payout));
        modal.querySelector("#copy-amt")?.addEventListener("click", () => copyText(amt));
      }

      const tabs = modal.querySelector("#crypto-tabs");
      Object.keys(methods).forEach((key) => {
        const b = document.createElement("button");
        b.type = "button";
        const meta = methods[key];
        b.textContent = meta.sublabel ? `${meta.label} · ${meta.sublabel}` : meta.label;
        if (key === active) b.classList.add("active");
        b.addEventListener("click", () => {
          active = key;
          render();
        });
        tabs.appendChild(b);
      });

      modal.querySelector("#crypto-close")?.addEventListener("click", () => overlay.remove());
      modal.querySelector("#confirm-paid")?.addEventListener("click", onPaid);
    }

    window.addEventListener("message", function transakListener(event) {
      if (!overlay.isConnected) {
        window.removeEventListener("message", transakListener);
        return;
      }
      if (event?.data?.event_id === "TRANSAK_ORDER_SUCCESSFUL") onPaid();
    });

    overlay.addEventListener("click", (e) => {
      if (e.target === overlay) overlay.remove();
    });

    overlay.appendChild(modal);
    document.body.appendChild(overlay);
    render();
  }

  function buyButton(slug, label) {
    const prod = products[slug];
    if (!prod || !payout) return null;
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = label === "card" ? "btn buy-card" : "btn buy-crypto";
    btn.textContent = label === "card" ? `Pay Card — $${prod.price_usd}` : `Pay Crypto — $${prod.price_usd}`;
    btn.addEventListener("click", () => openModal(slug));
    return btn;
  }

  fetchRates();

  document.querySelectorAll("[data-crypto]").forEach((el) => {
    const slug = el.getAttribute("data-crypto");
    const cardBtn = buyButton(slug, "card");
    const cryptoBtn = buyButton(slug, "crypto");
    if (cardBtn) el.prepend(cardBtn);
    if (cryptoBtn) el.prepend(cryptoBtn);
  });

  document.querySelectorAll("[data-crypto-bundle]").forEach((el) => {
    const cardBtn = buyButton("seller-kit-bundle", "card");
    const cryptoBtn = buyButton("seller-kit-bundle", "crypto");
    if (cardBtn) {
      cardBtn.textContent = `Card — $${products["seller-kit-bundle"]?.price_usd || 29}`;
      el.appendChild(cardBtn);
    }
    if (cryptoBtn) {
      cryptoBtn.textContent = `Crypto — $${products["seller-kit-bundle"]?.price_usd || 29}`;
      el.appendChild(cryptoBtn);
    }
  });
})();