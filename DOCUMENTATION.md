# Bangalore Car Radar — Architecture & System Documentation

Autonomous multi-platform used vehicle radar tracking, scoring, and alert pipeline for the Bangalore pre-owned car market across Spinny, Cars24, Truwo, and OLX.

[![Live Dashboard](https://img.shields.io/badge/Live_Radar-kiranpuli.github.io%2Fbangalore--car--radar-f59e0b?style=for-the-badge&logo=google-chrome&logoColor=white)](https://kiranpuli.github.io/bangalore-car-radar/)
[![GitHub Repo](https://img.shields.io/badge/GitHub_Repo-kiranpuli%2Fbangalore--car--radar-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/kiranpuli/bangalore-car-radar)
[![Push Alerts](https://img.shields.io/badge/Push_Alerts-ntfy.sh%2Fkiran--car--radar-0ea5e9?style=for-the-badge&logo=android&logoColor=white)](https://ntfy.sh/kiran-car-radar)
[![License](https://img.shields.io/badge/License-MIT-10b981?style=for-the-badge)](LICENSE)

---

## 🎬 Product Launch Video & Feature Tour

Watch the 18-second product overview showcasing the multi-platform radar sweep, 200-point mechanical telemetry scoring, dedicated transmission facets, and instant mobile push alerts:

[![Bangalore Car Radar Launch Video](product-preview.gif)](product-launch.mp4)

> Rendered using Hyperframes with synchronized music and interface audio cues. [Download high-definition 1080p MP4 (2.8 MB)](product-launch.mp4).

---

## 1. Overview & Market Intelligence

Bangalore Car Radar aggregates and evaluates pre-owned vehicle inventory across all major automotive platforms in Bangalore. It eliminates speculative dealership pricing by computing algorithmic fair-market valuations, running 200-point mechanical audits, and monitoring live listings hourly.

| Metric | Live Count / Frequency | Description |
| :--- | :--- | :--- |
| **Tracked Bangalore Cars** | **1,746** | Live verified inventory across all Bengaluru hubs |
| **Integrated Marketplaces** | **4** | Spinny, Cars24, Truwo, and OLX Bangalore |
| **Sync & Scrape Cadence** | **Hourly (24/7)** | Autonomous background scraping & deal detection |
| **Mechanical Audit Engine** | **200-Point** | Automated analysis of raw inspection sheets |

---

## 2. Supported Marketplace Sources

The monitoring pipeline pulls verified inventory with mechanical inspection sheets and direct vehicle listing URLs:

| Platform | Type | Inspection Guarantee | Hubs Covered |
| :--- | :--- | :--- | :--- |
| **Spinny (594 cars)** | Direct Hub Feeds & APIs | 200-Point Spinny Assured & Max | Whitefield, Yelahanka, Electronic City, Mysore Road |
| **Cars24 (620 cars)** | Search API Endpoints | 140-Point Cars24 Assured Warranty | All Bangalore Mega Hubs & Centers |
| **Truwo (106 cars)** | Curated Hub Inventory | Verified Inspection & Multi-Point Warranty | Bengaluru South & East Hubs |
| **OLX (426 cars)** | Classifieds Scraping | Direct Seller & Verified Certified | Bengaluru Metropolitan Area |

---

## 3. Deal Scoring Algorithm (0 to 100)

Every vehicle receives an objective 0 to 100 conviction score evaluating mechanical integrity, market depreciation, and price positioning:

| Component | Weight | Calculation Basis |
| :--- | :--- | :--- |
| **Price Retention & Depreciation** | **40 Points** | Compares asking price against model-year depreciation curve for Bangalore used car market. |
| **Mechanical Audit Score** | **30 Points** | Analyzes suspension health, tyre tread depth ($\ge$ 4.0 mm), engine bay leaks, coolant condition, battery health, and AC performance. |
| **Mileage & Odometer Integrity** | **15 Points** | Points awarded for verified odometers under 60k km; deductions applied for high cumulative annual mileage (> 15,000 km/year). |
| **Ownership & Bodywork** | **15 Points** | Deductions for structural repainting, panel replacements, minor scratch counts, and third-or-higher owner history. |

### Curated Top Deal Threshold
Cars scoring **$\ge$ 80/100**, priced **$\le$ ₹5.00 Lakh**, and with **$\le$ 80,000 km** are automatically promoted to the **🔥 Top Deals** curated shortlist and dispatched as push notifications.

---

## 4. Ex-Showroom Retail Benchmark & Discount Calculation

Original showroom price (`orig_retail_price`) and savings discount (`retail_discount_pct`) are derived through a 4-tier normalized evaluation pipeline in `estimate_original_retail()`:

| Tier | Mechanism | Formula & Behavior |
| :--- | :--- | :--- |
| **1. Model Baseline Matrix** | 100+ vehicle lines matched by normalized longest-substring priority | Whitespace/hyphen stripped regex match prevents misclassification (e.g. *Grand i10* before *i10*; *BMW X5* before generic *BMW*). |
| **2. Brand-Level Fallback** | Segment anchors for unlisted or sparse trims | Luxury brands anchored accurately (BMW ₹58L, Mercedes ₹65L, Audi ₹52L, Volvo ₹62L, Toyota ₹14.5L). |
| **3. Year & Trim Adjustments** | Dynamic inflation and variant scaling | `base * (1 + (year - 2016) * 0.035) * (+10% top-spec) * (+8% AT)`. |
| **4. Age Depreciation Floor** | Logical floor gate against source payload anomalies | If asking price exceeds model base, enforces `orig_retail = price * max(1.25, 1.0 + age * 0.07)`. Ignores marketplace pre-markdown listing strikes. |

---

## 5. Ergonomic Filter Control Deck & Mobile Architecture

The dashboard provides a responsive, dual-mode filter architecture designed for rapid refinement across both desktop and mobile viewports:

### Mobile Viewport (< 768px): Zero-Overhead Bottom Sheet
On mobile devices, vertical filter forms are eliminated to keep car cards in the first viewport:
- **Sticky Command Bar (40px):** Search input with instant clear, quick sort selector, and dedicated `⚙️ Filters [count]` trigger button.
- **Horizontal Quick-Chip Strip (32px):** Smooth-scrolling, 1-touch facet chips (`🔥 Top Deals`, `⚡ Auto`, `🕹️ Manual`, `≤ ₹5L`, `⛽ Petrol`, `🛢️ Diesel`, `🛡️ German ≤5L`, `🏎️ BMW`, `All Cars`) with real-time inventory counts.
- **Slide-Up Bottom Sheet Drawer:** Tapping `⚙️ Filters` slides up a native-feeling bottom sheet (86vh max-height, backdrop blur, swipe-down handle) housing the full granular control suite, with a sticky bottom `View X Verified Cars →` action bar.
- **Instant Result Visibility:** Cars appear immediately below the quick chip strip—zero screen space wasted.

### Desktop Viewport (≥ 768px): Symmetrical 4-Card Workbench
- **Budget Slider & Number Fields:** Exact numerical input boxes for Minimum and Maximum price in Lakhs (₹ L), paired with a continuous scrub slider from ₹1.0L to ₹15.0L+.
- **Model Year Floor:** Quick segmented pill buttons (`All`, `2016+`, `2018+`, `2020+`, `2022+`) and continuous year slider (2012 to 2024).
- **Showroom Savings %:** Discrete discount percentage selector (`Any`, `20%+`, `35%+`, `50%+`) with 0% to 60%+ range slider.
- **Maximum Mileage Ceiling:** Quick km pills (`Any`, `≤ 40k`, `≤ 60k`, `≤ 80k`, `≤ 100k`) and 20k to 120k km slider.
- **Transmission Panel:** Dedicated gearbox facet panel with live count badges for `All (1,746)`, `⚡ Automatic (805)`, and `🕹️ Manual (941)`.
- **Fuel Type Panel:** Dedicated fuel facet panel with live count badges for `All`, `⛽ Petrol (1,249)`, `🛢️ Diesel (449)`, and `🍃 CNG (12)`.
- **Source Platforms:** Multi-select discrete buttons for Spinny, Cars24, Truwo, and OLX with live count badges.
- **Automaker Chips:** One-click brand chips with live count badges for Maruti, Hyundai, Tata, Honda, Volkswagen, Toyota, Skoda, BMW, Mahindra, Renault, and MG.
- **Model Exclusion (Hide Model):** Permanent model exclusion button on cards and scorecard modals, persisting hidden models in browser `localStorage`.

---

## 6. Mobile & Push Notification Architecture

Pre-owned car deals under ₹5L often receive reservations within 3 hours in Bangalore. The system provides two notification channels:

### Channel A: Mobile Push (ntfy.sh / Samsung S25 Ultra)
Zero signups, open-source notification pipeline via `ntfy.sh/kiran-car-radar`. High-priority push notifications include direct listing links and car photographs, dispatched instantly to Android and iOS devices:

```bash
curl -d "🔥 2018 Honda Jazz Petrol dropped to ₹4.20L at Spinny Whitefield!" \
     -H "Title: Car Deal Radar Alert" \
     -H "Click: https://kiranpuli.github.io/bangalore-car-radar/" \
     https://ntfy.sh/kiran-car-radar
```

### Channel B: PWA (Progressive Web Application)
Configured with web application manifests (`site.webmanifest`, `manifest.json`), high-resolution vector SVG favicon, 192px/512px maskable icons, and `#131209` dark status bar theme color.

---

## 7. Automated Hourly Sync Architecture

The monitoring pipeline runs autonomously on two parallel schedules:

1. **GitHub Actions Workflow:** `.github/workflows/deploy.yml` schedules an hourly runner that executes scrapers, runs mechanical scoring, regenerates `deals.html` and `index.html`, and commits updates to `main`.
2. **Local Cron Daemon:** `hourly_update.sh` runs via macOS `launchd` / `cron` with rebase resilience:
   ```bash
   0 * * * * cd /Users/kiran/workplace/bangalore-car-radar && ./hourly_update.sh >> hourly_sync.log 2>&1
   ```

---

## 8. Local Development & CLI Commands

Run these commands locally to test scrapers, rebuild static UI, or re-render launch media:

### Recompile Dashboard UI
```bash
python3 build_ui.py
```

### Run Live Marketplace Scrapers
```bash
python3 spinny_checker.py --headless
```

### Re-render Product Launch Video (Hyperframes)
```bash
cd brag-output/composition && npx hyperframes check && npx hyperframes render -o ../brag.mp4
```

### Test Dispatch Push Alert
```bash
python3 -c "
import urllib.request
req = urllib.request.Request('https://ntfy.sh/kiran-car-radar', data=b'Test alert from Bangalore Car Radar', headers={'Title': 'Radar Test Alert'})
urllib.request.urlopen(req)
print('Alert dispatched successfully')
"
```
