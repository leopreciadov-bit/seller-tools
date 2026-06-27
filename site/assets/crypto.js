window.CRYPTO = {
  "payout_address": "BaZNTHB9DNBAq69WH2hv272LcYLJRiksBFfyKKmYdPxH",
  "payout_network": "solana",
  "preferred": "card",
  "contact": "support@example.com",
  "card": {
    "enabled": true,
    "helio_paylink_id": "",
    "transak_api_key": "",
    "moonpay_publishable_key": "",
    "provider": "auto"
  },
  "products": {
    "listinglab-pro": {
      "title": "ListingLab Pro",
      "price_usd": 19,
      "key_prefix": "LISTING"
    },
    "etsy-tag-finder-pro": {
      "title": "Etsy Tag Finder Pro",
      "price_usd": 14,
      "key_prefix": "TAGFINDER"
    },
    "seller-kit-bundle": {
      "title": "Seller Kit Bundle",
      "price_usd": 29,
      "key_prefix": "SELLERKIT"
    }
  },
  "methods": {
    "card": {
      "label": "Card",
      "sublabel": "Visa \u00b7 MC \u00b7 Apple Pay",
      "direct": true,
      "card": true,
      "stablecoin": true
    },
    "usdc_sol": {
      "label": "USDC",
      "sublabel": "Solana",
      "direct": true,
      "coingecko": "usd-coin",
      "stablecoin": true,
      "spl_mint": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
    },
    "usdt_sol": {
      "label": "USDT",
      "sublabel": "Solana",
      "direct": true,
      "coingecko": "tether",
      "stablecoin": true,
      "spl_mint": "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB"
    },
    "sol": {
      "label": "SOL",
      "sublabel": "Solana",
      "direct": true,
      "coingecko": "solana",
      "stablecoin": false
    },
    "btc": {
      "label": "BTC",
      "sublabel": "Bitcoin",
      "direct": false,
      "coingecko": "bitcoin",
      "stablecoin": false,
      "bridge_url": "https://fixedfloat.com/?from=BTC&to=USDCSOL&toAddress=BaZNTHB9DNBAq69WH2hv272LcYLJRiksBFfyKKmYdPxH"
    },
    "eth": {
      "label": "ETH",
      "sublabel": "Ethereum",
      "direct": false,
      "coingecko": "ethereum",
      "stablecoin": false,
      "bridge_url": "https://fixedfloat.com/?from=ETH&to=USDCSOL&toAddress=BaZNTHB9DNBAq69WH2hv272LcYLJRiksBFfyKKmYdPxH"
    },
    "usdt_trc20": {
      "label": "USDT",
      "sublabel": "TRC20",
      "direct": false,
      "coingecko": "tether",
      "stablecoin": true,
      "bridge_url": "https://fixedfloat.com/?from=USDTTRC&to=USDCSOL&toAddress=BaZNTHB9DNBAq69WH2hv272LcYLJRiksBFfyKKmYdPxH"
    },
    "usdc_eth": {
      "label": "USDC",
      "sublabel": "Ethereum",
      "direct": false,
      "coingecko": "usd-coin",
      "stablecoin": true,
      "bridge_url": "https://fixedfloat.com/?from=USDC&to=USDCSOL&toAddress=BaZNTHB9DNBAq69WH2hv272LcYLJRiksBFfyKKmYdPxH"
    },
    "ltc": {
      "label": "LTC",
      "sublabel": "Litecoin",
      "direct": false,
      "coingecko": "litecoin",
      "stablecoin": false,
      "bridge_url": "https://fixedfloat.com/?from=LTC&to=USDCSOL&toAddress=BaZNTHB9DNBAq69WH2hv272LcYLJRiksBFfyKKmYdPxH"
    }
  },
  "keyPool": {
    "listinglab-pro": [
      "LISTING-HH1Y-NWFT",
      "LISTING-DBQM-LNSE",
      "LISTING-3A2I-YJ2I",
      "LISTING-EDF8-UY54",
      "LISTING-43LM-MZV8",
      "LISTING-V355-OLV3",
      "LISTING-8834-2OG1",
      "LISTING-7XD3-6SG0",
      "LISTING-Z0OR-SK8W",
      "LISTING-11ZP-P5X0",
      "LISTING-B1YG-INQY",
      "LISTING-CREN-657M",
      "LISTING-Z7Q5-8Z8D",
      "LISTING-NTKW-5ZH7",
      "LISTING-7GWG-SI3X"
    ],
    "etsy-tag-finder-pro": [
      "TAGFINDER-VW9M-DJJO",
      "TAGFINDER-723Y-REEN",
      "TAGFINDER-XIAG-ATPN",
      "TAGFINDER-WZ6Y-QJ6W",
      "TAGFINDER-TRTH-YGW2",
      "TAGFINDER-W0NW-I908",
      "TAGFINDER-BHI0-Q3LS",
      "TAGFINDER-QA8F-OX0B",
      "TAGFINDER-FXM2-3FIP",
      "TAGFINDER-RQZ3-3Z7D",
      "TAGFINDER-T3M2-R554",
      "TAGFINDER-Y2WG-IZMZ",
      "TAGFINDER-FSCM-68S5",
      "TAGFINDER-ZMB4-PCTV",
      "TAGFINDER-067L-SSRL"
    ],
    "seller-kit-bundle": [
      "SELLERKIT-XP6K-TCYA",
      "SELLERKIT-9D7T-0VC8",
      "SELLERKIT-ADNX-083V",
      "SELLERKIT-OODW-AJRL",
      "SELLERKIT-P1NJ-AL5U",
      "SELLERKIT-A4TA-ZVKM",
      "SELLERKIT-AVYP-8APY",
      "SELLERKIT-BCB3-UH3R",
      "SELLERKIT-JB96-1TTC",
      "SELLERKIT-PLT7-WHZS"
    ]
  }
};
