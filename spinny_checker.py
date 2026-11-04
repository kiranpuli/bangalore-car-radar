#!/usr/bin/env python3
"""
Spinny Bangalore Used Car Deal Monitor & Screener
Crawls full Bangalore inventory with zero artificial price caps.
Enriches listings with deal quality score (0-100), 2-year buyback retention, and maintenance data.
Rebuilds deals.html automatically and dispatches notifications on new finds.
"""

import argparse
import json
import os
import subprocess
import sys
import requests
from datetime import datetime

API_URL = "https://api.spinny.com/v3/api/listing/v7/"

PRESTIGE_MODELS = [
    # German / European
    "polo", "vento", "ameo", "passat", "jetta", "taigun", "virtus", "tiguan", "t-roc", "beetle",
    "rapid", "fabia", "octavia", "superb", "kushaq", "slavia", "laura", "kodiaq", "yeti",
    # Honda
    "city", "amaze", "brio", "jazz", "wr-v", "civic", "cr-v", "elevate", "br-v", "accord",
    # Toyota
    "etios", "glanza", "yaris", "corolla", "camry", "innova", "fortuner", "hyryder", "urban cruiser",
    # Hyundai
    "i20", "elite i20", "verna", "creta", "venue", "xcent", "grand i10", "i10", "aura", "alcazar", "tucson", "elantra",
    # Maruti
    "baleno", "ciaz", "swift", "dzire", "brezza", "vitara brezza", "grand vitara", "scross", "s-cross", "ignis", "a-star", "ritz", "ertiga", "xl6", "fronx", "jimny",
    # Ford
    "ecosport", "figo", "aspire", "freestyle", "endeavour", "fiesta",
    # Tata
    "tiago", "altroz", "tigor", "zest", "nexon", "harrier", "safari", "punch", "hexa", "bolt",
    # Kia
    "seltos", "sonet", "carens", "carnival",
    # Mahindra
    "xuv300", "xuv500", "xuv700", "thar", "scorpio", "kuv100",
    # Others
    "compass", "duster", "terrano", "kiger", "magnite", "triber",
]

EXCLUDE_MODELS = [
    "alto", "eeco", "omni", "s-presso", "spresso",
    "celerio", "wagon r", "eon", "santro", "kwid", "nano", "matiz", "spark",
]

