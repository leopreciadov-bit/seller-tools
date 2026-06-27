(function () {
  const cfg = window.CRYPTO || {};
  const wallets = cfg.wallets || {};
  const products = cfg.products || {};
  const keyPool = cfg.keyPool || {};
  const preferred = cfg.preferred || "usdt_trc20";

  const LABELS = {
    usdt_trc20: "USDT (TRC20)",
    usdc_sol: "USDC (Solana)",
    btc: "BTC",
    eth: "ETH",
  };

  const COINGECKO = {
    usdt_trc20: "tether",
    usdc_sol: "usd-coin",
    btc: "bitcoin",
    eth: "ethereum",
  };

  let rates = { usdt_trc20: 1, usdc_sol: 1, btc: 0, eth: 0 };

  async function fetchRates() {
    const ids = [...new Set(Object.values(COINGECKO))].join(",");
    try {
      const r = await fetch(
        `https://api.coingecko.com/api/v3/simple/price?ids=${ids}&vs_currencies=usd`
      );
      const data = await r.json();
      for (const [k, id] of Object.entries(COINGECKO)) {
        if (data[id]?.usd) rates[k] = data[id].usd;
      }
    } catch (_) {
      /* fallback: stablecoins = 1 */
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

  function copyText(text) {
    navigator.clipboard.writeText(text).catch(() => {});
  }

  function cryptoAmount(usd, coin) {
    const rate = rates[coin] || 1;
    if (coin === "usdt_trc20" || coin === "usdc_sol") return usd.toFixed(2);
    return (usd / rate).toFixed(8).replace(/\.?0+$/, "");
  }

  function walletReady(addr) {
    return addr && !addr.startsWith("SET_YOUR");
  }

  function openModal(slug) {
    const prod = products[slug];
    if (!prod) return;

    const overlay = document.createElement("div");
    overlay.className = "crypto-overlay";
    const modal = document.createElement("div");
    modal.className = "crypto-modal";

    let activeCoin = walletReady(wallets[preferred])
      ? preferred
      : Object.keys(wallets).find((k) => walletReady(wallets[k])) || preferred;

    const ref = orderRef(slug);
    const usd = prod.price_usd;

    function render() {
      const addr = wallets[activeCoin] || "";
      const ready = walletReady(addr);
      const amt = cryptoAmount(usd, activeCoin);
      const label = LABELS[activeCoin] || activeCoin;

      modal.innerHTML = `
        <h3>${prod.title || slug} — $${usd}</h3>
        <p class="muted">Pay with crypto. Instant license key after confirmation.</p>
        <div class="crypto-tabs" id="crypto-tabs"></div>
        ${
          ready
            ? `<p class="crypto-amount">${amt} ${label}</p>
               <p class="crypto-ref">Order ref: <strong>${ref}</strong> (include in memo if possible)</p>
               <div class="crypto-wallet" id="wallet-addr">${addr}</div>
               <div class="crypto-row">
                 <button type="button" id="copy-addr">Copy address</button>
                 <button type="button" id="copy-amt">Copy amount</button>
               </div>`
            : `<p class="muted">Wallet not configured yet. Set addresses with:<br>
               <code>python3 scripts/crypto_setup.py set-wallet --usdt-trc20 YOUR_ADDRESS</code></p>`
        }
        <div class="crypto-row">
          <button type="button" class="btn-crypto" id="confirm-paid" ${ready ? "" : "disabled"}>
            I sent payment — get license key
          </button>
          <button type="button" class="secondary" id="crypto-close">Close</button>
        </div>
        <div id="key-reveal"></div>
      `;

      const tabs = modal.querySelector("#crypto-tabs");
      Object.keys(LABELS).forEach((coin) => {
        if (!wallets[coin]) return;
        const b = document.createElement("button");
        b.type = "button";
        b.textContent = LABELS[coin];
        if (coin === activeCoin) b.classList.add("active");
        b.addEventListener("click", () => {
          activeCoin = coin;
          render();
        });
        tabs.appendChild(b);
      });

      modal.querySelector("#copy-addr")?.addEventListener("click", () => copyText(addr));
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
            `<p class="muted">Contact ${cfg.contact || "seller"} with order ref ${ref} for your key.</p>`;
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
    if (!prod) return null;
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