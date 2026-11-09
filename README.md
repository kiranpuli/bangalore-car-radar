<div align="center">

# 🏎️ Bangalore Car Radar

### **Stop Overpaying Dealerships ₹1,50,000 for Used Cars in Bangalore.**

[![Status: Live](https://img.shields.io/badge/Status-Live%20Radar%20Active-10B981?style=for-the-badge&logo=radar&logoColor=white)](https://kiranpuli.github.io/spinny-deals/)
[![Coverage](https://img.shields.io/badge/Coverage-1%2C784%20Bangalore%20Cars-3B82F6?style=for-the-badge)](https://kiranpuli.github.io/spinny-deals/)
[![Alerts](https://img.shields.io/badge/Alerts-Instant%20Mobile%20Push-F59E0B?style=for-the-badge&logo=google-cloud&logoColor=white)](https://ntfy.sh/kiran-car-radar)
[![Audit](https://img.shields.io/badge/Audit-200--Point%20Telemetry-8B5CF6?style=for-the-badge)](documentation.html)

*The autonomous multi-platform intelligence feed that analyzes 200-point inspection sheets, scores deals on an algorithmic conviction index, and pings your phone before dealers flip them.*

[**🚀 Open Free Live Radar**](https://kiranpuli.github.io/spinny-deals/) &nbsp;•&nbsp; [**📲 Get Mobile Push Alerts**](https://ntfy.sh/kiran-car-radar) &nbsp;•&nbsp; [**📖 Technical Documentation**](documentation.html) &nbsp;•&nbsp; [**🎬 1080p Launch Video**](product-launch.mp4)

<br/>

[![Bangalore Car Radar Product Launch Preview](product-preview.gif)](https://kiranpuli.github.io/spinny-deals/)

<sub>🎬 18-second product overview showing real-time radar sweep, 200-point telemetry, transmission facets, and push alerts. <a href="product-launch.mp4">Download high-definition MP4 with audio</a>.</sub>

</div>

---

## ⚡ Why Bangalore Car Radar?

| Traditional Used Car Hunting | Bangalore Car Radar |
| :--- | :--- |
| ❌ Manually browsing 4 different apps (Spinny, Cars24, Truwo, OLX) every day | ✅ **1,780+ live Bangalore vehicles unified into one high-speed dashboard** |
| ❌ Dealing with dealership markups of ₹1,00,000 to ₹1,50,000 | ✅ **Fair-value depreciation curves spotlighting true bargains under ₹5 Lakhs** |
| ❌ Hidden tyre wear, suspension issues, and engine leaks discovered after booking | ✅ **200-Point mechanical telemetry scored (0 to 100) before you travel to the hub** |
| ❌ Sifting through unwanted car models repeatedly | ✅ **1-Click "⊘ Hide Model" button removes unwanted models permanently from your view** |
| ❌ Missing under-priced deals because someone else saw them first | ✅ **Zero-setup push notifications straight to your Samsung S25 Ultra or iPhone** |

---

## 🎯 5 Reasons Buyers Use Bangalore Car Radar

### 1. Four Major Marketplaces in One Radar
Stop jumping between tabs. Every hour, our scrapers sync live pre-owned inventories across all Bangalore hubs:
- **Spinny (740+ cars):** Whitefield, Yelahanka, Electronic City, and Mysore Road hubs.
- **Cars24 (620+ cars):** All Bangalore Assured inspection centers.
- **Truwo (210+ cars):** Verified direct hub inventory across Bengaluru South & East.
- **OLX (210+ cars):** Curated and verified direct seller listings.

### 2. 200-Point Mechanical Telemetry Audit
We extract raw inspection data so you never waste time visiting a showroom for a defective vehicle:
- **Tyre Health:** Exact tread depth measurements (≥ 4.0 mm required for green badge).
- **Suspension & Struts:** Leak detection and damping efficiency ratings.
- **Engine & ECU:** Scan results, smoke analysis, gasket inspection, and fluid checks.
- **Electrical & AC:** Battery health voltage, starter motor test, and cabin cooling speed.

### 3. Algorithmic Deal Conviction Scoring (0 to 100)
Our valuation algorithm scores every car based on Bangalore market retention curves:
- **40 Points — Depreciation Curve:** Price vs. original showroom cost and year-over-year retention.
- **30 Points — Mechanical Sheet:** Direct rating from tyre, suspension, and engine checklists.
- **15 Points — Mileage Verification:** Target ≤ 80,000 km with verified service history.
- **15 Points — Ownership Profile:** Single-owner bonus and clean body panels.

> **Curated Threshold:** Cars scoring 80+ priced under ₹5.00 Lakhs are automatically badged with **🔥 Top Deal**.

### 4. Laser-Targeted Transmission, Fuel & Year Filters
Filter 1,780+ cars in under 100 milliseconds with dedicated facet decks:
- **Dedicated Transmission Panel:** Real-time count badges for `All (1,784)`, `⚡ Automatic (837)`, and `🕹️ Manual (947)`.
- **Fuel Type Selector:** `All`, `⛽ Petrol (1,280+)`, `🛢️ Diesel (450+)`, and `🍃 CNG (40+)`.
- **Model Year Pills:** 1-Click jumps for `All`, `2016+`, `2018+`, `2020+`, and `2022+` plus continuous slider.
- **Custom Model Exclusion:** Hit **⊘ Hide Model** on any car card to hide that model across all platforms instantly (saved to device `localStorage`).

### 5. Instant Zero-Setup Phone Push Notifications
Get alerted the exact minute a price drop or new high-conviction deal appears. Built for Samsung S25 Ultra, Android, and iOS:

```bash
# Test sending a push notification right from your terminal:
curl -d "🔥 2018 Honda Jazz Petrol dropped to ₹4.20L at Spinny Whitefield!" \
     -H "Title: Car Deal Radar Alert" \
     -H "Click: https://kiranpuli.github.io/spinny-deals/" \
     https://ntfy.sh/kiran-car-radar
```

---

## ⚙️ Hourly Sync Architecture
The system operates autonomously 24 hours a day, 7 days a week:
1. **Hourly GitHub Action:** Automated cron executes scrapers headless, pulls fresh listings, recalculates conviction scores, updates the database, and commits changes.
2. **Local Background Sync:** `hourly_update.sh` runs alongside with git rebase resilience and error logging.
3. **Instant Static UI Build:** `build_ui.py` renders the complete interactive dashboard directly into standalone `index.html` with zero external runtime dependencies.

---

## 💻 Developer CLI Commands

```bash
# 1. Rebuild Static Dashboard
python3 build_ui.py

# 2. Run Headless Scrapers
python3 spinny_checker.py --headless

# 3. Start Local Development Server
python3 server.py 8000

# 4. Re-render Product Launch Video (Hyperframes)
cd brag-output/composition && npx hyperframes check && npx hyperframes render -o ../brag.mp4
```

---

<div align="center">

### Ready to find your car?

[**👉 Launch Bangalore Car Radar (Free)**](https://kiranpuli.github.io/spinny-deals/)

<sub>Maintained by [Kiran Puli](https://github.com/kiranpuli) • Standalone documentation at [documentation.html](documentation.html) • Push Channel: [ntfy.sh/kiran-car-radar](https://ntfy.sh/kiran-car-radar)</sub>

</div>