KNOWLEDGE_BASE = {
    "brio": {
        "pros": ["Bulletproof Honda 1.2L i-VTEC engine", "Easiest car to park in tight Bangalore spots", "Zippy 88 bhp with tight turning radius"],
        "cons": ["Stiff rear ride on bad roads/potholes", "Small 175L glass boot", "Basic interior features"],
        "maintenance_yr": "₹4,500 - ₹6,000",
        "retention_pct": 0.72,
    },
    "i10": {
        "pros": ["Feather-light clutch & steering for traffic", "Spares available at every neighborhood garage", "Upright seating with clear visibility"],
        "cons": ["1.1L engine strains on highway inclines", "City fuel economy ~11-12 kmpl with AC", "Dated dashboard styling"],
        "maintenance_yr": "₹4,000 - ₹5,000",
        "retention_pct": 0.71,
    },
    "figo": {
        "pros": ["Tank-like European build quality & safety", "Plush suspension over Bangalore potholes", "Excellent highway high-speed stability"],
        "cons": ["Ford service network is independent/FNG reliant", "Weak low-end torque in 2nd gear traffic", "Slightly heavier clutch"],
        "maintenance_yr": "₹5,500 - ₹7,000",
        "retention_pct": 0.67,
    },
    "amaze": {
        "pros": ["Massive 400L boot for outstation & airport runs", "Spacious rear legroom with great resale demand", "Engine easily lasts 200,000+ km"],
        "cons": ["Soft rear suspension can scrape tall speedbumps", "Lightweight door build compared to Polo", "Basic cabin sound insulation"],
        "maintenance_yr": "₹5,000 - ₹6,500",
        "retention_pct": 0.73,
    },
    "aspire": {
        "pros": ["Top Titanium trim (alloys, fog lamps, audio)", "Solid high-speed road manners & steering feel", "Great crash safety feel"],
        "cons": ["Ford parts take 2-3 days to order", "City mileage around 12-13 kmpl", "Resale market smaller than Maruti/Hyundai"],
        "maintenance_yr": "₹5,500 - ₹7,000",
        "retention_pct": 0.69,
    },
    "grand i10": {
        "pros": ["Ultra-refined 1.2L 4-cylinder engine", "Premium cabin fit and finish", "Very soft clutch and smooth gearbox"],
        "cons": ["Suspension gets floaty above 100 km/h", "Rear AC vents only on top trims", "Average mileage in heavy city jams"],
        "maintenance_yr": "₹4,500 - ₹6,000",
        "retention_pct": 0.74,
    },
    "polo": {
        "pros": ["Unmatched German chassis stability & paint quality", "Heavy doors with thud sound (5-star feel)", "Timeless styling and prestige"],
        "cons": ["Higher parts cost if sensors fail", "Tighter rear legroom", "3-cylinder petrol is vocal at high RPM"],
        "maintenance_yr": "₹7,500 - ₹10,000",
        "retention_pct": 0.75,
    },
    "jazz": {
        "pros": ["Incredible interior space & Magic Seats practicality", "Large glasshouse with zero blind spots", "Honda reliability"],
        "cons": ["Wide body takes care in narrow alleys", "Rubberband CVT (if AT) or tall gearing", "Priced higher than Brio"],
        "maintenance_yr": "₹5,000 - ₹6,500",
        "retention_pct": 0.74,
    },
    "rapid": {
        "pros": ["Executive sedan road presence", "Solid German build & planted highway cruise", "Large 460L boot space"],
        "cons": ["Skoda maintenance & spares cost higher", "Heavy steering at parking speeds", "Requires proactive upkeep"],
        "maintenance_yr": "₹8,500 - ₹12,000",
        "retention_pct": 0.68,
    },
    "swift": {
        "pros": ["Highest resale value in Indian market", "Instant parts availability everywhere", "Fun to drive peppy dynamics"],
        "cons": ["Thinner sheet metal", "Common on roads (less exclusivity)", "Ride is firm over broken tarmac"],
        "maintenance_yr": "₹4,000 - ₹5,500",
        "retention_pct": 0.78,
    },
    "etios": {
        "pros": ["Indestructible Toyota engine & chassis", "Massive 595L boot space", "Plush ride quality over potholes"],
        "cons": ["Basic cab-like dashboard ergonomics", "Plain exterior styling", "Larger turning radius"],
        "maintenance_yr": "₹4,500 - ₹6,000",
        "retention_pct": 0.72,
    },
    "a-star": {
        "pros": ["Super compact - slots into tightest parking spots", "Torque converter AT is smoother than modern AMTs", "Maruti parts cost peanuts"],
        "cons": ["Tight rear legroom", "Small 180L boot", "Outdated interior trim"],
        "maintenance_yr": "₹3,500 - ₹4,500",
        "retention_pct": 0.70,
    },
    "tiago": {
        "pros": ["Solid 4-star Global NCAP crash safety", "Best-in-class 8-speaker Harman sound system", "Thick European sheet metal feel"],
        "cons": ["3-cylinder Revotron engine vibrates at idle", "Tata service center experience varies", "Clutch has slightly long travel"],
        "maintenance_yr": "₹5,000 - ₹6,500",
        "retention_pct": 0.72,
    },
    "city": {
        "pros": ["Legendary 1.5L i-VTEC benchmark performance", "Spacious executive rear legroom", "Superb highway high-speed cruising"],
        "cons": ["Low ground clearance requires caution on tall Bangalore speed bumps", "Thin sheet metal on doors", "Basic sound insulation"],
        "maintenance_yr": "₹6,000 - ₹8,000",
        "retention_pct": 0.75,
    },
    "nexon": {
        "pros": ["5-star Global NCAP crash test rating", "Class-leading 209mm ground clearance for waterlogging", "Plush ride over potholes"],
        "cons": ["Thick A-pillar creates front-right blind spot", "AMT gearbox has noticeable shifts", "Interior panel fit can have minor gaps"],
        "maintenance_yr": "₹6,000 - ₹8,000",
        "retention_pct": 0.76,
    },
    "creta": {
        "pros": ["Unmatched resale demand in India", "Ultra-smooth petrol engine and light city controls", "Feature-loaded cabin"],
        "cons": ["Firm rear ride on sharp ruts", "Brakes have sharp initial bite", "Higher insurance renewal premiums"],
        "maintenance_yr": "₹7,000 - ₹9,500",
        "retention_pct": 0.78,
    },
    "baleno": {
        "pros": ["Extremely frugal 18-20 kmpl fuel economy", "Spacious cabin with wide rear bench", "Cheapest spare parts in segment"],
        "cons": ["Lightweight build quality", "Steering does not self-center eagerly at low speeds", "Thin paint finish"],
        "maintenance_yr": "₹4,000 - ₹5,500",
        "retention_pct": 0.78,
    },
    "ecosport": {
        "pros": ["Heavy tank-like body integrity and solid doors", "Punchy performance with direct steering feel", "High 200mm ground clearance"],
        "cons": ["Stiff low-speed suspension", "Tight rear legroom", "Ford service is independent garage reliant"],
        "maintenance_yr": "₹6,500 - ₹8,500",
        "retention_pct": 0.70,
    },
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "origin": "https://www.spinny.com",
    "platform": "desktop",
}


