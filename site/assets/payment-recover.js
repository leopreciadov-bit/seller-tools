(function () {
  const cfg = window.CRYPTO || {};
  const recoveries = cfg.recoveries || {};
  const products = cfg.products || {};
  const payout = cfg.payout_address || "";
  const USDC_MINT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v";
  const USDT_MINT = "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB";
  const RPC_URLS = ["https://solana-rpc.publicnode.com", "https://rpc.ankr.com/solana"];
  const BLOCKED_PROGRAMS = new Set([
    "PERPHjGBqRHArX4DySjwM6UJHiR3sWAatqfdBS2qQJu",
    "JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4",
    "DoVEsk76QybCEHQGzkvYPWLQu9gzNoZZZt3TPiL597e",
  ]);

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

  function productForAmount(amount) {
    for (const [slug, p] of Object.entries(products)) {
      const usd = p.price_usd;
      if (amount >= usd * 0.85 && amount <= usd * 1.15) return slug;
    }
    return null;
  }

  function isDirectPayment(tx) {
    if (!tx?.meta) return false;
    const keys = (tx.transaction?.message?.accountKeys || []).map((k) =>
      typeof k === "string" ? k : k.pubkey
    );
    if (!keys.length || keys[0] === payout) return false;
    if (keys.some((k) => BLOCKED_PROGRAMS.has(k))) return false;
    const blocked = ["InstantDecreasePosition", "InstantIncreasePosition", "SwapWithTokenLedger"];
    for (const log of tx.meta.logMessages || []) {
      if (blocked.some((m) => log.includes(m))) return false;
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
    return inbound;
  }

  async function verifyTx(sig) {
    const tx = await solanaRpc("getTransaction", [
      sig,
      { encoding: "jsonParsed", maxSupportedTransactionVersion: 0 },
    ]);
    if (!tx?.meta || !isDirectPayment(tx)) return null;
    const pre = {};
    for (const t of tx.meta.preTokenBalances || []) {
      if (t.owner === payout) pre[t.mint] = parseFloat(t.uiTokenAmount?.uiAmount || 0);
    }
    for (const mint of [USDC_MINT, USDT_MINT]) {
      for (const t of tx.meta.postTokenBalances || []) {
        if (t.owner !== payout || t.mint !== mint) continue;
        const delta = parseFloat(t.uiTokenAmount?.uiAmount || 0) - (pre[mint] || 0);
        if (delta > 0) return { amount: delta, product: productForAmount(delta) };
      }
    }
    return null;
  }

  function showKey(key, title, unlockUrl, slug) {
    const out = document.getElementById("recover-result");
    out.innerHTML = `
      <div class="crypto-key-reveal" style="margin-top:1rem">
        <p><strong>${title} — your license key:</strong></p>
        <code style="display:block;padding:0.75rem;background:#0d1117;border-radius:8px;font-size:1.1rem">${key}</code>
        <div style="margin-top:0.75rem;display:flex;gap:0.5rem;flex-wrap:wrap">
          <button type="button" class="btn-crypto" id="copy-recover-key">Copy key</button>
          <a class="btn secondary" href="${unlockUrl}" style="padding:0.55rem 0.9rem;border-radius:8px;text-decoration:none">Open tool & unlock</a>
        </div>
        <p class="muted" style="margin-top:0.75rem">Paste the key in the Pro box and click Unlock Pro.</p>
      </div>`;
    document.getElementById("copy-recover-key").onclick = () =>
      navigator.clipboard.writeText(key).catch(() => {});
    if (slug) localStorage.setItem(`crypto_license_${slug}`, key);
  }

  const toolUrls = {
    "listinglab-pro": "/listing-lab/",
    "etsy-tag-finder-pro": "/etsy-tag-finder/",
    "seller-kit-bundle": "/listing-lab/",
  };

  document.getElementById("recover-form")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const sig = document.getElementById("tx-sig").value.trim();
    const status = document.getElementById("recover-status");
    const out = document.getElementById("recover-result");
    out.innerHTML = "";
    if (!sig || sig.length < 80) {
      status.textContent = "Paste your full Solana transaction signature (from Phantom → Activity → transaction).";
      return;
    }

    status.textContent = "Checking direct payment to seller wallet…";
    const btn = document.querySelector("#recover-form button");
    if (btn) btn.disabled = true;

    if (recoveries[sig]?.key) {
      const r = recoveries[sig];
      const prod = products[r.product] || { title: r.title || r.product };
      showKey(r.key, prod.title || r.title, toolUrls[r.product] || "/listing-lab/", r.product);
      status.textContent = "Payment matched. Your key is below.";
      if (btn) btn.disabled = false;
      return;
    }

    const verified = await verifyTx(sig);
    if (!verified?.product) {
      status.textContent =
        "Not a direct payment to our wallet. Use Phantom → Send USDC/USDT on Solana. No Drift, Jupiter, or swaps.";
      if (btn) btn.disabled = false;
      return;
    }

    const slug = verified.product;
    const pool = cfg.keyPool?.[slug] || [];
    if (!pool.length) {
      status.textContent = `Payment confirmed ($${verified.amount.toFixed(2)}). Email ${cfg.contact || "support"} with tx sig for your key.`;
      if (btn) btn.disabled = false;
      return;
    }
    showKey(pool[0], products[slug]?.title || slug, toolUrls[slug] || "/", slug);
    status.textContent = "Payment confirmed. Your key is below.";
    if (btn) btn.disabled = false;
  });
})();