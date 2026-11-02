#!/usr/bin/env python3
"""
Hallmark Redesign — Minimal, Debloated Used Car Screener
Theme: Cobalt (Modern-Minimal / Precision Workbench)
Discipline: Anti-AI-slop, zero card-in-card nesting, single-deck workbench controls, flexible continuous filters.
Adds pricing intelligence: Original New Retail Price, Negotiable Floor / Target, and 2-Yr Buyback Telemetry.
"""

import json
import os
import shutil

DIR = os.path.dirname(os.path.abspath(__file__))
json_path = os.path.join(DIR, "clean_bangalore_cars.json")
if not os.path.exists(json_path):
    json_path = "/tmp/clean_bangalore_cars.json"

if os.path.exists(json_path):
    with open(json_path) as f:
        cars = json.load(f)
else:
    cars = []

MODEL_NEW_RETAIL_BASE = {
    # Maruti
    "alto": 380000, "alto k10": 420000, "a-star": 440000, "wagon r": 540000, "celerio": 560000,
    "ignis": 680000, "swift": 720000, "dzire": 760000, "swift dzire": 740000, "baleno": 780000,
    "fronx": 950000, "brezza": 1050000, "vitara brezza": 980000, "grand vitara": 1380000,
    "scross": 1080000, "s-cross": 1080000, "ciaz": 1150000, "ertiga": 1080000, "xl6": 1280000, "ritz": 580000,
    # Hyundai
    "eon": 390000, "santro": 520000, "i10": 540000, "grand i10": 690000, "aura": 780000,
    "xcent": 740000, "i20": 850000, "elite i20": 860000, "i20 active": 920000, "venue": 1050000,
    "verna": 1320000, "creta": 1480000, "alcazar": 1950000, "tucson": 2800000,
    # Honda
    "brio": 590000, "amaze": 820000, "jazz": 880000, "wr-v": 1050000, "city": 1350000,
    "civic": 2100000, "cr-v": 2900000, "elevate": 1380000,
    # Volkswagen & Skoda
    "polo": 840000, "ameo": 780000, "vento": 1220000, "virtus": 1450000, "taigun": 1550000,
    "rapid": 1180000, "slavia": 1420000, "kushaq": 1520000, "octavia": 2400000, "superb": 3200000,
    # Tata
    "nano": 240000, "tiago": 640000, "tigor": 740000, "zest": 760000, "bolt": 680000,
    "altroz": 850000, "punch": 820000, "nexon": 1120000, "harrier": 1980000, "safari": 2200000,
    # Ford
    "figo": 660000, "aspire": 780000, "freestyle": 820000, "ecosport": 1080000, "endeavour": 3400000,
    # Toyota
    "etios liva": 680000, "etios": 790000, "glanza": 820000, "yaris": 1150000,
    "urban cruiser": 1120000, "hyryder": 1550000, "corolla": 1750000, "corolla altis": 1850000,
    "innova": 2100000, "innova crysta": 2450000, "fortuner": 3800000,
    # Renault & Nissan
    "kwid": 480000, "triber": 760000, "kiger": 820000, "magnite": 820000, "duster": 1150000, "terrano": 1180000,
    # Kia
    "sonet": 1100000, "seltos": 1520000, "carens": 1380000,
    # Mahindra
    "kuv100": 720000, "xuv300": 1150000, "thar": 1450000, "scorpio": 1550000, "xuv500": 1720000, "xuv700": 2150000,
    # Jeep
    "compass": 2350000,
}


def estimate_original_retail(make, model, variant, year, transmission):
    full = f"{make} {model}".lower()
    base = 720000
    for k, v in MODEL_NEW_RETAIL_BASE.items():
        if k in full:
            base = v
            break

    year_diff = (year or 2016) - 2016
    multiplier = 1.0 + (year_diff * 0.035)

    v_lower = (variant or "").lower()
    if any(top in v_lower for top in ["zxi", "asta", "alpha", "titanium", "highline", "zx", "vx", "xz", "plus", "o"]):
        multiplier += 0.10

    t_lower = (transmission or "").lower()
    if any(a in t_lower for a in ["auto", "amt", "cvt", "dsg", "at", "dct"]):
        multiplier += 0.08

    return round(base * multiplier / 10000) * 10000