def get_cache_file(city):
    return os.path.expanduser(f"~/.spinny_cheapest_prestige_{city}.json")


def load_seen_ids(cache_file):
    if os.path.exists(cache_file):
        try:
            with open(cache_file, "r") as f:
                return set(json.load(f))
        except Exception:
            return set()
    return set()


def save_seen_ids(cache_file, seen_ids):
    with open(cache_file, "w") as f:
        json.dump(list(seen_ids), f, indent=2)


def notify_mac(title, message):
    script = f'display notification "{message}" with title "{title}" sound name "Glass"'
    subprocess.run(["osascript", "-e", script], capture_output=True)


def is_good_deal(car):
    price = car.get("price", 9999999)
    score = car.get("deal_score", 0)
    km = car.get("mileage", 999999)
    # High conviction: under 5.0L, deal score 80+, km <= 80k
    if price <= 500000 and score >= 80 and km <= 80000:
        return True
    # Great value: under 4.5L, deal score 75+, km <= 90k
    if price <= 450000 and score >= 75 and km <= 90000:
        return True
    # Rare steal: under 5.5L, score 90+, km <= 50k
    if price <= 550000 and score >= 90 and km <= 50000:
        return True
    return False


def record_alerts(new_good_deals):
    cur_dir = os.path.dirname(os.path.abspath(__file__))
    alerts_file = os.path.join(cur_dir, "latest_alerts.json")
    existing_alerts = []
    if os.path.exists(alerts_file):
        try:
            with open(alerts_file, "r") as f:
                existing_alerts = json.load(f)
        except Exception:
            existing_alerts = []

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    new_entries = []
    for d in new_good_deals:
        new_entries.append({
            "id": d.get("id"),
            "timestamp": now_str,
            "platform": d.get("platform", "Spinny"),
            "make": d.get("make"),
            "model": d.get("model"),
            "variant": d.get("variant"),
            "make_year": d.get("make_year"),
            "price": d.get("price"),
            "negotiable_price": d.get("negotiable_price"),
            "deal_score": d.get("deal_score"),
            "mileage": d.get("mileage"),
            "hub": d.get("hub"),
            "url": d.get("url"),
            "img": d.get("img"),
        })

    seen_ids = set()
    combined = []
    for a in (new_entries + existing_alerts):
        if a.get("id") not in seen_ids:
            seen_ids.add(a.get("id"))
            combined.append(a)

    with open(alerts_file, "w") as f:
        json.dump(combined[:30], f, indent=2)


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

    # Year inflation multiplier relative to 2016 baseline
    year_diff = (year or 2016) - 2016
    multiplier = 1.0 + (year_diff * 0.035)

    v_lower = (variant or "").lower()
    if any(top in v_lower for top in ["zxi", "asta", "alpha", "titanium", "highline", "zx", "vx", "xz", "plus", "o"]):
        multiplier += 0.10

    t_lower = (transmission or "").lower()
    if any(a in t_lower for a in ["auto", "amt", "cvt", "dsg", "at", "dct"]):
        multiplier += 0.08

    return round(base * multiplier / 10000) * 10000


