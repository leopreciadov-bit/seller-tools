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
  const USDC_MINT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v";
  const USDT_MINT = "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB";
  const LAMPORTS = 1_000_000_000;
  const DIRECT_ONLY = cfg.direct_only !== false;
  const BLOCKED_PROGRAMS = new Set([
    "PERPHjGBqRHArX4DySjwM6UJHiR3sWAatqfdBS2qQJu",
    "JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4",
    "JUP4Fb2cqiRUcaTHdrPC8h2gNsA2ETXiPDD33WcGuJB",
    "DoVEsk76QybCEHQGzkvYPWLQu9gzNoZZZt3TPiL597e",
  ]);
  const BLOCKED_LOGS = [
    "InstantDecreasePosition",
    "InstantIncreasePosition",
    "SwapWithTokenLedger",
    "shared_accounts_route",
    "Instruction: Route",
  ];

  function payMethods() {
    if (!DIRECT_ONLY) return methods;
    const out = {};
    for (const [k, m] of Object.entries(methods)) {
      if (m.direct && !m.bridge_url) out[k] = m;
    }
    return out;
  }
  const RPC_URLS = [
    "https://solana-rpc.publicnode.com",
    "https://rpc.ankr.com/solana",
  ];

  async function solanaRpc(method, params) {
    for (const url of RPC_URLS) {
      try {
        const r = await fetch(url, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ jsonrpc: "2.0", id: 1, method, params }),
        });
        const j = await r.json();
        if (j.result !== undefined) return j.result;
      } catch (_) {}
    }
    return null;
  }

  function inAmountRange(deltaUsd, usd) {
    return deltaUsd >= usd * 0.85 && deltaUsd <= usd * 1.15;
  }

  function txAccountKeys(tx) {
    return (tx?.transaction?.message?.accountKeys || []).map((k) =>
      typeof k === "string" ? k : k.pubkey
    );
  }

  function isDirectPayment(tx) {
    if (!tx?.meta) return false;
    const keys = txAccountKeys(tx);
    if (!keys.length || keys[0] === payout) return false;
    if (keys.some((k) => BLOCKED_PROGRAMS.has(k))) return false;
    for (const log of tx.meta.logMessages || []) {
      if (BLOCKED_LOGS.some((m) => log.includes(m))) return false;
    }
    const pre = {};
    for (const t of tx.meta.preTokenBalances || []) {
      if (t.owner === payout) pre[t.mint] = parseFloat(t.uiTokenAmount?.uiAmount || 0);
    }
    let inbound = false;
    for (const t of tx.meta.postTokenBalances || []) {
      if (t.owner !== payout) continue;
      if (t.mint !== USDC_MINT && t.mint !== USDT_MINT) continue;
      const delta = parseFloat(t.uiTokenAmount?.uiAmount || 0) - (pre[t.mint] || 0);
      if (delta < -0.001) return false;
      if (delta > 0.001) inbound = true;
    }
    const idx = keys.indexOf(payout);
    if (idx >= 0 && tx.meta.preBalances && tx.meta.postBalances) {
      const lam = tx.meta.postBalances[idx] - tx.meta.preBalances[idx];
      if (lam < -1_000_000) return false;
      if (lam > 1_000_000) inbound = true;
    }
    return inbound;
  }

  function txInboundUsd(tx) {
    if (!isDirectPayment(tx)) return 0;
    const keys = txAccountKeys(tx);
    const idx = keys.indexOf(payout);
    const pre = {};
    for (const t of tx.meta.preTokenBalances || []) {
      if (t.owner === payout) pre[t.mint] = parseFloat(t.uiTokenAmount?.uiAmount || 0);
    }
    let best = 0;
    for (const t of tx.meta.postTokenBalances || []) {
      if (t.owner !== payout) continue;
      const delta = parseFloat(t.uiTokenAmount?.uiAmount || 0) - (pre[t.mint] || 0);
      if (delta <= 0) continue;
      if (t.mint === USDC_MINT || t.mint === USDT_MINT) best = Math.max(best, delta);
    }
    const solRate = rates.sol || 0;
    if (solRate > 0 && idx >= 0 && tx.meta.preBalances && tx.meta.postBalances) {
      const lamportDelta = tx.meta.postBalances[idx] - tx.meta.preBalances[idx];
      if (lamportDelta > 0) best = Math.max(best, (lamportDelta / LAMPORTS) * solRate);
    }
    return best;
  }

  async function verifyPayment(usd) {
    const since = Math.floor(Date.now() / 1000) - 7200;
    const sigs = await solanaRpc("getSignaturesForAddress", [payout, { limit: 40 }]);
    if (!sigs) return false;
    for (const s of sigs) {
      if (s.err || (s.blockTime && s.blockTime < since)) continue;
      const tx = await solanaRpc("getTransaction", [
        s.signature,
        { encoding: "jsonParsed", maxSupportedTransactionVersion: 0 },
      ]);
      if (inAmountRange(txInboundUsd(tx), usd)) return true;
    }
    return false;
  }

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

  function bridgeUrl(methodKey, usd) {
    const m = methods[methodKey];
    if (!m?.bridge_url) return null;
    try {
      const u = new URL(m.bridge_url);
      const amt = cryptoAmount(usd, methodKey);
      u.searchParams.set("amount", amt);
      return u.toString();
    } catch (_) {
      return m.bridge_url;
    }
  }

  function defaultMethod() {
    const m = payMethods();
    if (cardCfg.enabled !== false && cardProvider() && m.card) return "card";
    return m[preferred] ? preferred : "usdc_sol";
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

  function cardSetupHtml(slug) {
    const gum = window.GUMROAD || {};
    const gp = gum.products && gum.products[slug];
    const gumUrl = gp && gp.url && !gp.url.includes("YOURNAME") ? gp.url : null;
    const deals = "https://leopreciadov-bit.github.io/seller-tools/deals/";
    return `<div class="crypto-bridge-notice">
      <strong>Pay with card</strong>
      ${
        gumUrl
          ? `<p style="margin-top:0.5rem"><a class="btn-crypto" href="${gumUrl}" target="_blank" rel="noopener">Buy on Gumroad — card/PayPal</a></p>`
          : `<p style="margin-top:0.5rem"><a class="btn-crypto" href="${deals}" target="_blank" rel="noopener">Deals page — card + crypto</a></p>`
      }
      <p>Or switch to <strong>USDC / USDT / SOL</strong> tab — send directly to Solana wallet.</p>
      <p class="muted">Payout: <code>${payout.slice(0, 8)}…${payout.slice(-6)}</code></p>
    </div>`;
  }

  function openModal(slug, startMethod) {
    const prod = products[slug];
    if (!prod || !payout) return;

    const overlay = document.createElement("div");
    overlay.className = "crypto-overlay";
    const modal = document.createElement("div");
    modal.className = "crypto-modal";

    const allowed = payMethods();
    let active = startMethod && allowed[startMethod] ? startMethod : defaultMethod();
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

    async function onPaid() {
      const reveal = modal.querySelector("#key-reveal");
      const btn = modal.querySelector("#confirm-paid");
      const cached = localStorage.getItem(`crypto_license_${slug}`);
      if (cached) {
        showKey(cached);
        return;
      }
      if (btn) {
        btn.disabled = true;
        btn.textContent = "Checking payment on Solana…";
      }
      if (reveal) reveal.innerHTML = `<p class="muted">Looking for your payment on Solana (card → USDC, crypto direct, last 2 hours)…</p>`;

      let ok = false;
      for (let i = 0; i < 6; i++) {
        ok = await verifyPayment(usd);
        if (ok) break;
        if (reveal) reveal.innerHTML = `<p class="muted">Not confirmed yet — retrying (${i + 1}/6)…</p>`;
        await new Promise((r) => setTimeout(r, 5000));
      }

      if (!ok) {
        if (reveal) {
          reveal.innerHTML = `
            <div class="crypto-bridge-notice">
              <strong>Payment not detected yet.</strong>
              <ol style="margin:0.5rem 0 0 1rem;padding:0">
                <li>Pay <strong>$${usd}</strong> via card or crypto — all methods settle to the Solana address above</li>
                <li>Wait ~30 seconds for confirmation</li>
                <li>Click this button again <strong>on this same browser</strong></li>
              </ol>
              <p style="margin-top:0.5rem">Order ref: <strong>${ref}</strong><br>
              Paid but stuck? Email <a href="mailto:${cfg.contact || "seller"}">${cfg.contact || "seller"}</a> with ref + tx screenshot.</p>
            </div>`;
        }
        if (btn) {
          btn.disabled = false;
          btn.textContent = "I sent payment — get license key";
        }
        return;
      }

      const key = grantKey(slug, ref);
      if (key) showKey(key);
      else if (reveal) {
        reveal.innerHTML = `<p class="muted">Payment received — contact ${cfg.contact || "seller"} with ref ${ref} for your key.</p>`;
      }
      if (btn) {
        btn.disabled = false;
        btn.textContent = "Payment complete — get license key";
      }
    }

    function render() {
      const m = allowed[active] || {};
      const isCard = active === "card";
      modal.classList.toggle("crypto-modal-wide", isCard);

      if (isCard) {
        const provider = cardProvider();
        modal.innerHTML = `
          <h3>${prod.title || slug} — $${usd}</h3>
          <p class="muted">Pay with card — you pay fiat, seller receives USDC on Solana</p>
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

        if (!mounted) widget.innerHTML = cardSetupHtml(slug);
      } else {
        const amt = cryptoAmount(usd, active);
        const direct = !!m.direct;
        const payUrl = solanaPayUrl(active, amt, ref);

        modal.innerHTML = `
          <h3>${prod.title || slug} — $${usd}</h3>
          <p class="muted">Send directly to this wallet only — no swaps, bridges, or DeFi.</p>
          <div class="crypto-tabs" id="crypto-tabs"></div>
          <p class="crypto-amount">${amt} ${m.label || active}${m.sublabel ? ` <span class="muted">on ${m.sublabel}</span>` : ""}</p>
          <p class="crypto-ref">Order ref: <strong>${ref}</strong></p>
          ${
            direct
              ? `<p class="crypto-settle">Send <strong>only</strong> ${m.label} on Solana to this address:</p>`
              : `<p class="crypto-settle">Send directly to Solana address:</p>`
          }
          <div class="crypto-wallet" id="wallet-addr">${payout}</div>
          <div class="crypto-row">
            <button type="button" id="copy-addr">Copy Solana address</button>
            <button type="button" id="copy-amt">Copy amount</button>
            ${payUrl ? `<a class="btn-crypto" id="open-wallet" href="${payUrl}">Open wallet</a>` : ""}
          </div>
          <p class="crypto-settle-foot">Payout: <code>${payout.slice(0, 8)}…${payout.slice(-6)}</code></p>
          <div class="crypto-bridge-notice" style="margin-top:0.75rem">
            <strong>Important:</strong> Use Phantom → Send → paste address + amount. Do not use Drift/Jupiter. Then click below.
          </div>
          <div class="crypto-row">
            <button type="button" class="btn-crypto" id="confirm-paid">I sent payment — get license key</button>
            <button type="button" class="secondary" id="crypto-close">Close</button>
          </div>
          <div id="key-reveal"></div>`;

        modal.querySelector("#copy-addr")?.addEventListener("click", () => copyText(payout));
        modal.querySelector("#copy-amt")?.addEventListener("click", () => copyText(amt));
      }

      const tabs = modal.querySelector("#crypto-tabs");
      Object.keys(allowed).forEach((key) => {
        const b = document.createElement("button");
        b.type = "button";
        const meta = allowed[key];
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
    if (label === "card") {
      btn.textContent = `Card — $${prod.price_usd}`;
      btn.addEventListener("click", () => openModal(slug, "card"));
    } else if (label === "both") {
      btn.className = "btn buy-crypto";
      btn.textContent = `Upgrade — $${prod.price_usd}`;
      btn.addEventListener("click", () => openModal(slug));
    } else {
      btn.textContent = `Crypto — $${prod.price_usd}`;
      btn.addEventListener("click", () => openModal(slug, preferred));
    }
    return btn;
  }

  fetchRates();

  window.SellerToolsPay = { buy: openModal };

  function mountPayButtons(el, slug) {
    const cardBtn = buyButton(slug, "card");
    const cryptoBtn = buyButton(slug, "crypto");
    if (cardBtn) el.prepend(cardBtn);
    if (cryptoBtn) el.prepend(cryptoBtn);
  }

  document.querySelectorAll("[data-crypto]").forEach((el) => {
    mountPayButtons(el, el.getAttribute("data-crypto"));
  });

  document.querySelectorAll("[data-crypto-bundle]").forEach((el) => {
    const slug = "seller-kit-bundle";
    const cardBtn = buyButton(slug, "card");
    const cryptoBtn = buyButton(slug, "crypto");
    if (cardBtn) {
      cardBtn.textContent = `Card — $${products[slug]?.price_usd || 29}`;
      el.appendChild(cardBtn);
    }
    if (cryptoBtn) {
      cryptoBtn.textContent = `Crypto — $${products[slug]?.price_usd || 29}`;
      el.appendChild(cryptoBtn);
    }
  });

  document.querySelectorAll("[data-crypto-buy]").forEach((el) => {
    const slug = el.getAttribute("data-crypto-buy");
    const cardBtn = buyButton(slug, "card");
    const cryptoBtn = buyButton(slug, "crypto");
    if (cardBtn) el.appendChild(cardBtn);
    if (cryptoBtn) el.appendChild(cryptoBtn);
  });
})();