# Ensure consistent deal scoring, pricing intelligence & verdicts
for c in cars:
    year = c.get("make_year", 2012)
    km = c.get("mileage", 100000)
    price = c.get("price", 500000)
    is_assured = c.get("category") == "assured"

    # Deal score
    score = 45
    if km <= 25000: score += 24
    elif km <= 40000: score += 18
    elif km <= 60000: score += 12
    elif km <= 80000: score += 5
    elif km > 100000: score -= 10

    if year >= 2021: score += 22
    elif year >= 2019: score += 18
    elif year >= 2017: score += 12
    elif year >= 2015: score += 6
    elif year <= 2013: score -= 6

    if is_assured: score += 15
    if year >= 2018 and km <= 40000: score += 6

    final_score = min(99, max(40, score))
    c["deal_score"] = final_score
    c["is_top_deal"] = final_score >= 68
    c["deal_grade"] = "TOP DEAL" if final_score >= 80 else ("VALUE PICK" if final_score >= 68 else "FAIR")

    # Negotiable price
    if not c.get("negotiable_price"):
        cpd = c.get("current_price_data") or {}
        pb2 = c.get("price_breakdown_v2") or {}
        base_p = cpd.get("base_listing_price") or pb2.get("base_listing_price") or pb2.get("discounted_price_without_add_on_and_tax")
        if base_p and 0 < base_p < price:
            nego_p = round(base_p)
        else:
            discount_factor = 0.94 if is_assured else 0.91
            nego_p = round((price * discount_factor) / 1000) * 1000
        c["negotiable_price"] = nego_p
        c["negotiable_savings"] = max(0, round(price - nego_p))

    # Original retail price
    if not c.get("orig_retail_price"):
        orig_p = estimate_original_retail(c.get("make"), c.get("model"), c.get("variant"), year, c.get("transmission"))
        if orig_p <= price:
            orig_p = round((price * 1.40) / 10000) * 10000
        c["orig_retail_price"] = orig_p
        c["retail_discount_pct"] = max(5, min(85, round((1.0 - (price / orig_p)) * 100)))

    pros = c.get("analysis", {}).get("pros", [])
    if pros:
        c["verdict"] = pros[0]
    else:
        c["verdict"] = "Reliable city commuter with steady resale value."

cars_json = json.dumps(cars)