def extract_car_image(c):
    wb = c.get("without_bg_image") or {}
    f = wb.get("file") or {}
    raw = f.get("taburl") or f.get("absurl") or f.get("moburl") or f.get("thumburl") or c.get("showcase_image") or c.get("image")
    if raw:
        if raw.startswith("//"):
            return "https:" + raw
        elif raw.startswith("/"):
            return "https://www.spinny.com" + raw
        return raw
    return None


def is_prestige_car(car):
    make = (car.get("make") or "").lower()
    model = (car.get("model") or "").lower()
    variant = (car.get("variant") or "").lower()
    full_name = f"{make} {model} {variant}".strip()

    if any(ex in full_name for ex in EXCLUDE_MODELS):
        return False

    if any(m in full_name for m in PRESTIGE_MODELS):
        return True

    # If it's a recognised quality manufacturer and not a excluded tin can
    reputable_makes = ["volkswagen", "honda", "toyota", "skoda", "hyundai", "ford", "tata", "kia", "mahindra", "jeep", "renault", "mg"]
    return any(rm in make for rm in reputable_makes)


def enrich_cars(cars):
    cleaned = []
    for c in cars:
        model_name = (c.get("model") or "").lower()
        matched = None
        for k in KNOWLEDGE_BASE:
            if k in model_name:
                matched = KNOWLEDGE_BASE[k]
                break
        if not matched:
            matched = {
                "pros": ["Reliable brand backing with steady resale demand", "Smooth city drivability", "Predictable routine service upkeep"],
                "cons": ["Regular periodic maintenance required"],
                "maintenance_yr": "₹5,500 - ₹7,500",
                "retention_pct": 0.72,
            }

        price = c.get("price", 0)
        km = c.get("mileage", 0)
        year = c.get("make_year", 2012)
        cat = str(c.get("procurement_category", "")).lower()
        cons_cat = str(c.get("consumer_procurement_category", "")).lower()
        is_assured = cat in ["assured", "assured-plus"] or cons_cat in ["assured", "assured-plus"]
        tier = "assured" if is_assured else "auction"

        retention_pct = matched["retention_pct"] if is_assured else round(matched["retention_pct"] * 0.90, 2)
        retention_val = round(price * retention_pct)
        total_loss_2yr = price - retention_val
        monthly_loss = round(total_loss_2yr / 24)

        # Negotiable target price calculation
        cpd = c.get("current_price_data") or {}
        pb2 = c.get("price_breakdown_v2") or {}
        base_p = cpd.get("base_listing_price") or pb2.get("base_listing_price") or pb2.get("discounted_price_without_add_on_and_tax")
        if base_p and 0 < base_p < price:
            negotiable_price = round(base_p)
        else:
            discount_factor = 0.94 if is_assured else 0.91
            negotiable_price = round((price * discount_factor) / 1000) * 1000

        negotiable_savings = max(0, round(price - negotiable_price))

        # Original retail price calculation
        orig_retail = estimate_original_retail(c.get("make"), c.get("model"), c.get("variant"), year, c.get("transmission"))
        if orig_retail <= price:
            orig_retail = round((price * 1.40) / 10000) * 10000
        retail_discount_pct = max(5, min(85, round((1.0 - (price / orig_retail)) * 100)))

        # Objective Deal Quality Scoring (0 - 100)
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

        # Value density bonus (low km relative to age)
        if year >= 2018 and km <= 40000: score += 6

        final_score = min(99, max(40, score))
        if final_score >= 80:
            deal_grade = "TOP DEAL"
        elif final_score >= 68:
            deal_grade = "VALUE PICK"
        else:
            deal_grade = "FAIR"

        pros = matched.get("pros", [])
        verdict = pros[0] if pros else "Dependable commuter with accessible service network."

        cleaned.append({
            "id": c.get("id"),
            "platform": "Spinny",
            "make": c.get("make"),
            "model": c.get("model"),
            "variant": c.get("variant"),
            "make_year": year,
            "mileage": km,
            "price": price,
            "negotiable_price": negotiable_price,
            "negotiable_savings": negotiable_savings,
            "orig_retail_price": orig_retail,
            "retail_discount_pct": retail_discount_pct,
            "fuel_type": c.get("fuel_type"),
            "transmission": c.get("transmission"),
            "category": tier,
            "hub": c.get("hub") or "Bangalore Hub",
            "img": extract_car_image(c),
            "url": f"https://www.spinny.com{c.get('permanent_url', '')}",
            "deal_score": final_score,
            "deal_grade": deal_grade,
            "is_top_deal": final_score >= 68,
            "verdict": verdict,
            "analysis": {
                "pros": matched["pros"],
                "cons": matched["cons"],
                "maintenance_yr": matched["maintenance_yr"],
                "retention_pct": retention_pct,
                "est_buyback_2yr": retention_val,
                "total_loss_2yr": total_loss_2yr,
                "monthly_loss": monthly_loss,
            },
        })
    return cleaned


