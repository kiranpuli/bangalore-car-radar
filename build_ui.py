#!/usr/bin/env python3
"""
Spinny Bangalore Deals Screener
Redesigned with rules from https://github.com/elayadesign/ai-design-skills
Visual System:
- Typography: Geist & Geist Mono, Tailwind type scale, named text styles, zero italics, text-wrap balance/pretty
- Palette: Strict dark tokens (#000000, #181818, #1F1F1F, #272727, #313131, #131209)
- Surface: Flat surfaces, zero background gradients, complete 4-sided borders
- Motion: cubic-bezier(0.22, 1, 0.36, 1), scroll reveals, tagline word-reveal (B11)
- Ergonomic Filters: Multi-faceted workbench, continuous price scrubbing, quick archetypes, active filter tags
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

alerts_path = os.path.join(DIR, "latest_alerts.json")
if not os.path.exists(alerts_path):
    alerts_path = "/tmp/latest_alerts.json"

if os.path.exists(alerts_path):
    with open(alerts_path) as f:
        alerts_list = json.load(f)
else:
    alerts_list = []

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
    if not c.get("platform"):
        c["platform"] = "Cars24" if str(c.get("id", "")).startswith("c24_") or "cars24.com" in c.get("url", "") else "Spinny"
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
alerts_json = json.dumps(alerts_list)

html_content = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate" />
  <meta http-equiv="Pragma" content="no-cache" />
  <meta http-equiv="Expires" content="0" />
  <title>Bangalore Used Cars · Top Deals Under ₹5L Screener</title>
  <meta name="description" content="Curated shortlist of verified Bangalore cars under ₹5 Lakhs with high resale retention and certified inspection across Spinny and Cars24." />
  
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600;700&family=Geist+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">
  
  <style>
    /*
      Visual System based on https://github.com/elayadesign/ai-design-skills
      - Primary Type: Geist
      - Monospace: Geist Mono
      - Dark Mode Surfaces: #131209 (Canvas), #1F1F1F (Cards/Panels), #272727 (Inputs/Controls), #313131 (Borders), #181818 (Photo Wells)
      - Text: #FFFFFF (Headings), #EDEDED (Body), #9B9B9B (Muted), #737373 (Subtle)
      - Accents: #10B981 (Emerald/Savings), #F59E0B (Amber/Top Deals), #3B82F6 (Cobalt/Actions)
      - Motion Curve: cubic-bezier(0.22, 1, 0.36, 1)
      - Zero background gradients, 4-sided borders, strict Tailwind type scale
    */
    :root {
      --font-sans: 'Geist', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      --font-mono: 'Geist Mono', ui-monospace, SFMono-Regular, monospace;

      /* Dark tokens */
      --bg-canvas: #131209;
      --bg-surface: #1F1F1F;
      --bg-subsurface: #272727;
      --bg-photo: #181818;
      --border-color: #313131;
      --border-focus: #3B82F6;

      --text-primary: #FFFFFF;
      --text-body: #EDEDED;
      --text-muted: #9B9B9B;
      --text-subtle: #737373;

      --accent-emerald: #10B981;
      --accent-emerald-bg: rgba(16, 185, 129, 0.14);
      --accent-amber: #F59E0B;
      --accent-amber-bg: rgba(245, 158, 11, 0.14);
      --accent-blue: #3B82F6;
      --accent-blue-bg: rgba(59, 130, 246, 0.14);

      /* Spacing scale */
      --sp-25: 2px;
      --sp-50: 4px;
      --sp-75: 8px;
      --sp-100: 12px;
      --sp-200: 16px;
      --sp-300: 24px;
      --sp-400: 32px;
      --sp-500: 40px;
      --sp-600: 48px;

      /* Radius scale & nested formula */
      --radius-sm: 4px;
      --radius-md: 8px;
      --radius-lg: 12px;
      --radius-xl: 16px;
      --radius-pill: 9999px;

      /* Motion */
      --ease-base: cubic-bezier(0.22, 1, 0.36, 1);
      --dur-fast: 200ms;
      --dur-normal: 300ms;
      --dur-slow: 500ms;
    }

    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }

    html, body {
      background-color: var(--bg-canvas);
      color: var(--text-body);
      font-family: var(--font-sans);
      font-size: 16px;
      line-height: 1.5;
      -webkit-font-smoothing: antialiased;
      overflow-x: clip;
    }

    /* Named Text Styles */
    .heading-1 {
      font-size: clamp(32px, 5vw, 48px);
      line-height: 1.1;
      font-weight: 600;
      letter-spacing: -0.02em;
      text-wrap: balance;
    }
    .heading-3 {
      font-size: 30px;
      line-height: 36px;
      font-weight: 600;
      letter-spacing: -0.01em;
      text-wrap: balance;
    }
    .title-1 {
      font-size: 20px;
      line-height: 28px;
      font-weight: 600;
      color: var(--text-primary);
    }
    .title-2 {
      font-size: 18px;
      line-height: 28px;
      font-weight: 600;
      color: var(--text-primary);
    }
    .title-3 {
      font-size: 16px;
      line-height: 24px;
      font-weight: 500;
      color: var(--text-primary);
    }
    .title-4 {
      font-size: 14px;
      line-height: 20px;
      font-weight: 500;
      color: var(--text-primary);
    }
    .title-5 {
      font-size: 12px;
      line-height: 16px;
      font-weight: 500;
      color: var(--text-muted);
    }
    .body-3 {
      font-size: 16px;
      line-height: 24px;
      font-weight: 400;
      color: var(--text-muted);
      text-wrap: pretty;
    }
    .body-5 {
      font-size: 14px;
      line-height: 20px;
      font-weight: 500;
      color: var(--text-muted);
    }
    .body-6 {
      font-size: 14px;
      line-height: 20px;
      font-weight: 400;
      color: var(--text-muted);
      text-wrap: pretty;
    }
    .caption-3 {
      font-family: var(--font-mono);
      font-size: 12px;
      line-height: 16px;
      font-weight: 600;
    }
    .caption-4 {
      font-family: var(--font-mono);
      font-size: 12px;
      line-height: 16px;
      font-weight: 500;
    }
    .caption-5 {
      font-family: var(--font-mono);
      font-size: 12px;
      line-height: 16px;
      font-weight: 400;
    }

    /* Container Shell */
    .shell {
      max-width: 1400px;
      margin: 0 auto;
      padding: var(--sp-300) var(--sp-200) var(--sp-800, 80px) var(--sp-200);
    }

    /* Floating Navigation Bar (B7) */
    .floating-nav {
      position: sticky;
      top: 12px;
      z-index: 50;
      margin-bottom: var(--sp-400);
      display: flex;
      justify-content: center;
    }
    .nav-inner {
      background: rgba(31, 31, 31, 0.88);
      backdrop-filter: blur(16px);
      -webkit-backdrop-filter: blur(16px);
      border: 1px solid var(--border-color);
      border-radius: var(--radius-pill);
      padding: var(--sp-75) var(--sp-200);
      display: flex;
      align-items: center;
      gap: var(--sp-200);
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
    }
    .nav-brand {
      display: flex;
      align-items: center;
      gap: var(--sp-75);
      font-weight: 600;
      font-size: 14px;
      color: var(--text-primary);
      text-decoration: none;
    }
    .pulse-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: var(--accent-emerald);
      box-shadow: 0 0 8px var(--accent-emerald);
    }
    .nav-stats {
      font-family: var(--font-mono);
      font-size: 12px;
      color: var(--text-muted);
      border-left: 1px solid var(--border-color);
      padding-left: var(--sp-200);
    }
    .nav-stats strong {
      color: var(--text-primary);
    }
    .nav-btn {
      background: var(--bg-subsurface);
      border: 1px solid var(--border-color);
      color: var(--text-body);
      font-size: 12px;
      font-weight: 500;
      padding: 6px 12px;
      border-radius: var(--radius-pill);
      cursor: pointer;
      text-decoration: none;
      transition: all var(--dur-normal) var(--ease-base);
    }
    .nav-btn:hover {
      background: var(--border-color);
      color: var(--text-primary);
    }

    /* View Mode Bar (Curated Top Deals vs Full Market) */
    .view-mode-bar {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: var(--sp-100);
      margin: 0 auto var(--sp-300) auto;
      max-width: 780px;
    }
    .view-mode-pills {
      display: inline-flex;
      background: var(--bg-surface);
      border: 1px solid var(--border-color);
      border-radius: var(--radius-pill);
      padding: 4px;
      gap: 4px;
    }
    .view-mode-pill {
      background: transparent;
      border: 1px solid transparent;
      color: var(--text-muted);
      font-size: 13px;
      font-weight: 600;
      padding: 8px 18px;
      border-radius: var(--radius-pill);
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 8px;
      transition: all var(--dur-normal) var(--ease-base);
    }
    .view-mode-pill:hover {
      color: var(--text-primary);
    }
    .view-mode-pill.active {
      background: var(--bg-subsurface);
      color: var(--text-primary);
      border-color: var(--border-color);
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.4);
    }
    .view-mode-pill.active.curated {
      border-color: rgba(245, 158, 11, 0.4);
      color: #FBBF24;
    }
    .count-pill {
      font-family: var(--font-mono);
      font-size: 11px;
      padding: 1px 7px;
      border-radius: var(--radius-pill);
      background: rgba(255, 255, 255, 0.08);
      color: inherit;
    }
    .view-mode-status {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 12px;
      color: var(--text-muted);
      font-family: var(--font-mono);
      text-align: center;
    }

    /* Alerts Drawer / Modal */
    .alerts-modal-backdrop {
      position: fixed;
      inset: 0;
      background: rgba(0, 0, 0, 0.7);
      backdrop-filter: blur(4px);
      z-index: 999;
      display: none;
      align-items: center;
      justify-content: center;
      padding: var(--sp-200);
    }
    .alerts-modal-backdrop.open {
      display: flex;
    }
    .alerts-modal {
      background: var(--bg-surface);
      border: 1px solid var(--border-color);
      border-radius: var(--radius-xl);
      max-width: 620px;
      width: 100%;
      max-height: 85vh;
      display: flex;
      flex-direction: column;
      overflow: hidden;
      box-shadow: 0 20px 40px rgba(0, 0, 0, 0.6);
    }
    .alerts-modal-header {
      padding: var(--sp-200);
      border-bottom: 1px solid var(--border-color);
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .alerts-modal-header h3 {
      font-size: 16px;
      font-weight: 600;
      color: var(--text-primary);
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .alerts-modal-close {
      background: transparent;
      border: none;
      color: var(--text-muted);
      font-size: 16px;
      cursor: pointer;
      padding: 4px;
    }
    .alerts-modal-body {
      padding: var(--sp-200);
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: var(--sp-100);
    }
    .alert-card {
      background: var(--bg-subsurface);
      border: 1px solid var(--border-color);
      border-radius: var(--radius-md);
      padding: var(--sp-100);
      display: flex;
      align-items: center;
      gap: var(--sp-100);
      text-decoration: none;
      color: inherit;
      transition: border-color var(--dur-fast) var(--ease-base);
    }
    .alert-card:hover {
      border-color: var(--accent-blue);
    }
    .alert-card-thumb {
      width: 75px;
      height: 52px;
      object-fit: contain;
      background: var(--bg-photo);
      border-radius: var(--radius-sm);
      padding: 4px;
      flex-shrink: 0;
    }
    .alert-card-info {
      flex: 1;
      min-width: 0;
    }
    .alert-card-title {
      font-size: 13px;
      font-weight: 600;
      color: var(--text-primary);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .alert-card-meta {
      font-family: var(--font-mono);
      font-size: 11px;
      color: var(--text-muted);
      display: flex;
      gap: 8px;
      margin-top: 2px;
      align-items: center;
    }
    .alert-card-price {
      font-weight: 700;
      color: var(--accent-emerald);
      font-size: 13px;
    }
    .alert-bell-btn {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      position: relative;
    }
    .alert-count-pill {
      background: var(--accent-amber);
      color: #000000;
      font-weight: 700;
      font-size: 10px;
      padding: 1px 6px;
      border-radius: var(--radius-pill);
    }

    /* Hero Section (B5) */
    .hero-section {
      text-align: center;
      margin: 0 auto var(--sp-400) auto;
      max-width: 680px;
    }
    .hero-heading {
      background: linear-gradient(90deg, #FFFFFF 0%, #9B9B9B 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      margin-bottom: var(--sp-100);
    }
    .hero-subhead {
      color: var(--text-muted);
      font-size: 16px;
      line-height: 24px;
      text-wrap: balance;
    }

    /* Mandatory Tagline Word-by-Word Reveal Section (B11) */
    .tagline-section {
      margin: 0 auto var(--sp-500) auto;
      max-width: 780px;
      text-align: center;
      padding: var(--sp-300) var(--sp-200);
      background: var(--bg-surface);
      border: 1px solid var(--border-color);
      border-radius: var(--radius-xl);
    }
    .tagline-badge {
      display: inline-block;
      font-family: var(--font-mono);
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      color: var(--accent-blue);
      background: var(--accent-blue-bg);
      border: 1px solid rgba(59, 130, 246, 0.3);
      padding: 3px 10px;
      border-radius: var(--radius-pill);
      margin-bottom: var(--sp-100);
    }
    .tagline-text {
      font-size: clamp(20px, 3.2vw, 28px);
      line-height: 1.35;
      font-weight: 600;
      letter-spacing: -0.01em;
      color: var(--text-muted);
      text-wrap: balance;
    }
    .tagline-word {
      display: inline-block;
      color: rgba(255, 255, 255, 0.28);
      transition: color 500ms var(--ease-base);
      margin-right: 0.28em;
    }
    .tagline-word.revealed {
      color: #FFFFFF;
    }

    /* Revamped Filter Console (Comprehensive Workbench) */
    .filter-console {
      background: var(--bg-surface);
      border: 1px solid var(--border-color);
      border-radius: var(--radius-xl);
      padding: var(--sp-300);
      margin-bottom: var(--sp-300);
      display: flex;
      flex-direction: column;
      gap: var(--sp-200);
    }

    /* Primary Search Row */
    .search-row {
      display: flex;
      gap: var(--sp-100);
      align-items: center;
      flex-wrap: wrap;
    }
    .search-input-wrap {
      flex: 1 1 320px;
      position: relative;
      display: flex;
      align-items: center;
    }
    .search-icon-svg {
      position: absolute;
      left: 14px;
      width: 18px;
      height: 18px;
      color: var(--text-subtle);
      pointer-events: none;
    }
    .search-field {
      width: 100%;
      background: var(--bg-subsurface);
      border: 1px solid var(--border-color);
      border-radius: var(--radius-md);
      color: var(--text-primary);
      font-family: var(--font-sans);
      font-size: 14px;
      padding: 10px 38px 10px 42px;
      outline: none;
      transition: border-color var(--dur-normal) var(--ease-base);
    }
    .search-field:focus {
      border-color: var(--border-focus);
      box-shadow: 0 0 0 2px var(--accent-blue-bg);
    }
    .search-clear-btn {
      position: absolute;
      right: 12px;
      background: transparent;
      border: none;
      color: var(--text-subtle);
      font-size: 14px;
      cursor: pointer;
      display: none;
      padding: 4px;
    }
    .search-clear-btn:hover {
      color: var(--text-primary);
    }

    .sort-wrap {
      display: flex;
      align-items: center;
      gap: var(--sp-75);
    }
    .control-label {
      font-family: var(--font-mono);
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: var(--text-subtle);
    }
    .select-dropdown {
      background: var(--bg-subsurface);
      border: 1px solid var(--border-color);
      border-radius: var(--radius-md);
      color: var(--text-body);
      font-family: var(--font-mono);
      font-size: 13px;
      padding: 9px 12px;
      outline: none;
      cursor: pointer;
      transition: border-color var(--dur-normal) var(--ease-base);
    }
    .select-dropdown:focus {
      border-color: var(--border-focus);
    }

    /* Filter Workbench Facets Grid */
    .filter-facets {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: var(--sp-200);
      padding-top: var(--sp-200);
      border-top: 1px solid var(--border-color);
    }
    .facet-col {
      display: flex;
      flex-direction: column;
      gap: var(--sp-75);
    }
    .facet-title {
      font-family: var(--font-mono);
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: var(--text-muted);
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .facet-pills {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
    }
    .facet-pill {
      background: var(--bg-subsurface);
      border: 1px solid var(--border-color);
      color: var(--text-muted);
      font-size: 12px;
      font-weight: 500;
      padding: 6px 11px;
      border-radius: var(--radius-md);
      cursor: pointer;
      user-select: none;
      display: inline-flex;
      align-items: center;
      gap: 5px;
      transition: all var(--dur-fast) var(--ease-base);
    }
    .facet-pill:hover {
      border-color: var(--text-muted);
      color: var(--text-primary);
    }
    .facet-pill.active {
      background: var(--text-primary);
      border-color: var(--text-primary);
      color: #000000;
      font-weight: 600;
    }
    .facet-pill.pill-item.active::before {
      content: "✓";
      font-weight: 800;
      font-size: 11px;
      color: #000000;
    }
    .btn-facet-reset {
      background: transparent;
      border: none;
      color: var(--text-subtle);
      font-family: var(--font-mono);
      font-size: 10px;
      cursor: pointer;
      text-transform: uppercase;
      padding: 2px 6px;
      border-radius: var(--radius-sm);
      transition: color var(--dur-fast) var(--ease-base);
    }
    .btn-facet-reset:hover {
      color: var(--text-primary);
    }

    /* Continuous Price Controls */
    .price-scrubber {
      display: flex;
      flex-direction: column;
      gap: 8px;
    }
    .price-inputs-row {
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .price-num-box {
      width: 78px;
      background: var(--bg-subsurface);
      border: 1px solid var(--border-color);
      border-radius: var(--radius-md);
      color: var(--text-primary);
      font-family: var(--font-mono);
      font-size: 13px;
      font-weight: 600;
      padding: 7px 8px;
      text-align: center;
      outline: none;
      transition: border-color var(--dur-normal) var(--ease-base);
    }
    .price-num-box:focus {
      border-color: var(--border-focus);
    }
    .price-slider-input {
      flex: 1;
      -webkit-appearance: none;
      appearance: none;
      height: 6px;
      border-radius: 3px;
      background: var(--border-color);
      outline: none;
      cursor: pointer;
      accent-color: var(--accent-blue);
    }
    .price-slider-input::-webkit-slider-thumb {
      -webkit-appearance: none;
      appearance: none;
      width: 16px;
      height: 16px;
      border-radius: 50%;
      background: var(--accent-blue);
      cursor: pointer;
      box-shadow: 0 0 6px rgba(59, 130, 246, 0.6);
    }

    /* Presets Bar */
    .presets-container {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: var(--sp-75);
      padding: var(--sp-100) 0 0 0;
      border-top: 1px solid var(--border-color);
    }
    .preset-chip-btn {
      background: transparent;
      border: 1px solid var(--border-color);
      color: var(--text-muted);
      font-size: 12px;
      font-weight: 500;
      padding: 5px 11px;
      border-radius: var(--radius-pill);
      cursor: pointer;
      transition: all var(--dur-fast) var(--ease-base);
    }
    .preset-chip-btn:hover {
      border-color: var(--text-primary);
      color: var(--text-primary);
    }
    .preset-chip-btn.active {
      background: var(--accent-blue);
      border-color: var(--accent-blue);
      color: #FFFFFF;
      font-weight: 600;
    }

    /* Active Filter Summary Strip */
    .active-filters-bar {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: var(--sp-75);
      margin-bottom: var(--sp-300);
      font-size: 13px;
    }
    .active-tag {
      background: var(--bg-surface);
      border: 1px solid var(--border-color);
      border-radius: var(--radius-md);
      padding: 4px 10px;
      font-family: var(--font-mono);
      font-size: 12px;
      color: var(--text-body);
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }
    .active-tag-remove {
      background: none;
      border: none;
      color: var(--text-subtle);
      cursor: pointer;
      font-size: 13px;
      padding: 0 2px;
      line-height: 1;
    }
    .active-tag-remove:hover {
      color: var(--text-primary);
    }
    .btn-reset-all {
      background: transparent;
      border: none;
      color: var(--accent-blue);
      font-family: var(--font-mono);
      font-size: 12px;
      cursor: pointer;
      padding: 4px 8px;
      text-decoration: underline;
    }
    .btn-reset-all:hover {
      color: #FFFFFF;
    }
    .results-count-wrap {
      margin-left: auto;
      font-family: var(--font-mono);
      font-size: 13px;
      color: var(--text-muted);
    }
    .results-count-wrap strong {
      color: var(--text-primary);
    }

    /* Cars Grid (Debloated Cards) */
    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(min(100%, 380px), 1fr));
      gap: var(--sp-300);
    }

    /* Strict Card Component per elayadesign/ai-design-skills */
    .card {
      background: var(--bg-surface);
      border: 1px solid var(--border-color);
      border-radius: var(--radius-xl);
      display: flex;
      flex-direction: column;
      overflow: hidden;
      transition: border-color var(--dur-normal) var(--ease-base), transform var(--dur-normal) var(--ease-base);
    }
    .card:hover {
      border-color: var(--text-subtle);
      transform: translateY(-2px);
    }

    /* Flat Photo slot with no gradient */
    .card-photo {
      height: 200px;
      background: var(--bg-photo);
      position: relative;
      display: flex;
      align-items: center;
      justify-content: center;
      border-bottom: 1px solid var(--border-color);
      padding: var(--sp-200);
      overflow: hidden;
    }
    .card-photo img {
      width: 100%;
      height: 100%;
      object-fit: contain;
      filter: drop-shadow(0 10px 18px rgba(0, 0, 0, 0.65));
      transition: transform var(--dur-normal) var(--ease-base);
    }
    .card:hover .card-photo img {
      transform: scale(1.04);
    }

    /* Badges */
    .badge-grade {
      position: absolute;
      top: 12px;
      left: 12px;
      font-family: var(--font-mono);
      font-size: 11px;
      font-weight: 600;
      padding: 3px 8px;
      border-radius: var(--radius-sm);
      letter-spacing: 0.04em;
      z-index: 2;
    }
    .badge-grade.top {
      background: var(--accent-amber);
      color: #000000;
      border: 1px solid var(--accent-amber);
    }
    .badge-grade.value {
      background: var(--accent-emerald);
      color: #000000;
      border: 1px solid var(--accent-emerald);
    }
    .badge-grade.fair {
      background: var(--bg-subsurface);
      border: 1px solid var(--border-color);
      color: var(--text-muted);
    }

    .badge-tier {
      position: absolute;
      top: 12px;
      right: 12px;
      font-family: var(--font-mono);
      font-size: 11px;
      font-weight: 500;
      padding: 3px 8px;
      border-radius: var(--radius-sm);
      background: var(--bg-surface);
      border: 1px solid var(--border-color);
      color: var(--text-muted);
      z-index: 2;
    }
    .badge-tier.assured {
      color: var(--accent-emerald);
      border-color: rgba(16, 185, 129, 0.4);
    }

    .badge-platform {
      position: absolute;
      bottom: 12px;
      left: 12px;
      font-family: var(--font-mono);
      font-size: 11px;
      font-weight: 600;
      padding: 3px 8px;
      border-radius: var(--radius-sm);
      letter-spacing: 0.04em;
      z-index: 2;
    }
    .badge-platform.spinny {
      background: rgba(245, 158, 11, 0.15);
      border: 1px solid rgba(245, 158, 11, 0.4);
      color: #FBBF24;
    }
    .badge-platform.cars24 {
      background: rgba(59, 130, 246, 0.15);
      border: 1px solid rgba(59, 130, 246, 0.4);
      color: #60A5FA;
    }

    .card-content {
      padding: var(--sp-200);
      display: flex;
      flex-direction: column;
      gap: var(--sp-100);
      flex: 1;
    }

    .car-title {
      font-size: 18px;
      line-height: 24px;
      font-weight: 600;
      color: var(--text-primary);
      text-wrap: balance;
    }

    .car-tags {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
    }
    .spec-tag {
      font-family: var(--font-mono);
      font-size: 11px;
      color: var(--text-muted);
      background: var(--bg-subsurface);
      border: 1px solid var(--border-color);
      padding: 2px 7px;
      border-radius: var(--radius-sm);
    }

    /* Nested Pricing Intelligence Box (Formula: radius 16px - gap 8px = 8px) */
    .pricing-box {
      display: grid;
      grid-template-columns: 1fr 1.25fr 1.1fr;
      background: var(--bg-subsurface);
      border: 1px solid var(--border-color);
      border-radius: var(--radius-md);
      padding: 10px 12px;
      gap: 8px;
    }
    .price-col {
      display: flex;
      flex-direction: column;
    }
    .price-label {
      font-family: var(--font-mono);
      font-size: 10px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: var(--text-subtle);
    }
    .price-val {
      font-family: var(--font-mono);
      font-size: 14px;
      font-weight: 600;
      color: var(--text-primary);
      margin-top: 2px;
      line-height: 1.2;
    }
    .price-val.negotiable {
      color: var(--accent-emerald);
    }
    .price-val.original {
      color: var(--text-subtle);
      text-decoration: line-through;
    }
    .savings-pill {
      font-family: var(--font-mono);
      font-size: 9px;
      font-weight: 600;
      color: var(--accent-emerald);
      background: var(--accent-emerald-bg);
      border: 1px solid rgba(16, 185, 129, 0.3);
      padding: 1px 4px;
      border-radius: 3px;
      display: inline-block;
      margin-top: 2px;
    }
    .discount-pill {
      font-family: var(--font-mono);
      font-size: 9px;
      font-weight: 600;
      color: var(--accent-blue);
      background: var(--accent-blue-bg);
      border: 1px solid rgba(59, 130, 246, 0.3);
      padding: 1px 4px;
      border-radius: 3px;
      display: inline-block;
      margin-top: 2px;
    }

    /* Value Telemetry Strip */
    .telemetry-strip {
      display: grid;
      grid-template-columns: 1.2fr 1fr;
      background: var(--bg-photo);
      border: 1px solid var(--border-color);
      border-radius: var(--radius-md);
      padding: 8px 12px;
      gap: 8px;
    }
    .telemetry-col {
      display: flex;
      flex-direction: column;
    }
    .telemetry-label {
      font-family: var(--font-mono);
      font-size: 10px;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      color: var(--text-subtle);
    }
    .telemetry-val {
      font-family: var(--font-mono);
      font-size: 13px;
      font-weight: 600;
      color: var(--text-body);
      margin-top: 1px;
    }
    .telemetry-val.buyback {
      color: var(--accent-emerald);
    }
    .telemetry-val.cost {
      color: var(--accent-blue);
    }

    /* Verdict */
    .verdict-line {
      font-size: 13px;
      color: var(--text-body);
      line-height: 1.4;
      padding-left: 10px;
      border-left: 2px solid var(--accent-blue);
      margin-top: 2px;
      text-wrap: pretty;
    }

    /* Action Button (B2 Button-md padding 8px 12px) */
    .card-footer {
      margin-top: auto;
      padding-top: var(--sp-100);
      border-top: 1px solid var(--border-color);
    }
    .cta-btn {
      display: flex;
      align-items: center;
      justify-content: space-between;
      width: 100%;
      background: transparent;
      border: 1px solid var(--border-color);
      color: var(--text-body);
      font-family: var(--font-mono);
      font-size: 13px;
      font-weight: 600;
      padding: 8px 12px;
      border-radius: var(--radius-md);
      text-decoration: none;
      transition: all var(--dur-normal) var(--ease-base);
    }
    .cta-btn:hover {
      background: var(--text-primary);
      border-color: var(--text-primary);
      color: #000000;
    }
    .cta-btn:active {
      transform: scale(0.98);
    }

    /* Empty State */
    .empty-state {
      grid-column: 1 / -1;
      padding: var(--sp-600) var(--sp-300);
      text-align: center;
      background: var(--bg-surface);
      border: 1px dashed var(--border-color);
      border-radius: var(--radius-xl);
    }
    .empty-state h3 {
      font-size: 20px;
      font-weight: 600;
      margin-bottom: 8px;
      color: var(--text-primary);
    }
    .empty-state p {
      font-size: 14px;
      color: var(--text-muted);
      margin-bottom: 20px;
    }

    /* Focus visible rings */
    button:focus-visible, input:focus-visible, select:focus-visible, a:focus-visible {
      outline: 2px solid var(--accent-blue);
      outline-offset: 2px;
    }

    /* Responsive Mobile @ 390px */
    @media (max-width: 640px) {
      .shell {
        padding: 16px 12px 60px 12px;
      }
      .filter-console {
        padding: 14px;
      }
      .filter-facets {
        grid-template-columns: 1fr;
      }
      .pricing-box {
        grid-template-columns: 1fr;
        gap: 6px;
      }
      .telemetry-strip {
        grid-template-columns: 1fr;
        gap: 6px;
      }
    }
  </style>
</head>
<body>

  <!-- Sticky Floating Nav (B7) -->
  <nav class="floating-nav" aria-label="Main Navigation">
    <div class="nav-inner">
      <a href="#" class="nav-brand">
        <span class="pulse-dot"></span>
        <span>Bangalore Car Radar</span>
      </a>
      <div class="nav-stats">
        Top Deals: <strong id="tele-curated">0</strong> (<span id="tele-total">0</span> market)
      </div>
      <button class="nav-btn alert-bell-btn" onclick="toggleAlertsModal()" title="View Recent Deal Alerts">
        <span>🔔 Alerts</span>
        <span id="badge-alerts-count" class="alert-count-pill">0</span>
      </button>
      <button class="nav-btn" onclick="scrollToFilters()">Filters</button>
    </div>
  </nav>

  <div class="shell">
    <!-- Hero Section (B5) -->
    <header class="hero-section">
      <h1 class="heading-1 hero-heading">Bangalore Top Used Car Deals</h1>
      <p class="body-3 hero-subhead">
        Curated shortlist of verified Bangalore cars under ₹5 Lakhs with high resale retention and certified inspection across Spinny and Cars24.
      </p>
    </header>

    <!-- Curation Mode Switcher -->
    <div class="view-mode-bar">
      <div class="view-mode-pills">
        <button type="button" class="view-mode-pill active curated" id="btn-mode-curated" onclick="setViewMode('curated')">
          <span>🔥 Top Deals to Consider</span>
          <span class="count-pill" id="badge-curated-count">0</span>
        </button>
        <button type="button" class="view-mode-pill" id="btn-mode-all" onclick="setViewMode('all')">
          <span>📦 Full Inventory</span>
          <span class="count-pill" id="badge-all-count">0</span>
        </button>
      </div>
      <div class="view-mode-status" id="mode-status-text">
        <span class="pulse-dot"></span>
        <span>Curated view: Under ₹5.0L · Deal Score 80+ · Low Mileage (&lt; 80k km) · Certified Assured</span>
      </div>
    </div>

    <!-- Mandatory Tagline Word-by-Word Reveal Section (B11) -->
    <section class="tagline-section" id="tagline-reveal" aria-label="Core Commitment">
      <span class="tagline-badge">Verified Deal Intelligence</span>
      <p class="tagline-text" id="tagline-words">
        <!-- Injected via JavaScript for scroll word-by-word reveal -->
      </p>
    </section>

    <!-- Revamped Filter Console -->
    <section class="filter-console" id="filter-workbench" aria-label="Filter Controls">
      <!-- Search & Sort Row -->
      <div class="search-row">
        <div class="search-input-wrap">
          <svg class="search-icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8"></circle>
            <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
          </svg>
          <input 
            type="text" 
            id="ctrl-search" 
            class="search-field" 
            placeholder="Search by model, hub location, variant, or fuel..." 
            oninput="onSearchInput(this.value)"
          />
          <button type="button" id="btn-clear-search" class="search-clear-btn" onclick="clearSearch()" title="Clear search">✕</button>
        </div>

        <div class="sort-wrap">
          <label for="ctrl-sort" class="control-label">Sort By:</label>
          <select id="ctrl-sort" class="select-dropdown" onchange="onSortChange(this.value)">
            <option value="score">Best Value Score</option>
            <option value="price_asc">Listed Price: Low to High</option>
            <option value="price_desc">Listed Price: High to Low</option>
            <option value="nego_asc">Negotiable Floor: Low to High</option>
            <option value="discount_desc">Highest % Off Original Retail</option>
            <option value="year_desc">Year: Newest First</option>
            <option value="km_asc">Mileage: Lowest KM</option>
          </select>
        </div>
      </div>

      <!-- Unified Multi-Select Facets Grid -->
      <div class="filter-facets">
        <!-- Platform Facet (Multi-Select) -->
        <div class="facet-col">
          <div class="facet-title">
            <span>Listing Platform</span>
            <button type="button" class="btn-facet-reset" onclick="clearMultiFilter('platforms')">Reset</button>
          </div>
          <div class="facet-pills" id="platforms-pills">
            <button type="button" class="facet-pill pill-all active" onclick="clearMultiFilter('platforms')">Both Platforms</button>
            <button type="button" class="facet-pill pill-item" data-val="Spinny" onclick="toggleMultiFilter('platforms', 'Spinny')">Spinny (<span id="count-spinny">0</span>)</button>
            <button type="button" class="facet-pill pill-item" data-val="Cars24" onclick="toggleMultiFilter('platforms', 'Cars24')">Cars24 (<span id="count-cars24">0</span>)</button>
          </div>
        </div>

        <!-- Budget Scrubber Facet -->
        <div class="facet-col">
          <div class="facet-title">
            <span>Budget (₹ Lakhs)</span>
            <button type="button" class="btn-facet-reset" onclick="clearPrice()">Reset</button>
          </div>
          <div class="price-scrubber">
            <div class="price-inputs-row">
              <span class="caption-4" style="color:var(--text-subtle);">₹</span>
              <input type="number" id="ctrl-min-price" class="price-num-box" min="0" max="30" step="0.1" placeholder="Min" oninput="onPriceChange()" />
              <span style="color:var(--text-subtle);">–</span>
              <input type="number" id="ctrl-max-price" class="price-num-box" min="0" max="30" step="0.1" placeholder="Max" oninput="onPriceChange()" />
              <input type="range" id="ctrl-price-range" class="price-slider-input" min="2" max="20" step="0.25" value="5" oninput="onSliderChange(this.value)" title="Scrub Max Budget" />
            </div>
            <div class="facet-pills">
              <button type="button" class="facet-pill" onclick="setMaxBudget(4.0)">≤ ₹4L</button>
              <button type="button" class="facet-pill" onclick="setMaxBudget(5.0)">≤ ₹5L</button>
              <button type="button" class="facet-pill" onclick="setMaxBudget(7.0)">≤ ₹7L</button>
              <button type="button" class="facet-pill" onclick="setMaxBudget(10.0)">≤ ₹10L</button>
              <button type="button" class="facet-pill" onclick="clearPrice()">Any</button>
            </div>
          </div>
        </div>

        <!-- Quality & Verification Facet (Multi-Select) -->
        <div class="facet-col">
          <div class="facet-title">
            <span>Quality & Assurance</span>
            <button type="button" class="btn-facet-reset" onclick="clearMultiFilter('qualities')">Reset</button>
          </div>
          <div class="facet-pills" id="qualities-pills">
            <button type="button" class="facet-pill pill-all" onclick="clearMultiFilter('qualities')">All Cars</button>
            <button type="button" class="facet-pill pill-item active" data-val="top_deal" onclick="toggleMultiFilter('qualities', 'top_deal')">💎 Top Deals (80+)</button>
            <button type="button" class="facet-pill pill-item" data-val="assured" onclick="toggleMultiFilter('qualities', 'assured')">🛡️ Certified Assured</button>
            <button type="button" class="facet-pill pill-item" data-val="high_discount" onclick="toggleMultiFilter('qualities', 'high_discount')">💰 50%+ Off New</button>
          </div>
        </div>

        <!-- Gearbox & Fuel Facet (Multi-Select) -->
        <div class="facet-col">
          <div class="facet-title">
            <span>Gearbox & Fuel</span>
            <button type="button" class="btn-facet-reset" onclick="clearMultiFilter('transmissions'); clearMultiFilter('fuels');">Reset</button>
          </div>
          <div class="facet-pills" id="transmissions-pills" style="margin-bottom:6px;">
            <button type="button" class="facet-pill pill-all active" onclick="clearMultiFilter('transmissions')">All Trans</button>
            <button type="button" class="facet-pill pill-item" data-val="automatic" onclick="toggleMultiFilter('transmissions', 'automatic')">Automatic</button>
            <button type="button" class="facet-pill pill-item" data-val="manual" onclick="toggleMultiFilter('transmissions', 'manual')">Manual</button>
          </div>
          <div class="facet-pills" id="fuels-pills">
            <button type="button" class="facet-pill pill-all active" onclick="clearMultiFilter('fuels')">All Fuels</button>
            <button type="button" class="facet-pill pill-item" data-val="petrol" onclick="toggleMultiFilter('fuels', 'petrol')">Petrol</button>
            <button type="button" class="facet-pill pill-item" data-val="diesel" onclick="toggleMultiFilter('fuels', 'diesel')">Diesel</button>
            <button type="button" class="facet-pill pill-item" data-val="cng" onclick="toggleMultiFilter('fuels', 'cng')">CNG</button>
          </div>
        </div>

        <!-- Manufacturer Facet (Multi-Select) -->
        <div class="facet-col" style="grid-column: 1 / -1;">
          <div class="facet-title">
            <span>Manufacturers (Select multiple brands simultaneously)</span>
            <button type="button" class="btn-facet-reset" onclick="clearMultiFilter('brands')">All Brands</button>
          </div>
          <div class="facet-pills" id="brands-pills">
            <button type="button" class="facet-pill pill-all active" onclick="clearMultiFilter('brands')">All Brands</button>
            <button type="button" class="facet-pill pill-item" data-val="maruti" onclick="toggleMultiFilter('brands', 'maruti')">Maruti (<span id="count-maruti">0</span>)</button>
            <button type="button" class="facet-pill pill-item" data-val="hyundai" onclick="toggleMultiFilter('brands', 'hyundai')">Hyundai (<span id="count-hyundai">0</span>)</button>
            <button type="button" class="facet-pill pill-item" data-val="tata" onclick="toggleMultiFilter('brands', 'tata')">Tata (<span id="count-tata">0</span>)</button>
            <button type="button" class="facet-pill pill-item" data-val="renault" onclick="toggleMultiFilter('brands', 'renault')">Renault (<span id="count-renault">0</span>)</button>
            <button type="button" class="facet-pill pill-item" data-val="honda" onclick="toggleMultiFilter('brands', 'honda')">Honda (<span id="count-honda">0</span>)</button>
            <button type="button" class="facet-pill pill-item" data-val="volkswagen" onclick="toggleMultiFilter('brands', 'volkswagen')">Volkswagen (<span id="count-volkswagen">0</span>)</button>
            <button type="button" class="facet-pill pill-item" data-val="toyota" onclick="toggleMultiFilter('brands', 'toyota')">Toyota (<span id="count-toyota">0</span>)</button>
            <button type="button" class="facet-pill pill-item" data-val="mahindra" onclick="toggleMultiFilter('brands', 'mahindra')">Mahindra (<span id="count-mahindra">0</span>)</button>
            <button type="button" class="facet-pill pill-item" data-val="ford" onclick="toggleMultiFilter('brands', 'ford')">Ford (<span id="count-ford">0</span>)</button>
            <button type="button" class="facet-pill pill-item" data-val="kia" onclick="toggleMultiFilter('brands', 'kia')">Kia (<span id="count-kia">0</span>)</button>
            <button type="button" class="facet-pill pill-item" data-val="skoda" onclick="toggleMultiFilter('brands', 'skoda')">Skoda (<span id="count-skoda">0</span>)</button>
          </div>
        </div>

        <!-- Age & Mileage Facet -->
        <div class="facet-col" style="grid-column: 1 / -1;">
          <div class="facet-title">
            <span>Age & Mileage Ceilings</span>
            <button type="button" class="btn-facet-reset" onclick="setYear(0, document.querySelector('#year-pills .facet-pill')); setMaxKm(0, document.querySelector('#km-pills .facet-pill'));">Reset</button>
          </div>
          <div style="display:flex; flex-wrap:wrap; gap:var(--sp-200); align-items:center;">
            <div class="facet-pills" id="year-pills">
              <span class="control-label" style="align-self:center; margin-right:4px;">Min Year:</span>
              <button type="button" class="facet-pill active" onclick="setYear(0, this)">Any Year</button>
              <button type="button" class="facet-pill" onclick="setYear(2022, this)">2022+</button>
              <button type="button" class="facet-pill" onclick="setYear(2020, this)">2020+</button>
              <button type="button" class="facet-pill" onclick="setYear(2018, this)">2018+</button>
              <button type="button" class="facet-pill" onclick="setYear(2016, this)">2016+</button>
            </div>
            <div class="facet-pills" id="km-pills">
              <span class="control-label" style="align-self:center; margin-right:4px;">Max Mileage:</span>
              <button type="button" class="facet-pill active" onclick="setMaxKm(0, this)">Any KM</button>
              <button type="button" class="facet-pill" onclick="setMaxKm(30000, this)">&le; 30k km</button>
              <button type="button" class="facet-pill" onclick="setMaxKm(50000, this)">&le; 50k km</button>
              <button type="button" class="facet-pill" onclick="setMaxKm(80000, this)">&le; 80k km</button>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Active Filters Summary Strip -->
    <div class="active-filters-bar" id="active-tags-strip">
      <span class="caption-4" style="color:var(--text-subtle);">Active Filters:</span>
      <div id="active-tags-container" style="display:inline-flex; flex-wrap:wrap; gap:6px;"></div>
      <button class="btn-reset-all" onclick="resetAll()">Reset All</button>

      <div class="results-count-wrap">
        Showing <strong id="res-count">0</strong> verified vehicles
      </div>
    </div>

    <!-- Cards Grid -->
    <main class="grid" id="cars-grid" aria-live="polite"></main>
  </div>

  <!-- Deal Alerts Modal -->
  <div class="alerts-modal-backdrop" id="alerts-modal-backdrop" onclick="closeAlertsModalOnBackdrop(event)">
    <div class="alerts-modal" role="dialog" aria-modal="true" aria-labelledby="alerts-modal-title">
      <div class="alerts-modal-header">
        <h3 id="alerts-modal-title">🔔 Recent Top Deal Alerts (&lt; ₹5L)</h3>
        <button class="alerts-modal-close" onclick="toggleAlertsModal()" title="Close">✕</button>
      </div>
      <div style="padding:12px 16px; background:var(--bg-subsurface); border-bottom:1px solid var(--border-color); display:flex; justify-content:space-between; align-items:center;">
        <span class="caption-5" style="color:var(--text-muted);">Dispatches automatically when deals under ₹5L are discovered.</span>
        <button class="nav-btn" id="btn-req-notify" onclick="requestBrowserNotifications()">Enable Desktop Alerts</button>
      </div>
      <div class="alerts-modal-body" id="alerts-modal-body">
        <!-- Injected via JavaScript -->
      </div>
    </div>
  </div>

  <script>
    const CARS = """ + cars_json + """;
    const ALERTS = """ + alerts_json + """;

    // Application state - Defaults strictly to Curated Top Deals to Consider (< ₹5L, Score 80+)
    const state = {
      viewMode: 'curated',
      search: '',
      min_year: 0,
      min_price: 0,
      max_price: 500000,
      max_km: 80000,
      sort: 'score',
      platforms: new Set(),
      brands: new Set(),
      transmissions: new Set(),
      fuels: new Set(),
      qualities: new Set(['top_deal'])
    };

    // Initialize counts
    const spinnyCount = CARS.filter(c => (c.platform || '').toLowerCase() === 'spinny').length;
    const cars24Count = CARS.filter(c => (c.platform || '').toLowerCase() === 'cars24').length;
    const curatedCars = CARS.filter(c => (c.price || 0) <= 500000 && (c.deal_score || 0) >= 80 && (c.mileage || 0) <= 80000);
    const curatedCount = curatedCars.length;

    const teleTotal = document.getElementById('tele-total');
    if (teleTotal) teleTotal.textContent = CARS.length.toLocaleString('en-IN');
    const teleCurated = document.getElementById('tele-curated');
    if (teleCurated) teleCurated.textContent = curatedCount.toLocaleString('en-IN');
    const badgeCurated = document.getElementById('badge-curated-count');
    if (badgeCurated) badgeCurated.textContent = curatedCount.toLocaleString('en-IN');
    const badgeAll = document.getElementById('badge-all-count');
    if (badgeAll) badgeAll.textContent = CARS.length.toLocaleString('en-IN');
    const badgeAlerts = document.getElementById('badge-alerts-count');
    if (badgeAlerts) badgeAlerts.textContent = ALERTS.length.toLocaleString('en-IN');

    const countAll = document.getElementById('count-all');
    if (countAll) countAll.textContent = CARS.length.toLocaleString('en-IN');
    const countSpinny = document.getElementById('count-spinny');
    if (countSpinny) countSpinny.textContent = spinnyCount.toLocaleString('en-IN');
    const countCars24 = document.getElementById('count-cars24');
    if (countCars24) countCars24.textContent = cars24Count.toLocaleString('en-IN');

    // Dynamic brand counts
    ['maruti', 'hyundai', 'tata', 'renault', 'honda', 'volkswagen', 'toyota', 'mahindra', 'ford', 'kia', 'skoda'].forEach(b => {
      const el = document.getElementById(`count-${b}`);
      if (el) {
        const cnt = CARS.filter(c => (c.make || '').toLowerCase().includes(b)).length;
        el.textContent = cnt.toLocaleString('en-IN');
      }
    });

    // Initialize inputs to curated defaults
    const ctrlMaxPrice = document.getElementById('ctrl-max-price');
    if (ctrlMaxPrice) ctrlMaxPrice.value = '5.0';
    const ctrlSlider = document.getElementById('ctrl-price-range');
    if (ctrlSlider) ctrlSlider.value = 5.0;

    // Set curated default km pill active (<= 80k km)
    document.querySelectorAll('#km-pills .facet-pill').forEach(b => {
      if (b.textContent.includes('80k')) b.classList.add('active');
      else b.classList.remove('active');
    });

    // Word-by-word reveal for B11 tagline
    const taglineContent = "Transparent pricing and verified mechanical telemetry. Every Bangalore car evaluated before you negotiate.";
    const taglineEl = document.getElementById('tagline-words');
    if (taglineEl) {
      taglineEl.innerHTML = taglineContent.split(' ').map((word, i) => `<span class="tagline-word" data-w="${i}">${word}</span>`).join(' ');
      
      if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
        document.querySelectorAll('.tagline-word').forEach(w => w.classList.add('revealed'));
      } else {
        const observer = new IntersectionObserver((entries) => {
          entries.forEach(entry => {
            if (entry.isIntersecting) {
              const words = entry.target.querySelectorAll('.tagline-word');
              words.forEach((w, idx) => {
                setTimeout(() => {
                  w.classList.add('revealed');
                }, idx * 60);
              });
              observer.unobserve(entry.target);
            }
          });
        }, { threshold: 0.15 });
        observer.observe(document.getElementById('tagline-reveal'));
      }
    }

    function scrollToFilters() {
      const el = document.getElementById('filter-workbench');
      if (el) el.scrollIntoView({ behavior: 'smooth' });
    }

    // View Mode Switcher (Curated Top Deals vs All Market)
    function setViewMode(mode) {
      state.viewMode = mode;
      const btnCurated = document.getElementById('btn-mode-curated');
      const btnAll = document.getElementById('btn-mode-all');
      const statusText = document.getElementById('mode-status-text');

      if (mode === 'curated') {
        if (btnCurated) btnCurated.classList.add('active', 'curated');
        if (btnAll) btnAll.classList.remove('active');
        if (statusText) statusText.innerHTML = '<span class="pulse-dot"></span><span>Curated view: Under ₹5.0L · Deal Score 80+ · Low Mileage (&lt; 80k km)</span>';

        state.max_price = 500000;
        state.max_km = 80000;
        state.qualities.clear();
        state.qualities.add('top_deal');

        const maxInput = document.getElementById('ctrl-max-price');
        if (maxInput) maxInput.value = '5.0';
        const slider = document.getElementById('ctrl-price-range');
        if (slider) slider.value = 5.0;

        document.querySelectorAll('#km-pills .facet-pill').forEach(b => {
          if (b.textContent.includes('80k')) b.classList.add('active');
          else b.classList.remove('active');
        });
      } else {
        if (btnCurated) btnCurated.classList.remove('active', 'curated');
        if (btnAll) btnAll.classList.add('active');
        if (statusText) statusText.innerHTML = '<span class="pulse-dot" style="background:var(--accent-blue);"></span><span>Showing all verified vehicles across Bangalore (Spinny + Cars24).</span>';

        state.max_price = 0;
        state.max_km = 0;
        state.qualities.delete('top_deal');

        const maxInput = document.getElementById('ctrl-max-price');
        if (maxInput) maxInput.value = '';
        const slider = document.getElementById('ctrl-price-range');
        if (slider) slider.value = 20;

        document.querySelectorAll('#km-pills .facet-pill').forEach((b, idx) => {
          if (idx === 0) b.classList.add('active');
          else b.classList.remove('active');
        });
      }
      updateMultiFilterUI('qualities');
      applyFilters();
    }

    // Deal Alerts Drawer / Modal
    function toggleAlertsModal() {
      const modal = document.getElementById('alerts-modal-backdrop');
      if (modal) {
        modal.classList.toggle('open');
      }
    }

    function closeAlertsModalOnBackdrop(e) {
      if (e.target.id === 'alerts-modal-backdrop') {
        toggleAlertsModal();
      }
    }

    function renderAlertsList() {
      const body = document.getElementById('alerts-modal-body');
      if (!body) return;
      if (!ALERTS.length) {
        body.innerHTML = '<p style="color:var(--text-muted); padding:20px; text-align:center;">No recent alerts recorded yet. Daily monitor checks morning & evening.</p>';
        return;
      }
      body.innerHTML = ALERTS.map(a => {
        const title = `${a.make_year} ${a.make} ${a.model} ${a.variant || ''}`.trim();
        const price = '₹' + (a.price / 100000).toFixed(2) + 'L';
        const negoPrice = a.negotiable_price ? ('₹' + (a.negotiable_price / 100000).toFixed(2) + 'L') : price;
        const km = (a.mileage / 1000).toFixed(0) + 'k km';
        const isCars24 = (a.platform || '').toLowerCase() === 'cars24';
        const platBadge = isCars24 ? 'badge-platform cars24' : 'badge-platform spinny';

        return `
          <a href="${a.url || '#'}" target="_blank" rel="noopener noreferrer" class="alert-card">
            ${a.img ? `<img src="${a.img}" class="alert-card-thumb" alt="${title}" />` : '<div class="alert-card-thumb"></div>'}
            <div class="alert-card-info">
              <div style="display:flex; justify-content:space-between; align-items:center;">
                <span class="alert-card-title">${title}</span>
                <span class="${platBadge}" style="position:static; padding:1px 6px; font-size:10px;">${a.platform}</span>
              </div>
              <div class="alert-card-meta">
                <span class="alert-card-price">${price}</span>
                <span>(Nego: ${negoPrice})</span>
                <span>·</span>
                <span>${km}</span>
                <span>·</span>
                <span style="color:var(--accent-amber); font-weight:600;">Score ${a.deal_score}</span>
              </div>
              <div class="caption-5" style="color:var(--text-subtle); margin-top:2px;">Discovered: ${a.timestamp} · ${a.hub || 'Bangalore'}</div>
            </div>
            <span style="font-size:14px; color:var(--accent-blue); padding-right:4px;">&rarr;</span>
          </a>
        `;
      }).join('');
    }

    function requestBrowserNotifications() {
      if (!('Notification' in window)) {
        alert('Desktop notifications are not supported by this browser.');
        return;
      }
      Notification.requestPermission().then(permission => {
        const btn = document.getElementById('btn-req-notify');
        if (permission === 'granted') {
          if (btn) btn.textContent = '✓ Desktop Alerts Active';
          new Notification('🔥 Bangalore Deal Alerts Active', {
            body: 'You will receive desktop alerts when high-conviction car deals (< ₹5L) are found!',
            icon: 'https://www.spinny.com/favicon.ico'
          });
        } else {
          if (btn) btn.textContent = 'Permission Denied';
        }
      });
    }

    // Search input handler
    function onSearchInput(val) {
      state.search = (val || '').toLowerCase().trim();
      const clearBtn = document.getElementById('btn-clear-search');
      if (clearBtn) clearBtn.style.display = state.search ? 'block' : 'none';
      applyFilters();
    }

    function clearSearch() {
      const input = document.getElementById('ctrl-search');
      if (input) input.value = '';
      onSearchInput('');
    }

    // Sort handler
    function onSortChange(val) {
      state.sort = val;
      applyFilters();
    }

    // Unified Multi-Filter Handlers
    function toggleMultiFilter(groupKey, val) {
      if (!state[groupKey]) return;
      if (state[groupKey].has(val)) {
        state[groupKey].delete(val);
      } else {
        state[groupKey].add(val);
      }
      updateMultiFilterUI(groupKey);
      applyFilters();
    }

    function clearMultiFilter(groupKey) {
      if (!state[groupKey]) return;
      state[groupKey].clear();
      updateMultiFilterUI(groupKey);
      applyFilters();
    }

    function updateMultiFilterUI(groupKey) {
      const container = document.getElementById(`${groupKey}-pills`);
      if (!container) return;
      const set = state[groupKey];
      const allBtn = container.querySelector('.pill-all');
      const items = container.querySelectorAll('.pill-item');

      if (set.size === 0) {
        if (allBtn) allBtn.classList.add('active');
        items.forEach(btn => btn.classList.remove('active'));
      } else {
        if (allBtn) allBtn.classList.remove('active');
        items.forEach(btn => {
          const val = btn.getAttribute('data-val');
          if (set.has(val)) {
            btn.classList.add('active');
          } else {
            btn.classList.remove('active');
          }
        });
      }
    }

    function updateAllMultiFilterUIs() {
      ['platforms', 'brands', 'transmissions', 'fuels', 'qualities'].forEach(updateMultiFilterUI);
    }

    // Year handler
    function setYear(year, btn) {
      state.min_year = Number(year);
      document.querySelectorAll('#year-pills .facet-pill').forEach(b => b.classList.remove('active'));
      if (btn) btn.classList.add('active');
      applyFilters();
    }

    // Mileage handler
    function setMaxKm(km, btn) {
      state.max_km = Number(km);
      document.querySelectorAll('#km-pills .facet-pill').forEach(b => b.classList.remove('active'));
      if (btn) btn.classList.add('active');
      applyFilters();
    }

    // Continuous Price Controls & Quick Budget Caps
    function setMaxBudget(val) {
      const maxInput = document.getElementById('ctrl-max-price');
      const slider = document.getElementById('ctrl-price-range');
      if (val > 0) {
        if (maxInput) maxInput.value = val.toFixed(1);
        state.max_price = val * 100000;
        if (slider) slider.value = Math.min(20, val);
      } else {
        if (maxInput) maxInput.value = '';
        state.max_price = 0;
        if (slider) slider.value = 20;
      }
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
      applyFilters();
    }

    function onSliderChange(val) {
      const num = parseFloat(val);
      const maxInput = document.getElementById('ctrl-max-price');
      if (num >= 20) {
        if (maxInput) maxInput.value = '';
        state.max_price = 0;
      } else {
        maxInput.value = num.toFixed(1);
        state.max_price = num * 100000;
      }
      applyFilters();
    }

    function clearPrice() {
      const minInput = document.getElementById('ctrl-min-price');
      if (minInput) minInput.value = '';
      const maxInput = document.getElementById('ctrl-max-price');
      if (maxInput) maxInput.value = '';
      const slider = document.getElementById('ctrl-price-range');
      if (slider) slider.value = 20;
      state.min_price = 0;
      state.max_price = 0;
      applyFilters();
    }

    function resetAll() {
      state.viewMode = 'curated';
      state.search = '';
      state.min_year = 0;
      state.min_price = 0;
      state.max_price = 500000;
      state.max_km = 80000;
      state.sort = 'score';

      state.platforms.clear();
      state.brands.clear();
      state.transmissions.clear();
      state.fuels.clear();
      state.qualities.clear();
      state.qualities.add('top_deal');

      document.getElementById('ctrl-search').value = '';
      document.getElementById('btn-clear-search').style.display = 'none';
      document.getElementById('ctrl-min-price').value = '';
      document.getElementById('ctrl-max-price').value = '5.0';
      const slider = document.getElementById('ctrl-price-range');
      if (slider) slider.value = 5.0;
      document.getElementById('ctrl-sort').value = 'score';

      const btnCurated = document.getElementById('btn-mode-curated');
      const btnAll = document.getElementById('btn-mode-all');
      if (btnCurated) btnCurated.classList.add('active', 'curated');
      if (btnAll) btnAll.classList.remove('active');

      const statusText = document.getElementById('mode-status-text');
      if (statusText) statusText.innerHTML = '<span class="pulse-dot"></span><span>Curated view: Under ₹5.0L · Deal Score 80+ · Low Mileage (&lt; 80k km)</span>';

      document.querySelectorAll('#year-pills .facet-pill').forEach((p, idx) => {
        if (idx === 0) p.classList.add('active');
        else p.classList.remove('active');
      });

      document.querySelectorAll('#km-pills .facet-pill').forEach(b => {
        if (b.textContent.includes('80k')) b.classList.add('active');
        else b.classList.remove('active');
      });

      updateAllMultiFilterUIs();
      applyFilters();
    }

    function renderActiveTags() {
      const container = document.getElementById('active-tags-container');
      if (!container) return;
      const tags = [];

      if (state.viewMode === 'curated' && state.max_price === 500000 && state.max_km === 80000 && state.qualities.has('top_deal')) {
        tags.push({ label: '🔥 Curated: Under ₹5L & Score 80+', clear: () => setViewMode('all') });
      }

      if (state.search) {
        tags.push({ label: `Search: "${state.search}"`, clear: () => clearSearch() });
      }

      if (state.platforms.size > 0) {
        state.platforms.forEach(plat => {
          tags.push({ label: `Platform: ${plat}`, clear: () => toggleMultiFilter('platforms', plat) });
        });
      }

      if (state.min_price > 0 || (state.max_price > 0 && state.viewMode !== 'curated')) {
        const minL = state.min_price ? (state.min_price / 100000).toFixed(1) : '0';
        const maxL = state.max_price ? (state.max_price / 100000).toFixed(1) : 'Any';
        tags.push({ label: `Budget: ₹${minL}L – ₹${maxL}L`, clear: () => clearPrice() });
      }

      if (state.brands.size > 0) {
        state.brands.forEach(b => {
          tags.push({ label: `Brand: ${b.toUpperCase()}`, clear: () => toggleMultiFilter('brands', b) });
        });
      }

      if (state.transmissions.size > 0) {
        state.transmissions.forEach(t => {
          tags.push({ label: `Gearbox: ${t.charAt(0).toUpperCase() + t.slice(1)}`, clear: () => toggleMultiFilter('transmissions', t) });
        });
      }

      if (state.fuels.size > 0) {
        state.fuels.forEach(f => {
          tags.push({ label: `Fuel: ${f.toUpperCase()}`, clear: () => toggleMultiFilter('fuels', f) });
        });
      }

      if (state.qualities.size > 0) {
        const qualityLabels = {
          top_deal: '💎 Top Deals (80+)',
          assured: '🛡️ Certified Assured',
          high_discount: '💰 50%+ Off New'
        };
        state.qualities.forEach(q => {
          if (state.viewMode === 'curated' && q === 'top_deal') return;
          tags.push({ label: qualityLabels[q] || q, clear: () => toggleMultiFilter('qualities', q) });
        });
      }

      if (state.min_year > 0) {
        tags.push({ label: `Year: ${state.min_year}+`, clear: () => setYear(0, document.querySelector('#year-pills .facet-pill')) });
      }

      if (state.max_km > 0 && !(state.viewMode === 'curated' && state.max_km === 80000)) {
        tags.push({ label: `Mileage: ≤ ${Math.round(state.max_km / 1000)}k km`, clear: () => setMaxKm(0, document.querySelector('#km-pills .facet-pill')) });
      }

      window._activeTags = tags;

      if (!tags.length) {
        container.innerHTML = '<span class="caption-5" style="color:var(--text-subtle);">None (Showing all Bangalore inventory)</span>';
      } else {
        container.innerHTML = tags.map((t, idx) => `
          <span class="active-tag">
            <span>${t.label}</span>
            <button type="button" class="active-tag-remove" onclick="window._activeTags[${idx}].clear()" title="Remove filter">✕</button>
          </span>
        `).join('');
      }
    }

    function applyFilters() {
      let filtered = CARS.filter(c => {
        // Search
        if (state.search) {
          const text = `${c.make_year} ${c.make} ${c.model} ${c.variant || ''} ${c.hub || ''} ${c.transmission || ''} ${c.fuel_type || ''}`.toLowerCase();
          if (!text.includes(state.search)) return false;
        }

        // Platform (Multi-Select)
        if (state.platforms.size > 0) {
          const p = (c.platform || '').toLowerCase();
          const match = [...state.platforms].some(plat => plat.toLowerCase() === p);
          if (!match) return false;
        }

        // Brand (Multi-Select, matching includes for Maruti / Maruti Suzuki)
        if (state.brands.size > 0) {
          const make = (c.make || '').toLowerCase();
          const match = [...state.brands].some(b => make.includes(b.toLowerCase()));
          if (!match) return false;
        }

        // Transmission (Multi-Select)
        if (state.transmissions.size > 0) {
          const t = (c.transmission || '').toLowerCase();
          const isAuto = t.includes('auto') || t.includes('amt') || t.includes('at') || t.includes('cvt') || t.includes('dsg') || t.includes('dct');
          const wantAuto = state.transmissions.has('automatic');
          const wantManual = state.transmissions.has('manual');
          if (wantAuto && wantManual) {
            // Both selected -> pass
          } else if (wantAuto && !isAuto) {
            return false;
          } else if (wantManual && isAuto) {
            return false;
          }
        }

        // Fuel (Multi-Select)
        if (state.fuels.size > 0) {
          const f = (c.fuel_type || '').toLowerCase();
          const match = [...state.fuels].some(fuel => f.includes(fuel.toLowerCase()));
          if (!match) return false;
        }

        // Quality (Multi-Select: satisfies all selected criteria)
        if (state.qualities.size > 0) {
          if (state.qualities.has('top_deal') && (c.deal_score || 0) < 80) return false;
          if (state.qualities.has('assured') && (c.category !== 'assured')) return false;
          if (state.qualities.has('high_discount') && (c.retail_discount_pct || 0) < 50) return false;
        }

        // Budget range
        if (state.min_price > 0 && (c.price || 0) < state.min_price) return false;
        if (state.max_price > 0 && (c.price || 0) > state.max_price) return false;

        // Year & Mileage ceilings
        if (state.min_year > 0 && (c.make_year || 0) < state.min_year) return false;
        if (state.max_km > 0 && (c.mileage || 0) > state.max_km) return false;

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
        filtered.sort((a, b) => (b.deal_score || 0) - (a.deal_score || 0));
      }

      const resCount = document.getElementById('res-count');
      if (resCount) resCount.textContent = filtered.length.toLocaleString('en-IN');
      renderActiveTags();
      renderCards(filtered);
    }

    function renderCards(list) {
      const grid = document.getElementById('cars-grid');
      if (!list.length) {
        grid.innerHTML = `
          <div class="empty-state">
            <h3>No matching vehicles found</h3>
            <p>Try loosening your price window or clearing active filters to browse all Bangalore inventory.</p>
            <button class="facet-pill active" onclick="resetAll()">Reset All Filters</button>
          </div>
        `;
        return;
      }

      grid.innerHTML = list.map(c => {
        const isAssured = c.category === 'assured';
        const isCars24 = (c.platform || '').toLowerCase() === 'cars24';
        const tierLabel = isCars24 ? (isAssured ? '✓ Cars24 Assured' : '⚡ Verified Stock') : (isAssured ? '✓ Spinny Assured' : '⚡ Wholesale Stock');
        const platformClass = isCars24 ? 'cars24' : 'spinny';
        const platformName = c.platform || (isCars24 ? 'Cars24' : 'Spinny');

        const price = '₹' + (c.price / 100000).toFixed(2) + 'L';
        const negoPrice = c.negotiable_price ? ('₹' + (c.negotiable_price / 100000).toFixed(2) + 'L') : price;
        const retailPrice = c.orig_retail_price ? ('₹' + (c.orig_retail_price / 100000).toFixed(2) + 'L') : '—';
        const savings = c.negotiable_savings || Math.max(0, c.price - (c.negotiable_price || c.price));
        const savingsFmt = savings >= 100000 ? ('₹' + (savings / 100000).toFixed(2) + 'L') : ('₹' + Math.round(savings / 1000) + 'k');

        const km = (c.mileage / 1000).toFixed(0) + 'k km';
        const title = `${c.make_year} ${c.make} ${c.model} ${c.variant || ''}`.trim();
        const an = c.analysis || {};
        const buyback = '₹' + ((an.est_buyback_2yr || 0) / 100000).toFixed(2) + 'L';
        const monthly = '₹' + Math.round(an.monthly_loss || 0).toLocaleString('en-IN') + ' per mo';

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
              <span class="badge-grade ${gradeClass}">${gradeLabel}</span>
              <span class="badge-tier ${isAssured ? 'assured' : ''}">
                ${tierLabel}
              </span>
              <span class="badge-platform ${platformClass}">
                ${platformName}
              </span>
              ${c.img ? `<img src="${c.img}" alt="${title}" loading="lazy" referrerpolicy="no-referrer" />` : '<span class="caption-5" style="color:var(--text-subtle);">No image preview</span>'}
            </div>

            <div class="card-content">
              <div>
                <h2 class="car-title">${title}</h2>
                <div class="car-tags" style="margin-top:6px;">
                  <span class="spec-tag">${km}</span>
                  <span class="spec-tag">${(c.fuel_type || 'Petrol').toUpperCase()}</span>
                  <span class="spec-tag">${(c.transmission || 'MT').toUpperCase()}</span>
                  <span class="spec-tag" style="color:var(--text-subtle);">${c.hub}</span>
                </div>
              </div>

              <!-- Pricing Intelligence Box -->
              <div class="pricing-box">
                <div class="price-col">
                  <span class="price-label">Listed</span>
                  <span class="price-val">${price}</span>
                </div>
                <div class="price-col">
                  <span class="price-label">Negotiable Target</span>
                  <span class="price-val negotiable">${negoPrice}</span>
                  ${savings > 0 ? `<span class="savings-pill">Save ~${savingsFmt}</span>` : ''}
                </div>
                <div class="price-col">
                  <span class="price-label">Original New</span>
                  <span class="price-val original">${retailPrice}</span>
                  ${c.retail_discount_pct ? `<span class="discount-pill">-${c.retail_discount_pct}%</span>` : ''}
                </div>
              </div>

              <!-- Telemetry Strip -->
              <div class="telemetry-strip">
                <div class="telemetry-col">
                  <span class="telemetry-label">${isAssured ? '24 Month Guaranteed Buyback' : '24 Month Market Resale'}</span>
                  <span class="telemetry-val buyback">${buyback}</span>
                </div>
                <div class="telemetry-col">
                  <span class="telemetry-label">Depreciation Cost</span>
                  <span class="telemetry-val cost">${monthly}</span>
                </div>
              </div>

              <!-- Verdict -->
              <p class="verdict-line">${c.verdict || 'Reliable urban commuter with steady parts availability.'}</p>

              <div class="card-footer">
                <a href="${c.url || '#'}" target="_blank" rel="noopener noreferrer" class="cta-btn">
                  <span>Inspect vehicle on ${platformName}</span>
                  <span>&rarr;</span>
                </a>
              </div>
            </div>
          </article>
        `;
      }).join('');
    }

    // Initial render
    renderAlertsList();
    updateAllMultiFilterUIs();
    applyFilters();
  </script>
</body>
</html>
"""

deals_path = os.path.join(DIR, "deals.html")
with open(deals_path, "w") as f:
    f.write(html_content)

index_path = os.path.join(DIR, "index.html")
shutil.copyfile(deals_path, index_path)

print(f"Redesigned UI successfully generated at {deals_path} and synced to {index_path}")