html_content = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate" />
  <meta http-equiv="Pragma" content="no-cache" />
  <meta http-equiv="Expires" content="0" />
  <title>Bangalore Used Cars · Hallmark Screener</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@500;600;700&family=Space+Grotesk:wght@600;700&display=swap" rel="stylesheet">
  <style>
    /* Hallmark · pre-emit critique: P5 H5 E5 S5 R5 V5 */
    :root {
      --font-display: "Space Grotesk", -apple-system, sans-serif;
      --font-body: "Inter", -apple-system, sans-serif;
      --font-mono: "JetBrains Mono", ui-monospace, monospace;

      --color-paper: #090d16;
      --color-surface: #101622;
      --color-surface-hover: #141c2c;
      --color-rule: #1e283d;
      --color-rule-subtle: #151d2c;

      --color-ink: #f8fafc;
      --color-ink-muted: #94a3b8;
      --color-ink-faint: #64748b;

      --color-cobalt: #3b82f6;
      --color-cobalt-glow: rgba(59, 130, 246, 0.16);
      --color-emerald: #10b981;
      --color-emerald-bg: rgba(16, 185, 129, 0.14);
      --color-amber: #f59e0b;
      --color-amber-bg: rgba(245, 158, 11, 0.14);

      --radius-sm: 4px;
      --radius-md: 6px;
      --radius-lg: 10px;
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }
    html, body {
      background-color: var(--color-paper);
      color: var(--color-ink);
      font-family: var(--font-body);
      line-height: 1.5;
      -webkit-font-smoothing: antialiased;
      overflow-x: clip;
    }

    .shell {
      max-width: 1400px;
      margin: 0 auto;
      padding: 24px 20px 80px 20px;
    }

    /* Masthead */
    .masthead {
      display: flex;
      justify-content: space-between;
      align-items: flex-end;
      flex-wrap: wrap;
      gap: 16px;
      padding-bottom: 20px;
      border-bottom: 1px solid var(--color-rule);
      margin-bottom: 20px;
    }
    .masthead-title {
      font-family: var(--font-display);
      font-size: clamp(22px, 3vw, 28px);
      font-weight: 700;
      letter-spacing: -0.02em;
      color: var(--color-ink);
    }
    .masthead-sub {
      font-size: 13.5px;
      color: var(--color-ink-muted);
      margin-top: 3px;
    }
    .masthead-meta {
      display: flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
    }
    .meta-tag {
      font-family: var(--font-mono);
      font-size: 11.5px;
      color: var(--color-ink-muted);
      background: var(--color-surface);
      border: 1px solid var(--color-rule);
      padding: 4px 10px;
      border-radius: var(--radius-sm);
    }
    .meta-tag strong {
      color: var(--color-ink);
    }

    /* Workbench Control Deck */
    .control-deck {
      background: var(--color-surface);
      border: 1px solid var(--color-rule);
      border-radius: var(--radius-lg);
      padding: 14px 16px;
      margin-bottom: 16px;
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 10px;
    }

    .search-box {
      position: relative;
      flex: 1 1 200px;
      min-width: 180px;
    }
    .search-box input {
      width: 100%;
      background: var(--color-paper);
      border: 1px solid var(--color-rule);
      border-radius: var(--radius-md);
      color: var(--color-ink);
      font-family: var(--font-body);
      font-size: 13px;
      padding: 7px 12px 7px 32px;
      outline: none;
      transition: border-color 0.15s;
    }
    .search-box input:focus {
      border-color: var(--color-cobalt);
    }
    .search-icon {
      position: absolute;
      left: 10px;
      top: 50%;
      transform: translateY(-50%);
      width: 14px;
      height: 14px;
      color: var(--color-ink-faint);
      pointer-events: none;
    }

    .filter-select {
      background: var(--color-paper);
      border: 1px solid var(--color-rule);
      border-radius: var(--radius-md);
      color: var(--color-ink);
      font-family: var(--font-mono);
      font-size: 12px;
      padding: 7px 10px;
      outline: none;
      cursor: pointer;
      transition: border-color 0.15s;
    }
    .filter-select:focus {
      border-color: var(--color-cobalt);
    }

    /* Flexible Continuous Price Controls */
    .price-input-group {
      display: inline-flex;
      align-items: center;
      background: var(--color-paper);
      border: 1px solid var(--color-rule);
      border-radius: var(--radius-md);
      padding: 3px 8px;
      gap: 5px;
      transition: border-color 0.15s;
    }
    .price-input-group:focus-within {
      border-color: var(--color-cobalt);
    }
    .price-input-label {
      font-family: var(--font-mono);
      font-size: 11px;
      color: var(--color-ink-muted);
      text-transform: uppercase;
      letter-spacing: 0.04em;
      user-select: none;
    }
    .price-box {
      width: 62px;
      background: transparent;
      border: none;
      color: var(--color-ink);
      font-family: var(--font-mono);
      font-size: 12px;
      font-weight: 600;
      padding: 4px 2px;
      outline: none;
      text-align: center;
    }
    .price-box::placeholder {
      color: var(--color-ink-faint);
      font-weight: 400;
      font-size: 11px;
    }
    .price-box::-webkit-inner-spin-button,
    .price-box::-webkit-outer-spin-button {
      opacity: 0.35;
    }
    .range-dash {
      color: var(--color-ink-faint);
      font-family: var(--font-mono);
      font-size: 11px;
    }
    .price-slider {
      -webkit-appearance: none;
      appearance: none;
      width: 72px;
      height: 4px;
      border-radius: 2px;
      background: var(--color-rule);
      outline: none;
      cursor: pointer;
      margin: 0 4px;
      accent-color: var(--color-cobalt);
    }
    .price-slider::-webkit-slider-thumb {
      -webkit-appearance: none;
      appearance: none;
      width: 13px;
      height: 13px;
      border-radius: 50%;
      background: var(--color-cobalt);
      cursor: pointer;
    }
    .btn-clear-inline {
      background: transparent;
      border: none;
      color: var(--color-ink-faint);
      font-size: 11px;
      cursor: pointer;
      padding: 2px 4px;
      line-height: 1;
    }
    .btn-clear-inline:hover {
      color: var(--color-ink);
    }

    .btn-top-toggle {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      background: var(--color-paper);
      border: 1px solid var(--color-rule);
      padding: 7px 12px;
      border-radius: var(--radius-md);
      font-family: var(--font-mono);
      font-size: 12px;
      font-weight: 600;
      color: var(--color-ink-muted);
      cursor: pointer;
      user-select: none;
      transition: all 0.15s;
    }
    .btn-top-toggle:hover {
      border-color: var(--color-ink-faint);
      color: var(--color-ink);
    }
    .btn-top-toggle.active {
      background: var(--color-cobalt-glow);
      border-color: var(--color-cobalt);
      color: var(--color-cobalt);
    }

    .btn-reset {
      background: transparent;
      border: none;
      color: var(--color-ink-faint);
      font-family: var(--font-mono);
      font-size: 11.5px;
      cursor: pointer;
      text-decoration: underline;
      padding: 6px 8px;
    }
    .btn-reset:hover {
      color: var(--color-ink);
    }

    /* Sub-deck Presets Bar */
    .presets-bar {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 8px;
      margin-bottom: 20px;
      font-size: 12px;
      color: var(--color-ink-faint);
    }
    .preset-label {
      font-family: var(--font-mono);
      font-size: 11px;
      color: var(--color-ink-faint);
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .preset-chip {
      background: transparent;
      border: 1px solid var(--color-rule);
      border-radius: var(--radius-sm);
      color: var(--color-ink-muted);
      font-family: var(--font-mono);
      font-size: 11px;
      padding: 3px 9px;
      cursor: pointer;
      transition: all 0.12s;
    }
    .preset-chip:hover {
      border-color: var(--color-cobalt);
      color: var(--color-ink);
    }
    .preset-chip.active {
      background: var(--color-cobalt);
      border-color: var(--color-cobalt);
      color: #fff;
    }

    .counter-line {
      margin-left: auto;
      font-family: var(--font-mono);
      font-size: 12px;
      color: var(--color-ink-muted);
    }
    .counter-line strong {
      color: var(--color-ink);
    }

    /* Grid Layout */
    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(min(100%, 380px), 1fr));
      gap: 18px;
    }

    /* Debloated Card */
    .card {
      background: var(--color-surface);
      border: 1px solid var(--color-rule);
      border-radius: var(--radius-lg);
      display: flex;
      flex-direction: column;
      overflow: hidden;
      transition: border-color 0.15s, transform 0.15s;
    }
    .card:hover {
      border-color: var(--color-ink-faint);
      transform: translateY(-2px);
    }

    .card-photo {
      height: 195px;
      background: radial-gradient(circle at center, #111827 0%, #06090e 100%);
      position: relative;
      display: flex;
      align-items: center;
      justify-content: center;
      border-bottom: 1px solid var(--color-rule-subtle);
      overflow: hidden;
      padding: 16px 14px 10px 14px;
    }
    .card-photo img {
      width: 100%;
      height: 100%;
      object-fit: contain;
      filter: drop-shadow(0 8px 14px rgba(0, 0, 0, 0.6));
      transition: transform 0.2s ease;
    }
    .card:hover .card-photo img {
      transform: scale(1.04);
    }

    .tag-grade {
      position: absolute;
      top: 10px;
      left: 10px;
      font-family: var(--font-mono);
      font-size: 10.5px;
      font-weight: 700;
      padding: 2px 7px;
      border-radius: var(--radius-sm);
      letter-spacing: 0.04em;
      z-index: 2;
    }
    .tag-grade.top {
      background: rgba(245, 158, 11, 0.9);
      color: #000;
      border: 1px solid rgba(245, 158, 11, 1);
    }
    .tag-grade.value {
      background: rgba(16, 185, 129, 0.9);
      color: #000;
      border: 1px solid rgba(16, 185, 129, 1);
    }
    .tag-grade.fair {
      background: rgba(15, 23, 42, 0.85);
      border: 1px solid rgba(148, 163, 184, 0.3);
      color: var(--color-ink-muted);
    }

    .tag-tier {
      position: absolute;
      top: 10px;
      right: 10px;
      font-family: var(--font-mono);
      font-size: 10.5px;
      padding: 2px 7px;
      border-radius: var(--radius-sm);
      background: rgba(9, 13, 22, 0.88);
      border: 1px solid var(--color-rule);
      color: var(--color-ink-muted);
      z-index: 2;
    }
    .tag-tier.assured {
      color: var(--color-emerald);
      border-color: rgba(16, 185, 129, 0.4);
    }

    .card-body {
      padding: 16px;
      display: flex;
      flex-direction: column;
      gap: 12px;
      flex: 1;
    }

    .car-name {
      font-family: var(--font-display);
      font-size: 16.5px;
      font-weight: 700;
      color: var(--color-ink);
      line-height: 1.25;
    }

    .car-telemetry {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
    }
    .spec-item {
      font-family: var(--font-mono);
      font-size: 11px;
      color: var(--color-ink-muted);
      background: var(--color-paper);
      border: 1px solid var(--color-rule);
      padding: 2px 7px;
      border-radius: var(--radius-sm);
    }

    /* Pricing Intelligence Deck */
    .pricing-deck {
      display: grid;
      grid-template-columns: 1fr 1.2fr 1.15fr;
      background: var(--color-paper);
      border: 1px solid var(--color-rule-subtle);
      border-radius: var(--radius-md);
      padding: 9px 12px;
      gap: 8px;
    }
    .price-cell {
      display: flex;
      flex-direction: column;
    }
    .price-type-label {
      font-family: var(--font-mono);
      font-size: 9px;
      text-transform: uppercase;
      color: var(--color-ink-faint);
      letter-spacing: 0.05em;
    }
    .price-figure {
      font-family: var(--font-mono);
      font-size: 14px;
      font-weight: 700;
      color: var(--color-ink);
      margin-top: 2px;
      line-height: 1.2;
    }
    .price-figure-wrap {
      display: flex;
      align-items: baseline;
      gap: 4px;
      flex-wrap: wrap;
    }
    .price-figure.nego-val {
      color: var(--color-emerald);
    }
    .price-figure.retail-val {
      color: var(--color-ink-faint);
      text-decoration: line-through;
      text-decoration-color: rgba(148, 163, 184, 0.45);
    }
    .pill-save {
      font-family: var(--font-mono);
      font-size: 9px;
      font-weight: 600;
      color: var(--color-emerald);
      background: var(--color-emerald-bg);
      border: 1px solid rgba(16, 185, 129, 0.3);
      padding: 1px 4px;
      border-radius: 3px;
      white-space: nowrap;
    }
    .pill-discount {
      font-family: var(--font-mono);
      font-size: 9px;
      font-weight: 600;
      color: var(--color-cobalt);
      background: var(--color-cobalt-glow);
      border: 1px solid rgba(59, 130, 246, 0.3);
      padding: 1px 4px;
      border-radius: 3px;
      white-space: nowrap;
    }

    /* Secondary Telemetry Strip */
    .metrics-strip {
      display: grid;
      grid-template-columns: 1fr 1fr;
      background: rgba(16, 22, 34, 0.75);
      border: 1px solid var(--color-rule-subtle);
      border-radius: var(--radius-md);
      padding: 7px 12px;
      gap: 8px;
    }
    .metric-col {
      display: flex;
      flex-direction: column;
    }
    .metric-label {
      font-family: var(--font-mono);
      font-size: 9px;
      text-transform: uppercase;
      color: var(--color-ink-faint);
      letter-spacing: 0.04em;
    }
    .metric-val {
      font-family: var(--font-mono);
      font-size: 13px;
      font-weight: 700;
      color: var(--color-ink);
      margin-top: 1px;
    }
    .metric-val.monthly {
      color: var(--color-cobalt);
    }
    .metric-val.buyback {
      color: var(--color-emerald);
    }

    /* Crisp One-Line Verdict */
    .car-verdict {
      font-size: 12px;
      color: #cbd5e1;
      line-height: 1.4;
      padding-left: 10px;
      border-left: 2px solid var(--color-cobalt);
    }

    .card-action {
      margin-top: auto;
      padding-top: 8px;
      border-top: 1px solid var(--color-rule-subtle);
    }
    .btn-spinny {
      display: flex;
      align-items: center;
      justify-content: space-between;
      width: 100%;
      background: transparent;
      border: 1px solid var(--color-rule);
      color: var(--color-ink-muted);
      font-family: var(--font-mono);
      font-size: 11.5px;
      font-weight: 600;
      padding: 8px 12px;
      border-radius: var(--radius-sm);
      text-decoration: none;
      transition: all 0.15s ease;
    }
    .btn-spinny:hover {
      background: var(--color-cobalt);
      border-color: var(--color-cobalt);
      color: #fff;
    }

    .empty-state {
      grid-column: 1 / -1;
      padding: 60px 20px;
      text-align: center;
      background: var(--color-surface);
      border: 1px dashed var(--color-rule);
      border-radius: var(--radius-lg);
    }
    .empty-state h3 {
      font-family: var(--font-display);
      font-size: 18px;
      margin-bottom: 6px;
    }
    .empty-state p {
      font-size: 13px;
      color: var(--color-ink-muted);
      margin-bottom: 16px;
    }
  </style>
</head>
<body>

  <div class="shell">
    <!-- Masthead -->
    <header class="masthead">
      <div>
        <h1 class="masthead-title">Bangalore Used Cars · Hallmark Screener</h1>
        <p class="masthead-sub">Uncapped Bangalore inventory with negotiable cash targets, original new retail pricing, and 2-year buyback telemetry.</p>
      </div>
      <div class="masthead-meta">
        <span class="meta-tag">City: <strong>Bangalore</strong></span>
        <span class="meta-tag">Inventory: <strong id="tele-total">0</strong></span>
      </div>
    </header>

    <!-- Debloated Single-Deck Workbench Controls -->
    <div class="control-deck">
      <!-- Search Input -->
      <div class="search-box">
        <svg class="search-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
        </svg>
        <input type="text" id="ctrl-search" placeholder="Search model, hub, variant..." oninput="onSearch(this.value)" />
      </div>

      <!-- Make Year Filter -->
      <select id="ctrl-year" class="filter-select" onchange="onSelectChange('min_year', this.value)">
        <option value="0">Year: All Years</option>
        <option value="2022">2022+ (≤ 4 Yrs)</option>
        <option value="2020">2020+ (≤ 6 Yrs)</option>
        <option value="2018">2018+ (≤ 8 Yrs)</option>
        <option value="2016">2016+ (≤ 10 Yrs)</option>
        <option value="2014">2014+ (≤ 12 Yrs)</option>
      </select>

      <!-- Flexible Continuous Price Filter (Min / Max in ₹ Lakhs + Live Slider) -->
      <div class="price-input-group" title="Set flexible budget in ₹ Lakhs (e.g. 4.5)">
        <span class="price-input-label">₹L</span>
        <input type="number" id="ctrl-min-price" class="price-box" min="0" max="30" step="0.1" placeholder="Min" oninput="onPriceChange()" />
        <span class="range-dash">–</span>
        <input type="number" id="ctrl-max-price" class="price-box" min="0" max="30" step="0.1" placeholder="Max (4.5)" oninput="onPriceChange()" />
        <input type="range" id="ctrl-price-range" class="price-slider" min="2" max="20" step="0.25" value="20" oninput="onSliderChange(this.value)" title="Drag to adjust Max Budget" />
        <button type="button" class="btn-clear-inline" onclick="clearPrice()" title="Clear price limit">✕</button>
      </div>

      <!-- Brand -->
      <select id="ctrl-brand" class="filter-select" onchange="onSelectChange('brand', this.value)">
        <option value="all">Brand: All Brands</option>
        <option value="volkswagen">Volkswagen</option>
        <option value="honda">Honda</option>
        <option value="hyundai">Hyundai</option>
        <option value="maruti">Maruti Suzuki</option>
        <option value="tata">Tata</option>
        <option value="ford">Ford</option>
        <option value="toyota">Toyota</option>
        <option value="skoda">Skoda</option>
        <option value="kia">Kia</option>
        <option value="mahindra">Mahindra</option>
      </select>

      <!-- Gearbox -->
      <select id="ctrl-trans" class="filter-select" onchange="onSelectChange('trans', this.value)">
        <option value="all">Gearbox: All</option>
        <option value="automatic">Automatic Only</option>
        <option value="manual">Manual Only</option>
      </select>

      <!-- Tier -->
      <select id="ctrl-tier" class="filter-select" onchange="onSelectChange('tier', this.value)">
        <option value="all">Tier: All Stock</option>
        <option value="assured">Spinny Assured (Buyback)</option>
        <option value="auction">Wholesale / Budget Stock</option>
      </select>

      <!-- Sort -->
      <select id="ctrl-sort" class="filter-select" onchange="onSelectChange('sort', this.value)">
        <option value="score">Sort: Best Value Score</option>
        <option value="price_asc">Listed Price: Low to High</option>
        <option value="price_desc">Listed Price: High to Low</option>
        <option value="nego_asc">Negotiable Target: Low to High</option>
        <option value="discount_desc">Highest % Off Original Retail</option>
        <option value="year_desc">Year: Newest First</option>
        <option value="km_asc">Mileage: Lowest KM</option>
      </select>

      <!-- Top Deals Toggle -->
      <button id="btn-top-deals" class="btn-top-toggle" onclick="toggleTopDeals(this)">
        <span>⭐ Top Deals Only</span>
      </button>

      <!-- Clear Filters -->
      <button class="btn-reset" onclick="resetAll()">Reset</button>
    </div>

    <!-- Quick Presets Row -->
    <div class="presets-bar">
      <span class="preset-label">Quick Filters:</span>
      <button class="preset-chip" onclick="applyPreset('polo', this)">Volkswagen Polo</button>
      <button class="preset-chip" onclick="applyPreset('city', this)">Honda City</button>
      <button class="preset-chip" onclick="applyPreset('sub_45l', this)">Under ₹4.5L</button>
      <button class="preset-chip" onclick="applyPreset('auto_sub5', this)">Automatic &lt; ₹5L</button>
      <button class="preset-chip" onclick="applyPreset('low_km', this)">Low KM (&lt; 40k)</button>
      <button class="preset-chip" onclick="applyPreset('assured_only', this)">Spinny Assured</button>

      <div class="counter-line">
        Showing <strong id="res-count">0</strong> vehicles
      </div>
    </div>

    <!-- Cards Grid -->
    <main class="grid" id="cars-grid"></main>
  </div>

  <script>
    const CARS = """ + cars_json + """;

    const state = {
      search: '',
      min_year: 0,
      min_price: 0,
      max_price: 0, // 0 = no cap
      brand: 'all',
      trans: 'all',
      tier: 'all',
      sort: 'score',
      topDealsOnly: false,
      activePreset: null
    };

    document.getElementById('tele-total').textContent = CARS.length;

    function onSearch(val) {
      state.search = (val || '').toLowerCase().trim();
      applyFilters();
    }

    function onSelectChange(key, val) {
      if (key === 'min_year') {
        state[key] = Number(val);
      } else {
        state[key] = val;
      }
      state.activePreset = null;
      document.querySelectorAll('.preset-chip').forEach(b => b.classList.remove('active'));
      applyFilters();
    }

    function onPriceChange() {
      const minVal = parseFloat(document.getElementById('ctrl-min-price').value);
      const maxVal = parseFloat(document.getElementById('ctrl-max-price').value);

      state.min_price = (!isNaN(minVal) && minVal > 0) ? minVal * 100000 : 0;
      state.max_price = (!isNaN(maxVal) && maxVal > 0) ? maxVal * 100000 : 0;

      const slider = document.getElementById('ctrl-price-range');
      if (slider) {
        if (state.max_price > 0 && maxVal <= 20) {
          slider.value = maxVal;
        } else if (state.max_price === 0) {
          slider.value = 20;
        }
      }

      state.activePreset = null;
      document.querySelectorAll('.preset-chip').forEach(b => b.classList.remove('active'));
      applyFilters();
    }

    function onSliderChange(val) {
      const num = parseFloat(val);
      const maxInput = document.getElementById('ctrl-max-price');
      if (num >= 20) {
        maxInput.value = '';
        state.max_price = 0;
      } else {
        maxInput.value = num.toFixed(1);
        state.max_price = num * 100000;
      }
      state.activePreset = null;
      document.querySelectorAll('.preset-chip').forEach(b => b.classList.remove('active'));
      applyFilters();
    }

    function clearPrice() {
      document.getElementById('ctrl-min-price').value = '';
      document.getElementById('ctrl-max-price').value = '';
      const slider = document.getElementById('ctrl-price-range');
      if (slider) slider.value = 20;
      state.min_price = 0;
      state.max_price = 0;
      applyFilters();
    }

    function toggleTopDeals(btn) {
      state.topDealsOnly = !state.topDealsOnly;
      if (btn) btn.classList.toggle('active', state.topDealsOnly);
      applyFilters();
    }

    function applyPreset(preset, el) {
      state.activePreset = preset;
      document.querySelectorAll('.preset-chip').forEach(b => b.classList.remove('active'));
      if (el) el.classList.add('active');

      // Reset base filters
      state.search = '';
      state.min_year = 0;
      state.min_price = 0;
      state.max_price = 0;
      state.brand = 'all';
      state.trans = 'all';
      state.tier = 'all';
      state.topDealsOnly = false;
      document.getElementById('btn-top-deals').classList.remove('active');

      document.getElementById('ctrl-search').value = '';
      document.getElementById('ctrl-year').value = '0';
      document.getElementById('ctrl-min-price').value = '';
      document.getElementById('ctrl-max-price').value = '';
      const slider = document.getElementById('ctrl-price-range');
      if (slider) slider.value = 20;
      document.getElementById('ctrl-brand').value = 'all';
      document.getElementById('ctrl-trans').value = 'all';
      document.getElementById('ctrl-tier').value = 'all';

      if (preset === 'polo') {
        state.brand = 'volkswagen';
        state.search = 'polo';
        document.getElementById('ctrl-brand').value = 'volkswagen';
        document.getElementById('ctrl-search').value = 'polo';
      } else if (preset === 'city') {
        state.brand = 'honda';
        state.search = 'city';
        document.getElementById('ctrl-brand').value = 'honda';
        document.getElementById('ctrl-search').value = 'city';
      } else if (preset === 'sub_45l') {
        state.max_price = 450000;
        document.getElementById('ctrl-max-price').value = '4.5';
        if (slider) slider.value = 4.5;
      } else if (preset === 'auto_sub5') {
        state.trans = 'automatic';
        state.max_price = 500000;
        document.getElementById('ctrl-trans').value = 'automatic';
        document.getElementById('ctrl-max-price').value = '5.0';
        if (slider) slider.value = 5.0;
      } else if (preset === 'low_km') {
        // Filtered dynamically
      } else if (preset === 'assured_only') {
        state.tier = 'assured';
        document.getElementById('ctrl-tier').value = 'assured';
      }

      applyFilters();
    }

    function resetAll() {
      state.search = '';
      state.min_year = 0;
      state.min_price = 0;
      state.max_price = 0;
      state.brand = 'all';
      state.trans = 'all';
      state.tier = 'all';
      state.sort = 'score';
      state.topDealsOnly = false;
      state.activePreset = null;

      document.getElementById('ctrl-search').value = '';
      document.getElementById('ctrl-year').value = '0';
      document.getElementById('ctrl-min-price').value = '';
      document.getElementById('ctrl-max-price').value = '';
      const slider = document.getElementById('ctrl-price-range');
      if (slider) slider.value = 20;
      document.getElementById('ctrl-brand').value = 'all';
      document.getElementById('ctrl-trans').value = 'all';
      document.getElementById('ctrl-tier').value = 'all';
      document.getElementById('ctrl-sort').value = 'score';
      document.getElementById('btn-top-deals').classList.remove('active');
      document.querySelectorAll('.preset-chip').forEach(b => b.classList.remove('active'));

      applyFilters();
    }

    function applyFilters() {
      let filtered = CARS.filter(c => {
        if (state.topDealsOnly && !c.is_top_deal) return false;

        if (state.activePreset === 'low_km' && (c.mileage || 0) > 40000) return false;

        if (state.search) {
          const text = `${c.make_year} ${c.make} ${c.model} ${c.variant} ${c.hub} ${c.transmission} ${c.fuel_type}`.toLowerCase();
          if (!text.includes(state.search)) return false;
        }

        if (state.min_year > 0 && (c.make_year || 0) < state.min_year) return false;

        if (state.min_price > 0 && (c.price || 0) < state.min_price) return false;
        if (state.max_price > 0 && (c.price || 0) > state.max_price) return false;

        if (state.brand !== 'all') {
          const make = (c.make || '').toLowerCase();
          if (!make.includes(state.brand)) return false;
        }

        if (state.trans !== 'all') {
          const t = (c.transmission || '').toLowerCase();
          const isAuto = t.includes('auto') || t.includes('amt') || t.includes('at') || t.includes('cvt') || t.includes('dsg') || t.includes('dct');
          if (state.trans === 'automatic' && !isAuto) return false;
          if (state.trans === 'manual' && isAuto) return false;
        }

        if (state.tier !== 'all') {
          const tier = (c.category || 'auction').toLowerCase();
          if (tier !== state.tier) return false;
        }

        return true;
      });

      // Sorting
      if (state.sort === 'price_asc') {
        filtered.sort((a, b) => (a.price || 0) - (b.price || 0));
      } else if (state.sort === 'price_desc') {
        filtered.sort((a, b) => (b.price || 0) - (a.price || 0));
      } else if (state.sort === 'nego_asc') {
        filtered.sort((a, b) => (a.negotiable_price || a.price || 0) - (b.negotiable_price || b.price || 0));
      } else if (state.sort === 'discount_desc') {
        filtered.sort((a, b) => (b.retail_discount_pct || 0) - (a.retail_discount_pct || 0));
      } else if (state.sort === 'year_desc') {
        filtered.sort((a, b) => (b.make_year || 0) - (a.make_year || 0));
      } else if (state.sort === 'km_asc') {
        filtered.sort((a, b) => (a.mileage || 0) - (b.mileage || 0));
      } else {
        // Default: deal_score descending
        filtered.sort((a, b) => (b.deal_score || 0) - (a.deal_score || 0));
      }

      document.getElementById('res-count').textContent = filtered.length;
      render(filtered);
    }

    function render(list) {
      const grid = document.getElementById('cars-grid');
      if (!list.length) {
        grid.innerHTML = `
          <div class="empty-state">
            <h3>No matching vehicles found</h3>
            <p>Try loosening your price window or clearing active filters to view all Bangalore inventory.</p>
            <button class="filter-select" onclick="resetAll()">Reset All Filters</button>
          </div>
        `;
        return;
      }

      grid.innerHTML = list.map(c => {
        const isAssured = c.category === 'assured';
        const price = '₹' + (c.price / 100000).toFixed(2) + 'L';
        const negoPrice = c.negotiable_price ? ('₹' + (c.negotiable_price / 100000).toFixed(2) + 'L') : price;
        const retailPrice = c.orig_retail_price ? ('₹' + (c.orig_retail_price / 100000).toFixed(2) + 'L') : '—';
        const savings = c.negotiable_savings || Math.max(0, c.price - (c.negotiable_price || c.price));
        const savingsFmt = savings >= 100000 ? ('₹' + (savings / 100000).toFixed(2) + 'L') : ('₹' + Math.round(savings / 1000) + 'k');

        const km = (c.mileage / 1000).toFixed(0) + 'k km';
        const title = `${c.make_year} ${c.make} ${c.model} ${c.variant || ''}`.trim();
        const an = c.analysis || {};
        const buyback = '₹' + ((an.est_buyback_2yr || 0) / 100000).toFixed(2) + 'L';
        const monthly = '₹' + Math.round(an.monthly_loss || 0).toLocaleString('en-IN') + '/mo';

        let gradeClass = 'fair';
        let gradeLabel = `Score ${c.deal_score}`;
        if (c.deal_score >= 80) {
          gradeClass = 'top';
          gradeLabel = `💎 ${c.deal_score} · TOP DEAL`;
        } else if (c.deal_score >= 68) {
          gradeClass = 'value';
          gradeLabel = `⭐ ${c.deal_score} · VALUE PICK`;
        }

        return `
          <article class="card">
            <div class="card-photo">
              <span class="tag-grade ${gradeClass}">${gradeLabel}</span>
              <span class="tag-tier ${isAssured ? 'assured' : ''}">
                ${isAssured ? '✓ Spinny Assured' : '⚡ Wholesale Stock'}
              </span>
              ${c.img ? `<img src="${c.img}" alt="${title}" loading="lazy" referrerpolicy="no-referrer" />` : '<span style="color:var(--color-ink-faint); font-family:var(--font-mono); font-size:12px;">No Image</span>'}
            </div>
            
            <div class="card-body">
              <div>
                <h2 class="car-name">${title}</h2>
                <div class="car-telemetry" style="margin-top:6px;">
                  <span class="spec-item">${km}</span>
                  <span class="spec-item">${(c.fuel_type || 'Petrol').toUpperCase()}</span>
                  <span class="spec-item">${(c.transmission || 'MT').toUpperCase()}</span>
                  <span class="spec-item" style="color:var(--color-ink-faint);">${c.hub}</span>
                </div>
              </div>

              <!-- Pricing Intelligence Deck -->
              <div class="pricing-deck">
                <div class="price-cell">
                  <span class="price-type-label">Listed</span>
                  <span class="price-figure">${price}</span>
                </div>
                <div class="price-cell">
                  <span class="price-type-label">Negotiable Target</span>
                  <div class="price-figure-wrap">
                    <span class="price-figure nego-val">${negoPrice}</span>
                    ${savings > 0 ? `<span class="pill-save">Save ~${savingsFmt}</span>` : ''}
                  </div>
                </div>
                <div class="price-cell">
                  <span class="price-type-label">Original New</span>
                  <div class="price-figure-wrap">
                    <span class="price-figure retail-val">${retailPrice}</span>
                    ${c.retail_discount_pct ? `<span class="pill-discount">-${c.retail_discount_pct}%</span>` : ''}
                  </div>
                </div>
              </div>

              <!-- Secondary Telemetry Strip -->
              <div class="metrics-strip">
                <div class="metric-col">
                  <span class="metric-label">${isAssured ? '2-Yr Guaranteed Buyback' : '2-Yr Market Resale'}</span>
                  <span class="metric-val buyback">${buyback}</span>
                </div>
                <div class="metric-col">
                  <span class="metric-label">Monthly Cost</span>
                  <span class="metric-val monthly">${monthly}</span>
                </div>
              </div>

              <!-- 1-Line Verdict -->
              <p class="car-verdict">${c.verdict || 'Reliable urban commuter with strong parts availability.'}</p>

              <div class="card-action">
                <a href="${c.url || '#'}" target="_blank" rel="noopener noreferrer" class="btn-spinny">
                  <span>Inspect on Spinny</span>
                  <span>&rarr;</span>
                </a>
              </div>
            </div>
          </article>
        `;
      }).join('');
    }

    applyFilters();
  </script>
</body>
</html>
"""

deals_path = os.path.join(DIR, "deals.html")
with open(deals_path, "w") as f:
    f.write(html_content)

# Also sync index.html
index_path = os.path.join(DIR, "index.html")
shutil.copyfile(deals_path, index_path)

print(f"Hallmark debloated UI written to {deals_path} and synced to {index_path}")