def fetch_cheapest_cars(city="bangalore", max_price=None, max_pages=48):
    session = requests.Session()
    session.headers.update(HEADERS)
    cars = []

    for page in range(1, max_pages + 1):
        params = {
            "city": city,
            "o": "price",
            "page": page,
        }
        if max_price is not None and max_price > 0:
            params["max_price"] = str(max_price)

        page_results = None
        for attempt in range(3):
            try:
                res = session.get(API_URL, params=params, timeout=18)
                res.raise_for_status()
                page_results = res.json().get("results", [])
                break
            except Exception as e:
                if attempt < 2:
                    import time; time.sleep(2)
                else:
                    print(f"[{datetime.now()}] Error on page {page} after 3 attempts: {e}", file=sys.stderr)
        
        if page_results is None or not page_results:
            break
        cars.extend(page_results)

    filtered = []
    for c in cars:
        # Strictly ignore booked, sold, or on-hold vehicles
        if c.get("booked") is True or c.get("sold") is True or c.get("on_hold") is True or c.get("soft_unpublish") is True:
            continue
        price = c.get("price", 0)
        km = c.get("mileage", 0)
        price_ok = True if (max_price is None or max_price <= 0) else (price <= max_price)
        if price_ok and km <= 140000 and is_prestige_car(c):
            filtered.append(c)

    filtered.sort(key=lambda x: x.get("price", 0))
    return filtered


def fetch_cars24_cars(city_id="4709", max_pages=25, max_price=None):
    url = "https://car-catalog-gateway-in.c24.tech/listing/v1/buy-used-car"
    headers = {
        "Content-Type": "application/json",
        "X_TENANT_ID": "INDIA_CAR_LISTING",
        "SOURCE": "WebApp",
        "x_experiment_id": "f09f1cc0-deca-4583-95cc-e1f55130ad69",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Origin": "https://www.cars24.com",
        "Referer": "https://www.cars24.com/buy-used-cars-bangalore/",
    }
    cars = []
    seen = set()
    search_after = None

    for page in range(1, max_pages + 1):
        payload = {
            "cityId": str(city_id),
            "size": 30,
            "sort": "P",
            "searchFilter": [],
            "filterVersion": 4,
        }
        if search_after:
            payload["searchAfter"] = search_after

        res = None
        for attempt in range(3):
            try:
                r = requests.post(url, headers=headers, json=payload, timeout=12)
                if r.status_code == 200:
                    res = r.json()
                    break
            except Exception:
                import time; time.sleep(1.5)

        if not res:
            break

        items = res.get("content", [])
        if not items:
            break

        for it in items:
            aid = it.get("appointmentId")
            if aid and aid not in seen:
                # Strictly ignore booked, reserved, or unavailable stock
                st = str(it.get("status") or "").upper()
                sub_st = str(it.get("subStatus") or "").upper()
                if st != "AVAILABLE" or (sub_st and sub_st not in ["AVAILABLE", "NONE", "NULL"]):
                    continue
                if it.get("isBooked") is True:
                    continue
                price = it.get("listingPrice", 0)
                km = (it.get("odometer") or {}).get("value", 0)
                price_ok = True if (max_price is None or max_price <= 0) else (price <= max_price)
                if price_ok and km <= 140000:
                    seen.add(aid)
                    cars.append(it)

        page_meta = res.get("page") or {}
        search_after = page_meta.get("searchAfter")
        if not search_after:
            break

    return cars


def enrich_cars24(cars):
    cleaned = []
    for c in cars:
        make = c.get("make") or ""
        model = c.get("model") or ""
        variant = c.get("variant") or ""
        model_name = f"{make} {model} {variant}".lower()

        matched = None
        for k in KNOWLEDGE_BASE:
            if k in model_name:
                matched = KNOWLEDGE_BASE[k]
                break
        if not matched:
            matched = {
                "pros": ["Reliable brand backing with steady resale demand", "Smooth city drivability", "Predictable routine service upkeep"],
                "cons": ["Regular periodic maintenance required"],
                "maintenance_yr": "₹5,500 - ₹7,500",
                "retention_pct": 0.72,
            }

        price = c.get("listingPrice", 0)
        km = (c.get("odometer") or {}).get("value", 0)
        year = c.get("year", 2018)

        bt = str(c.get("businessTag", {})).lower()
        bt2 = str(c.get("businessTagV2", {})).lower()
        is_assured = "assured" in bt or "owned" in bt2 or "gs" in bt2
        tier = "assured" if is_assured else "market"

        retention_pct = matched["retention_pct"] if is_assured else round(matched["retention_pct"] * 0.90, 2)
        retention_val = round(price * retention_pct)
        total_loss_2yr = price - retention_val
        monthly_loss = round(total_loss_2yr / 24)

        discount_factor = 0.94 if is_assured else 0.91
        negotiable_price = round((price * discount_factor) / 1000) * 1000
        negotiable_savings = max(0, round(price - negotiable_price))

        orig_retail = c.get("originalPrice") or estimate_original_retail(make, model, variant, year, (c.get("transmissionType") or {}).get("value"))
        if orig_retail <= price:
            orig_retail = round((price * 1.40) / 10000) * 10000
        retail_discount_pct = max(5, min(85, round((1.0 - (price / orig_retail)) * 100)))

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
        deal_grade = "TOP DEAL" if final_score >= 80 else ("VALUE PICK" if final_score >= 68 else "FAIR")

        pros = matched.get("pros", [])
        verdict = pros[0] if pros else "Dependable commuter with accessible service network."

        d_img = c.get("detailImage") or {}
        img_url = d_img.get("bgRemovedUri") or d_img.get("uri")

        cleaned.append({
            "id": f"c24_{c.get('appointmentId')}",
            "platform": "Cars24",
            "make": make,
            "model": model,
            "variant": variant,
            "make_year": year,
            "mileage": km,
            "price": price,
            "negotiable_price": negotiable_price,
            "negotiable_savings": negotiable_savings,
            "orig_retail_price": orig_retail,
            "retail_discount_pct": retail_discount_pct,
            "fuel_type": c.get("fuelType") or "Petrol",
            "transmission": (c.get("transmissionType") or {}).get("value") or "Manual",
            "category": tier,
            "hub": (c.get("address") or {}).get("locality") or "Cars24 Bangalore Hub",
            "img": img_url,
            "url": f"https://www.cars24.com/{c.get('cdpRelativeUrl', '')}",
            "deal_score": final_score,
            "deal_grade": deal_grade,
            "is_top_deal": final_score >= 68,
            "verdict": verdict,
            "analysis": {
                "pros": matched["pros"],
                "cons": matched["cons"],
                "maintenance_yr": matched["maintenance_yr"],
                "retention_pct": retention_pct,
                "est_buyback_2yr": retention_val,
                "total_loss_2yr": total_loss_2yr,
                "monthly_loss": monthly_loss,
            },
        })
    return cleaned


def update_deals_html(cleaned_cars):
    cur_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(cur_dir, "clean_bangalore_cars.json")

    # Safety check: avoid clobbering large inventory on partial network aborts
    if os.path.exists(json_path) and len(cleaned_cars) < 150:
        try:
            with open(json_path) as fp:
                old = json.load(fp)
            if len(old) > len(cleaned_cars) * 2:
                print(f"[{datetime.now()}] Warning: Fetched {len(cleaned_cars)} cars but existing file has {len(old)}. Skipping overwrite to prevent truncation.", file=sys.stderr)
                return
        except Exception:
            pass

    with open(json_path, "w") as f:
        json.dump(cleaned_cars, f, indent=2)

    try:
        with open("/tmp/clean_bangalore_cars.json", "w") as f:
            json.dump(cleaned_cars, f, indent=2)
    except Exception:
        pass

    script_path = os.path.join(cur_dir, "build_ui.py")
    if os.path.exists(script_path):
        subprocess.run([sys.executable, script_path], capture_output=True)


def run_monitor(city="bangalore", max_price=None):
    cache_file = get_cache_file(city)
    seen_ids = load_seen_ids(cache_file)
    is_initial_run = len(seen_ids) == 0

    print(f"[{datetime.now()}] Fetching Bangalore cars from Spinny API...")
    spinny_matching = fetch_cheapest_cars(city=city, max_price=max_price)
    cleaned_spinny = enrich_cars(spinny_matching)
    print(f"[{datetime.now()}] Fetched {len(cleaned_spinny)} Spinny cars.")

    print(f"[{datetime.now()}] Fetching Bangalore cars from Cars24 API (REA reverse-engineered)...")
    cars24_raw = fetch_cars24_cars(city_id="4709", max_pages=25, max_price=max_price)
    cleaned_cars24 = enrich_cars24(cars24_raw)
    print(f"[{datetime.now()}] Fetched {len(cleaned_cars24)} Cars24 cars.")

    combined_cars = cleaned_spinny + cleaned_cars24
    combined_cars.sort(key=lambda x: x.get("deal_score", 0), reverse=True)

    new_cars = []
    for car in combined_cars:
        car_id = car.get("id")
        if car_id not in seen_ids:
            new_cars.append(car)
            seen_ids.add(car_id)

    save_seen_ids(cache_file, seen_ids)

    # Rebuild deals.html with live combined data
    update_deals_html(combined_cars)

    price_label = f"<= ₹{max_price//100000}L" if (max_price and max_price > 0) else "All Budgets"
    print(f"[{datetime.now()}] === Bangalore Combined Deals Screener ({price_label}) — Found {len(combined_cars)} Cars ({len(cleaned_spinny)} Spinny + {len(cleaned_cars24)} Cars24) ===")
    for idx, car in enumerate(combined_cars[:5], 1):
        title = f"{car.get('make_year')} {car.get('make')} {car.get('model')} {car.get('variant')}"
        price = f"₹{int(car.get('price', 0)):,}"
        km = f"{car.get('mileage', 0):,} km"
        url = car.get('url', '')
        print(f"{idx}. {title} | {price} | {km}\n   {url}")

    good_deals = [c for c in new_cars if is_good_deal(c)]
    if good_deals:
        record_alerts(good_deals)
        for d in good_deals[:3]:
            title = f"{d.get('make_year')} {d.get('make')} {d.get('model')} {d.get('variant') or ''}".strip()
            price_l = f"₹{d.get('price')/100000:.2f}L"
            km_k = f"{d.get('mileage')//1000}k km"
            plat = d.get('platform', 'Spinny')
            notify_mac(f"🔥 Top {plat} Deal Alert!", f"{title} for {price_l} ({km_k}, Score {d.get('deal_score')})")
        print(f"[{datetime.now()}] Alert dispatched for {len(good_deals)} high-conviction deal(s).")
    elif not is_initial_run:
        print(f"[{datetime.now()}] Inventory refreshed. No new qualifying top deals (< ₹5L, Score 80+).")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bangalore Used Car Deals Screener & Monitor")
    parser.add_argument("--city", default="bangalore", help="Target city")
    parser.add_argument("--max-price", type=int, default=0, help="Max budget threshold (0 for unlimited)")
    parser.add_argument("--test-notify", action="store_true", help="Dispatch a test macOS notification")
    args = parser.parse_args()

    if args.test_notify:
        notify_mac("🔥 Top Deal Alert (Test)!", "2022 Renault Kwid RXT 1.0 AMT for ₹4.26L (Score 99, 14k km)")
        print(f"[{datetime.now()}] Test macOS desktop notification dispatched successfully.")
        sys.exit(0)

    max_p = None if args.max_price <= 0 else args.max_price
    run_monitor(city=args.city, max_price=max_p)
