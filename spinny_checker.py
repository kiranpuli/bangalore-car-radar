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
import re
import subprocess
import sys
import requests
from datetime import datetime

API_URL = "https://api.spinny.com/v3/api/listing/v7/"

PRESTIGE_MODELS = [
    # German / European
    "polo", "vento", "ameo", "passat", "jetta", "taigun", "virtus", "tiguan", "t-roc", "beetle",
    "rapid", "fabia", "octavia", "superb", "kushaq", "slavia", "laura", "kodiaq", "yeti",
    # Luxury European
    "x1", "x3", "x5", "3 series", "5 series", "c-class", "e-class", "gla", "glc", "a4", "a6", "q3", "q5", "xf", "f-pace", "xc40", "xc60",
    # MG
    "astor", "hector", "gloster", "zs ev", "comet",
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
    "xuv300", "xuv500", "xuv700", "thar", "scorpio", "kuv100", "xev 9e", "be 6e", "xuv400",
    # Others
    "compass", "duster", "terrano", "kiger", "magnite", "triber",
]

EXCLUDE_MODELS = [
    "alto", "eeco", "omni", "s-presso", "spresso", "s presso", "presso",
    "celerio", "wagon r", "wagonr", "wagon", "eon", "santro", "kwid", "nano", "matiz", "spark",
    "datsun", "redi-go", "redigo", "kuv100", "kuv 100", "zen estilo", "estilo", "ritz",
]

def is_excluded_car(car):
    make = (car.get("make") or "").lower()
    model = (car.get("model") or "").lower()
    variant = (car.get("variant") or "").lower()
    full_name = f"{make} {model} {variant}".strip()
    return any(ex in full_name for ex in EXCLUDE_MODELS)

KNOWLEDGE_BASE = {
    "wagon r": {
        "pros": ["Tall-boy easy ingress and egress for all ages", "Superb city fuel economy 16+ kmpl with AC", "Spacious rear legroom with high market resale demand"],
        "cons": ["Body roll around sharp highway turns", "Light sheet metal feel"],
        "maintenance_yr": "₹3,500 - ₹4,500",
        "retention_pct": 0.76,
    },
    "wagonr": {
        "pros": ["Tall-boy easy ingress and egress for all ages", "Superb city fuel economy 16+ kmpl with AC", "Spacious rear legroom with high market resale demand"],
        "cons": ["Body roll around sharp highway turns", "Light sheet metal feel"],
        "maintenance_yr": "₹3,500 - ₹4,500",
        "retention_pct": 0.76,
    },
    "celerio": {
        "pros": ["Compact footprint and very economical K10C engine", "Effortless parking and steering in Bangalore traffic", "Pocket-friendly maintenance and cheap spares"],
        "cons": ["Lightweight build", "Basic highway overtaking punch"],
        "maintenance_yr": "₹3,500 - ₹4,500",
        "retention_pct": 0.75,
    },
    "alto": {
        "pros": ["Zero maintenance headaches with ubiquitous neighborhood spares", "Outstanding 17+ kmpl city fuel efficiency", "Ideal low-cost entry hatchback for city commuting"],
        "cons": ["Compact rear seat and boot", "Minimal safety equipment on older trims"],
        "maintenance_yr": "₹3,000 - ₹4,000",
        "retention_pct": 0.74,
    },
    "kwid": {
        "pros": ["SUV-inspired styling with high 184mm ground clearance", "Impressive 279L boot space for its segment", "Modern touchscreen infotainment on RXT trims"],
        "cons": ["3-cylinder engine vibration at idle", "AMT shift pauses in bumper-to-bumper jams"],
        "maintenance_yr": "₹4,000 - ₹5,000",
        "retention_pct": 0.70,
    },
    "s-presso": {
        "pros": ["High seating position with panoramic forward visibility", "High 180mm ground clearance for huge speedbumps", "Peculiarly roomy cabin for 4 adults"],
        "cons": ["Unconventional central speedometer styling", "Light highway stability in crosswinds"],
        "maintenance_yr": "₹3,500 - ₹4,500",
        "retention_pct": 0.72,
    },
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
    # Luxury European (BMW, Mercedes, Audi)
    "bmw 3 series": {
        "pros": ["Iconic 50:50 weight distribution & pure rear-wheel drive dynamics", "Refined 2.0L TwinPower turbo with slick ZF 8-speed automatic", "Timeless German sports sedan pedigree with huge enthusiast community"],
        "cons": ["Run-flat tyres deliver firm ride over sharp Bangalore potholes", "Dealership servicing carries luxury premium (independent European specialists advised)", "Inspect cooling system, oil filter housing & ABS sensors above 60k km"],
        "maintenance_yr": "₹25,000 - ₹38,000",
        "retention_pct": 0.68,
    },
    "bmw 5 series": {
        "pros": ["Executive luxury cabin with whisper-quiet high-speed acoustic insulation", "Monumental 3.0L / 2.0L diesel torque for effortless highway cruising", "Flagship road presence and exceptional highway stability"],
        "cons": ["Long 4.9m footprint needs extra care in central Bangalore alleys", "Higher maintenance costs (air suspension, brake discs, sensor calibrations)", "Annual insurance and 18-inch tyre replacements carry higher costs"],
        "maintenance_yr": "₹35,000 - ₹55,000",
        "retention_pct": 0.64,
    },
    "bmw x1": {
        "pros": ["Generous 180mm ground clearance easily clears notorious Bangalore speedbreakers", "Compact luxury SUV dimensions with commanding high seating & visibility", "Spacious 505L cargo volume and flexible split-folding rear seats"],
        "cons": ["Stiff suspension setup communicates expansion joints and road ripples", "Front-wheel drive architecture (UKL) on modern models lacks classic RWD drift", "Synthetic engine oil and premium brake pads require strict upkeep"],
        "maintenance_yr": "₹22,000 - ₹34,000",
        "retention_pct": 0.70,
    },
    "bmw x3": {
        "pros": ["Intelligent xDrive all-wheel drive ensures unshakable wet monsoon grip", "Substantial cabin room with panoramic glass roof and executive rear comfort", "Punchy powertrain and 5-star Euro NCAP active safety architecture"],
        "cons": ["Transfer case and differential fluid servicing required at higher mileage", "City fuel efficiency drops to 8-10 kmpl in peak Bengaluru congestion", "Replacement run-flat tyres are costly"],
        "maintenance_yr": "₹30,000 - ₹48,000",
        "retention_pct": 0.67,
    },
    "bmw": {
        "pros": ["Prestigious German badge and driver-focused mechanical precision", "Substantial depreciation arbitrage — pre-owned at a fraction of on-road price", "Strong network of Bangalore European specialist independent garages"],
        "cons": ["Mandatory pre-purchase OBD-II electronic diagnostic and hoist inspection", "Higher routine consumables and insurance expense than Japanese/Korean cars"],
        "maintenance_yr": "₹25,000 - ₹42,000",
        "retention_pct": 0.66,
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
    try:
        import platform, shutil
        if platform.system() != "Darwin" or not shutil.which("osascript"):
            return
        clean_msg = message.replace('"', '\\"')
        clean_title = title.replace('"', '\\"')
        script = f'display notification "{clean_msg}" with title "{clean_title}" sound name "Glass"'
        subprocess.run(["osascript", "-e", script], capture_output=True)
    except Exception:
        pass


NTFY_TOPIC = os.environ.get("NTFY_TOPIC", "kiran-car-radar")

def send_mobile_push(title, message, click_url=None, topic=NTFY_TOPIC):
    try:
        headers = {
            "Title": title,
            "Tags": "car,fire",
            "Priority": "high"
        }
        if click_url:
            headers["Click"] = click_url
        res = requests.post(
            f"https://ntfy.sh/{topic}",
            data=message.encode("utf-8"),
            headers=headers,
            timeout=8
        )
        if res.status_code == 200:
            print(f"[{datetime.now()}] Mobile push dispatched to ntfy.sh/{topic}")
    except Exception as e:
        print(f"[{datetime.now()}] Push notification error: {e}", file=sys.stderr)


def is_good_deal(car):
    if is_excluded_car(car):
        return False
    price = car.get("price", 9999999)
    score = car.get("deal_score", 0)
    km = car.get("mileage", 999999)
    # High conviction: under 4.0L, deal score 80+, km <= 80k
    if price <= 400000 and score >= 80 and km <= 80000:
        return True
    # Great value: under 3.5L, deal score 75+, km <= 90k
    if price <= 350000 and score >= 75 and km <= 90000:
        return True
    # Rare steal: under 4.5L, score 90+, km <= 50k
    if price <= 450000 and score >= 90 and km <= 50000:
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
            "retail_discount_pct": d.get("retail_discount_pct"),
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
    # Maruti Suzuki
    "alto": 380000, "alto k10": 440000, "a-star": 440000, "astar": 440000, "wagon r": 540000, "celerio": 560000,
    "ignis": 680000, "swift": 740000, "dzire": 780000, "swift dzire": 760000, "baleno": 820000,
    "fronx": 980000, "brezza": 1080000, "vitara brezza": 1020000, "grand vitara": 1420000, "jimny": 1380000,
    "scross": 1080000, "s-cross": 1080000, "s cross": 1080000, "ciaz": 1150000, "ertiga": 1120000, "xl6": 1320000,
    "ritz": 580000, "eeco": 540000, "invicto": 2850000, "esteem": 480000,
    # Hyundai
    "eon": 390000, "santro": 520000, "i10": 540000, "grand i10": 720000, "grand i10 nios": 740000, "aura": 820000,
    "xcent": 760000, "i20": 880000, "elite i20": 890000, "i20 active": 940000, "exter": 840000, "venue": 1080000,
    "verna": 1380000, "creta": 1540000, "alcazar": 2050000, "tucson": 3100000, "elantra": 1950000, "getz": 450000,
    # Honda
    "brio": 590000, "amaze": 840000, "jazz": 900000, "wr-v": 1080000, "city": 1420000, "br-v": 1180000, "mobilio": 940000,
    "civic": 2250000, "cr-v": 3200000, "elevate": 1420000,
    # Volkswagen & Skoda
    "polo": 860000, "ameo": 800000, "vento": 1250000, "virtus": 1480000, "taigun": 1580000, "tiguan": 3600000,
    "rapid": 1220000, "slavia": 1450000, "kushaq": 1550000, "kodiaq": 3900000, "octavia": 2850000, "superb": 3600000, "fabia": 620000,
    # Tata
    "nano": 240000, "tiago": 650000, "tigor": 760000, "zest": 780000, "bolt": 690000,
    "altroz": 880000, "punch": 840000, "curvv": 1550000, "nexon": 1150000, "harrier": 2050000, "safari": 2280000, "hexa": 1650000, "sierra": 1600000,
    # Ford
    "figo": 680000, "aspire": 800000, "freestyle": 840000, "fiesta": 880000, "ecosport": 1120000, "endeavour": 3600000,
    # Toyota
    "etios liva": 690000, "etios": 820000, "glanza": 840000, "yaris": 1180000, "rumion": 1180000,
    "urban cruiser": 1150000, "hyryder": 1580000, "urban cruiser hyryder": 1580000, "taisor": 1050000,
    "corolla": 1780000, "corolla altis": 1920000, "camry": 4400000, "innova": 2150000, "innova crysta": 2550000, "innova hycross": 2850000,
    "fortuner": 4100000, "qualis": 550000,
    # Renault & Nissan
    "kwid": 490000, "triber": 780000, "kiger": 840000, "captur": 1250000, "lodgy": 1080000, "duster": 1220000,
    "magnite": 840000, "micra": 640000, "micra active": 580000, "kicks": 1280000, "terrano": 1220000, "sunny": 920000,
    # Kia
    "sonet": 1150000, "seltos": 1580000, "carens": 1420000, "syros": 1250000, "carnival": 3400000, "ev6": 6500000,
    # Mahindra
    "kuv100": 740000, "xuv300": 1180000, "xuv 300": 1180000, "xuv 3xo": 1180000, "3xo": 1180000, "xuv400": 1850000,
    "thar": 1520000, "scorpio": 1620000, "scorpio n": 1850000, "scorpio classic": 1550000, "xuv500": 1780000, "xuv700": 2250000,
    "bolero": 980000, "bolero neo": 1020000, "bolero neo plus": 1150000, "tuv300": 980000, "tuv 300": 980000, "verito": 720000, "xev": 2900000,
    # Jeep
    "compass": 2450000, "meridian": 3400000, "wrangler": 6800000,
    # MG
    "astor": 1420000, "hector": 1820000, "hector plus": 1950000, "gloster": 3950000, "zs ev": 2350000, "comet": 820000,
    # BMW
    "bmw 2 series": 4600000, "2 series": 4600000, "2 series gran coupe": 4600000,
    "bmw 3 series": 5200000, "3 series": 5200000, "320d": 5200000, "330i": 5600000, "m340i": 7400000,
    "bmw 5 series": 7200000, "5 series": 7200000, "520d": 7200000, "530d": 7800000,
    "bmw 6 series": 7800000, "6 series": 7800000, "6 series gt": 7800000,
    "bmw 7 series": 14500000, "7 series": 14500000,
    "bmw x1": 4900000, "x1": 4900000, "ix1": 6800000,
    "bmw x3": 6900000, "x3": 6900000, "ix3": 8200000,
    "bmw x4": 7800000, "x4": 7800000,
    "bmw x5": 10200000, "x5": 10200000,
    "bmw x7": 12800000, "x7": 12800000,
    "bmw ix": 12200000, "ix": 12200000,
    "bmw z4": 9200000, "z4": 9200000,
    # Mercedes-Benz
    "a-class": 4600000, "a class": 4600000, "c-class": 5800000, "c class": 5800000,
    "e-class": 7800000, "e class": 7800000, "s-class": 17500000, "s class": 17500000,
    "gla": 5100000, "glb": 6500000, "glc": 7400000, "gle": 9800000, "gls": 13500000,
    "eqb": 7600000, "eqs": 16500000,
    # Audi
    "a3": 3600000, "a4": 4900000, "a6": 6800000, "a8": 13500000,
    "q2": 3900000, "q3": 4700000, "q5": 6900000, "q7": 8900000, "q8": 11500000,
    # Land Rover & Jaguar
    "defender": 9800000, "discovery": 9200000, "discovery sport": 7200000,
    "range rover evoque": 7200000, "evoque": 7200000,
    "range rover velar": 8900000, "velar": 8900000,
    "range rover sport": 16500000, "range rover": 24000000,
    "xf": 7500000, "xe": 5200000, "f-pace": 7800000,
    # Volvo & Porsche & Luxury
    "xc40": 4800000, "xc60": 7100000, "xc90": 10200000, "s60": 4800000, "s90": 7200000,
    "cayenne": 14200000, "macan": 9200000, "panamera": 16500000, "gallardo": 28000000,
    "countryman": 4600000, "cooper": 4200000,
    # Others
    "beat": 450000, "sail": 620000, "sail uva": 580000, "avventura": 780000, "linea": 920000,
    "atto 3": 3400000, "c3": 690000
}

BRAND_BASE_FALLBACK = {
    "lamborghini": 32000000, "ferrari": 45000000, "porsche": 13500000,
    "land rover": 8500000, "range rover": 12000000, "jaguar": 7500000,
    "mercedes-benz": 6500000, "mercedes": 6500000,
    "bmw": 5800000, "audi": 5200000, "volvo": 6200000, "mini": 4200000, "lexus": 7200000,
    "jeep": 2800000, "byd": 3200000,
    "toyota": 1450000, "mahindra": 1350000, "mg": 1550000, "mg motor": 1550000,
    "kia": 1350000, "volkswagen": 1250000, "skoda": 1250000,
    "hyundai": 1050000, "honda": 1150000, "tata": 1050000,
    "ford": 1050000, "renault": 850000, "nissan": 850000,
    "maruti suzuki": 780000, "maruti": 780000, "fiat": 750000, "chevrolet": 650000
}

def _clean_str(s):
    import re
    return re.sub(r"[\s\-_]+", "", (s or "").lower())

_SORTED_MODEL_ITEMS = sorted(MODEL_NEW_RETAIL_BASE.items(), key=lambda x: len(x[0]), reverse=True)


def estimate_original_retail(make, model, variant, year, transmission):
    full_str = f"{make} {model} {variant or ''}".lower()
    full_clean = _clean_str(full_str)
    
    base = None
    for k, v in _SORTED_MODEL_ITEMS:
        if _clean_str(k) in full_clean:
            base = v
            break

    if not base:
        m_clean = (make or "").lower().strip()
        for bk, bv in BRAND_BASE_FALLBACK.items():
            if bk in m_clean or m_clean in bk:
                base = bv
                break
        if not base:
            base = 820000

    year_diff = (year or 2016) - 2016
    multiplier = 1.0 + (year_diff * 0.035)

    v_lower = (variant or "").lower()
    if any(top in v_lower for top in ["zxi", "asta", "alpha", "titanium", "highline", "zx", "vx", "xz", "plus", "o", "tech", "luxury", "gt"]):
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
    reputable_makes = [
        "volkswagen", "honda", "toyota", "skoda", "hyundai", "ford", "tata", "kia", "mahindra",
        "jeep", "renault", "mg", "bmw", "mercedes", "mercedes-benz", "audi", "jaguar", "volvo", "land rover", "mini"
    ]
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


def call_api_anything(site, op, timeout=15, **kwargs):
    """Query an API operation via api-anything over plain HTTP."""
    try:
        cmd = ["npx", "-y", "api-anything", "call", site, op]
        for k, v in kwargs.items():
            if v is not None:
                cmd.append(f"{k}={v}")
        out = subprocess.check_output(cmd, text=True, timeout=timeout)
        res = json.loads(out)
        if res.get("ok"):
            return res.get("data", [])
    except Exception as e:
        print(f"[{datetime.now()}] api-anything {site} {op} fallback: {e}", file=sys.stderr)
    return None

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
        if price_ok and km <= 250000:
            filtered.append(c)

    filtered.sort(key=lambda x: x.get("price", 0))
    return filtered


def fetch_cars24_cars(city_id="4709", max_pages=80, max_price=None):
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
                if price_ok and km <= 250000:
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

        orig_retail = estimate_original_retail(make, model, variant, year, (c.get("transmissionType") or {}).get("value"))
        if orig_retail <= price:
            age = max(1, 2026 - year)
            orig_retail = round((price * max(1.25, 1.0 + (age * 0.07))) / 10000) * 10000
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
        l_img = c.get("listingImage") or {}
        candidates = [
            d_img.get("bgRemovedUri"),
            d_img.get("uri"),
            l_img.get("bgRemovedUri"),
            l_img.get("uri")
        ]
        img_url = None
        for cand in candidates:
            if cand and isinstance(cand, str):
                c_clean = cand.strip()
                if "UPCOMING_CAR" in c_clean or "comindia" in c_clean:
                    continue
                if c_clean.startswith("http"):
                    img_url = c_clean
                    break

        cleaned.append({
            "id": f"c24_{c.get('appointmentId')}",
            "platform": "Cars24",
            "make": make,
            "model": model,
            "variant": variant,
            "make_year": year,
            "mileage": km,
            "price": price,
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


def fetch_truwo_cars(max_price=None):
    # 1. Primary: query via api-anything learned operation (ultra-fast, tier-1 plain HTTP)
    data = call_api_anything("truwo", "listings", timeout=12, **{"--max-chars": "100000"})
    if data and isinstance(data, list) and len(data) > 0:
        filtered = []
        for item in data:
            price = item.get("price") or 0
            price_ok = True if (max_price is None or max_price <= 0) else (price <= max_price)
            if price_ok:
                filtered.append({
                    "name": item.get("name", ""),
                    "truwo_price": price,
                    "listed_price": price,
                    "url": item.get("url", ""),
                    "image": item.get("image", ""),
                    "source_format": "schema_org"
                })
        return filtered

    # 2. Fallback: Direct HTML requests & Next.js RSC parse
    url = "https://www.truwo.ai/listings"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    html = ""
    try:
        from scrapling.fetchers import Fetcher
        res = Fetcher.get(url, headers=headers, timeout=15)
        html = res.html_content or (res.body.decode("utf-8", errors="ignore") if hasattr(res, "body") else "")
    except Exception:
        pass

    if not html:
        try:
            r = requests.get(url, headers=headers, timeout=15)
            r.raise_for_status()
            html = r.text
        except Exception as e:
            print(f"[{datetime.now()}] Error fetching Truwo listings: {e}", file=sys.stderr)
            return []

    cars = []
    # Try Schema.org ItemList in script tags
    try:
        scripts = re.findall(r'<script type=["\']application/ld\+json["\']>(.*?)</script>', html, re.DOTALL)
        for s in scripts:
            if '"@type":"ItemList"' in s:
                d = json.loads(s)
                for it in d.get("itemListElement", []):
                    item = it.get("item", {})
                    if item:
                        price = (item.get("offers") or {}).get("price", 0)
                        cars.append({
                            "name": item.get("name", ""),
                            "truwo_price": price,
                            "listed_price": price,
                            "url": item.get("url", ""),
                            "image": item.get("image", ""),
                            "source_format": "schema_org"
                        })
                break
    except Exception:
        pass

    # Try Next.js RSC chunks
    if not cars:
        try:
            chunks = re.findall(r'self\.__next_f\.push\(\[1,\s*\"(.*?)\"\]\)', html)
            for c in chunks:
                try:
                    unescaped = c.encode('utf-8').decode('unicode_escape')
                except Exception:
                    unescaped = c
                if '\"items\":[' in unescaped:
                    idx = unescaped.find('\"items\":[') + 8
                    arr, _ = json.JSONDecoder().raw_decode(unescaped[idx:])
                    cars = arr
                    break
        except Exception as e:
            print(f"[{datetime.now()}] Error parsing Truwo listings: {e}", file=sys.stderr)

    filtered = []
    for c in cars:
        if c.get("sold") is True:
            continue
        price = c.get("truwo_price") or c.get("listed_price") or 0
        km = c.get("kms_driven", 0)
        price_ok = True if (max_price is None or max_price <= 0) else (price <= max_price)
        if price_ok and km <= 140000:
            filtered.append(c)

    return filtered


def enrich_truwo(cars):
    cleaned = []
    for c in cars:
        make = c.get("make") or ""
        model = c.get("model") or ""
        variant = c.get("variant") or ""
        year = c.get("year", 2020)

        # Parse schema_org title if make not separated
        raw_name = c.get("name") or ""
        if not make and raw_name:
            parts = raw_name.split(" ")
            if parts and parts[0].isdigit() and len(parts[0]) == 4:
                year = int(parts[0])
                make = parts[1] if len(parts) > 1 else ""
                model = parts[2] if len(parts) > 2 else ""
                variant = " ".join(parts[3:]) if len(parts) > 3 else ""

        model_name = f"{make} {model} {variant}".lower()

        matched = None
        for k in KNOWLEDGE_BASE:
            if k in model_name:
                matched = KNOWLEDGE_BASE[k]
                break
        if not matched:
            matched = {
                "pros": ["Direct owner vehicle verified by 200+ point inspection", "Zero dealer margin or hidden inventory markups", "Clear title and RTO transfer assistance"],
                "cons": ["Direct owner test drive scheduling required"],
                "maintenance_yr": "₹6,000 - ₹8,500",
                "retention_pct": 0.73,
            }

        price = c.get("truwo_price") or c.get("listed_price") or 0
        km = c.get("kms_driven", 0)
        dealer_p = c.get("dealer_price") or 0

        is_assured = c.get("verified", True)
        tier = "verified" if is_assured else "owner"

        retention_pct = matched["retention_pct"]
        retention_val = round(price * retention_pct)
        total_loss_2yr = price - retention_val
        monthly_loss = round(total_loss_2yr / 24)

        orig_retail = estimate_original_retail(make, model, variant, year, c.get("transmission"))
        if orig_retail <= price:
            orig_retail = round((price * 1.40) / 10000) * 10000
        retail_discount_pct = max(5, min(85, round((1.0 - (price / orig_retail)) * 100)))

        # Deal score calculation
        score = 48  # Direct owner verified baseline
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

        # Value bonus if benchmarked below dealer price
        if dealer_p > price and (dealer_p - price) >= 50000:
            score += 4

        final_score = min(99, max(40, score))
        deal_grade = "TOP DEAL" if final_score >= 80 else ("VALUE PICK" if final_score >= 68 else "FAIR")

        pros = matched.get("pros", [])
        verdict = pros[0] if pros else "Inspected direct-owner vehicle benchmarked below dealer price."

        locality = c.get("locality") or c.get("area") or "Bangalore"
        hub = f"{locality}, Bangalore" if "bangalore" not in locality.lower() else locality

        img_url = c.get("hero_photo") or c.get("image")
        slug = c.get("slug")
        url = c.get("url") or (f"https://www.truwo.ai/i/{slug}" if slug else "https://www.truwo.ai/listings")
        cid = c.get("id") or (url.rstrip("/").split("/")[-1] if url else slug)

        # Transmission inference if not provided
        raw_trans = c.get("transmission")
        if not raw_trans:
            is_auto = any(k in model_name for k in [" at", "amt", "cvt", "auto", "ivt", "dct"])
            transmission = "Automatic" if is_auto else "Manual"
        else:
            transmission = raw_trans.capitalize()

        raw_fuel = c.get("fuel_type")
        if not raw_fuel:
            if "diesel" in model_name: fuel = "Diesel"
            elif "cng" in model_name: fuel = "CNG"
            elif "electric" in model_name or " ev" in model_name: fuel = "Electric"
            else: fuel = "Petrol"
        else:
            fuel = raw_fuel.capitalize()

        cleaned.append({
            "id": f"truwo_{cid}",
            "platform": "Truwo",
            "make": make,
            "model": model,
            "variant": variant,
            "make_year": year,
            "mileage": km,
            "price": price,
            "dealer_benchmark_price": dealer_p,
            "orig_retail_price": orig_retail,
            "retail_discount_pct": retail_discount_pct,
            "fuel_type": fuel,
            "transmission": transmission,
            "category": tier,
            "hub": hub,
            "img": img_url,
            "url": url,
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

def fetch_olx_cars(max_pages=15, max_price=None, make=None):
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
    }
    cars = []
    seen_ids = set()
    price_param = f"&price_max={max_price}&price_min=50000" if (max_price and max_price > 0) else ""
    make_param = f"&make={make}" if make else ""

    try:
        from scrapling.fetchers import Fetcher
    except ImportError:
        Fetcher = None

    for page in range(max_pages):
        url = f"https://www.olx.in/api/relevance/v4/search?category=84&facet_limit=1000&location=4058803&location_facet_limit=40&platform=web-desktop&pttEnabled=true&relaxedFilters=true&size=40&user=anonymous&lang=en-IN&page={page}{price_param}{make_param}"
        try:
            if Fetcher:
                res = Fetcher.get(url, headers=headers, timeout=15)
                if res.status != 200:
                    break
                body = res.body.decode("utf-8", errors="ignore")
            else:
                r = requests.get(url, headers=headers, timeout=15)
                if r.status_code != 200:
                    break
                body = r.text

            data = json.loads(body)
            items = data.get("data", [])
            if not items:
                break

            for it in items:
                ad_id = str(it.get("id") or "")
                if not ad_id or ad_id in seen_ids:
                    continue
                seen_ids.add(ad_id)

                status = str(it.get("status", {}).get("status") or it.get("status") or "").lower()
                if status in ["deleted", "expired", "inactive"]:
                    continue

                raw_price = it.get("price", {}).get("value", {}).get("raw", 0)
                if raw_price <= 0:
                    continue
                if max_price and max_price > 0 and raw_price > max_price:
                    continue

                params = {}
                for p in it.get("parameters", []):
                    k = p.get("key")
                    v = p.get("value_name") or p.get("formatted_value") or p.get("value")
                    if k and v:
                        params[k] = v

                loc = it.get("locations_resolved") or {}
                subloc = loc.get("SUBLOCALITY_LEVEL_1_name") or "Bangalore"

                imgs = [img.get("url") for img in it.get("images", []) if img.get("url")]
                hero_img = imgs[0] if imgs else ""
                if hero_img and not hero_img.endswith(";s=780x0;q=80"):
                    hero_img = f"{hero_img};s=780x0;q=80"

                cars.append({
                    "id": ad_id,
                    "title": it.get("title", ""),
                    "price": float(raw_price),
                    "params": params,
                    "sublocality": subloc,
                    "hero_img": hero_img,
                    "ad_url": f"https://www.olx.in/item/iid-{ad_id}",
                    "user_type": it.get("user_type", ""),
                    "is_business": it.get("is_business", False),
                })
        except Exception as e:
            print(f"[{datetime.now()}] Error fetching OLX page {page}: {e}", file=sys.stderr)
            break

    return cars


def enrich_olx(cars):
    cleaned = []
    for c in cars:
        params = c.get("params", {})
        make = params.get("make") or ""
        model = params.get("model") or ""
        variant = params.get("variant") or ""

        raw_title = c.get("title") or ""
        if not make and raw_title:
            parts = raw_title.split(" ")
            make = parts[0] if parts else "Other"
            model = parts[1] if len(parts) > 1 else ""
            variant = " ".join(parts[2:]) if len(parts) > 2 else ""

        try:
            year = int(params.get("year") or 2017)
        except Exception:
            year = 2017

        try:
            km = int(re.sub(r"[^\d]", "", str(params.get("mileage") or "50000")))
        except Exception:
            km = 50000

        fuel = (params.get("petrol") or "Petrol").capitalize()
        transmission = (params.get("transmission") or "Manual").capitalize()
        is_business = c.get("is_business", False)
        owner = str(params.get("first_owner") or "")

        model_name = f"{make} {model} {variant}".lower()

        matched = None
        for k in KNOWLEDGE_BASE:
            if k in model_name:
                matched = KNOWLEDGE_BASE[k]
                break
        if not matched:
            matched = {
                "pros": ["Direct seller listing with zero platform surcharge", "Real-world negotiation margin in Bangalore local market", "Complete maintenance and service history reviewable with owner"],
                "cons": ["Direct buyer-seller diligence and RTO name transfer verification recommended"],
                "maintenance_yr": "₹6,000 - ₹9,000",
                "retention_pct": 0.68,
            }

        price = c.get("price") or 0
        if price <= 0:
            continue

        retention_pct = matched["retention_pct"]
        retention_val = round(price * retention_pct)
        total_loss_2yr = price - retention_val
        monthly_loss = round(total_loss_2yr / 24)

        orig_retail = estimate_original_retail(make, model, variant, year, transmission)
        if orig_retail <= price:
            orig_retail = round((price * 1.45) / 10000) * 10000
        retail_discount_pct = max(5, min(85, round((1.0 - (price / orig_retail)) * 100)))

        score = 44
        if km <= 25000: score += 24
        elif km <= 40000: score += 18
        elif km <= 60000: score += 12
        elif km <= 80000: score += 5
        elif km > 100000: score -= 10

        if year >= 2021: score += 22
        elif year >= 2019: score += 18
        elif year >= 2017: score += 12
        elif year >= 2015: score += 6
        elif year <= 2012: score -= 8

        if owner in ["1st", "1", "First"]: score += 6
        if not is_business: score += 5
        if year >= 2018 and km <= 40000: score += 5

        final_score = min(99, max(40, score))
        deal_grade = "TOP DEAL" if final_score >= 80 else ("VALUE PICK" if final_score >= 68 else "FAIR")

        breakdown = [
            {"pillar": "Base Inventory Baseline", "detail": "Direct Bangalore classified listing", "pts": "+40 pts", "type": "base"}
        ]
        if km <= 35000:
            breakdown.append({"pillar": "Odometer & Engine Wear", "detail": f"Low mileage ({km//1000}k km) · well below market wear", "pts": "+18 pts", "type": "pos"})
        elif km <= 65000:
            breakdown.append({"pillar": "Odometer & Engine Wear", "detail": f"Average wear ({km//1000}k km) · typical city usage", "pts": "+10 pts", "type": "pos"})
        elif km > 90000:
            breakdown.append({"pillar": "Odometer & Engine Wear", "detail": f"High odometer ({km//1000}k km) · assess engine mounts", "pts": "-8 pts", "type": "neg"})

        if year >= 2019:
            breakdown.append({"pillar": "Vehicle Age & Generation", "detail": f"Recent {year} generation · low age wear", "pts": "+18 pts", "type": "pos"})
        elif year >= 2015:
            breakdown.append({"pillar": "Vehicle Age & Generation", "detail": f"Mature {year} vehicle · reliable mechanical platform", "pts": "+10 pts", "type": "pos"})
        else:
            breakdown.append({"pillar": "Vehicle Age & Generation", "detail": f"{year} model · age-related maintenance cycle", "pts": "-6 pts", "type": "neg"})

        if retail_discount_pct >= 30:
            breakdown.append({"pillar": "Depreciation Arbitrage", "detail": f"Direct seller savings · {retail_discount_pct}% off original MSRP", "pts": "+10 pts", "type": "pos"})

        if owner in ["1st", "1", "First"]:
            breakdown.append({"pillar": "Ownership History", "detail": "1st owner vehicle · clear title provenance", "pts": "+6 pts", "type": "pos"})

        if not is_business:
            breakdown.append({"pillar": "Direct Seller Liquidity", "detail": "Private seller deal · zero dealership inventory markup", "pts": "+5 pts", "type": "pos"})

        rationale_reasons = []
        if km <= 35000: rationale_reasons.append("low odometer wear")
        if year >= 2019: rationale_reasons.append("recent generation")
        if retail_discount_pct >= 30: rationale_reasons.append("strong depreciation arbitrage")
        if not is_business: rationale_reasons.append("private seller value pricing")
        score_rationale = f"Rated {final_score}/100 primarily driven by " + (", ".join(rationale_reasons) if rationale_reasons else "Bangalore market pricing and mechanical baseline") + "."

        pros = matched.get("pros", [])
        verdict = pros[0] if pros else "Direct private seller listing with high price arbitrage."

        subloc = c.get("sublocality") or "Bangalore"
        hub = f"{subloc}, Bangalore" if "bangalore" not in subloc.lower() else subloc

        cleaned.append({
            "id": f"olx_{c['id']}",
            "platform": "OLX",
            "make": make,
            "model": model,
            "variant": variant,
            "make_year": year,
            "mileage": km,
            "price": price,
            "orig_retail_price": orig_retail,
            "retail_discount_pct": retail_discount_pct,
            "fuel_type": fuel,
            "transmission": transmission,
            "category": "direct_owner" if not is_business else "dealer",
            "hub": hub,
            "img": c.get("hero_img") or "",
            "url": c.get("ad_url") or f"https://www.olx.in/item/iid-{c['id']}",
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
            "score_breakdown": breakdown,
            "score_rationale": score_rationale,
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
    cars24_raw = fetch_cars24_cars(city_id="4709", max_pages=75, max_price=max_price)
    cleaned_cars24 = enrich_cars24(cars24_raw)
    print(f"[{datetime.now()}] Fetched {len(cleaned_cars24)} Cars24 cars.")

    print(f"[{datetime.now()}] Fetching Bangalore cars from Truwo (Direct Owner Verified)...")
    truwo_raw = fetch_truwo_cars(max_price=max_price)
    cleaned_truwo = enrich_truwo(truwo_raw)
    print(f"[{datetime.now()}] Fetched {len(cleaned_truwo)} Truwo cars.")

    print(f"[{datetime.now()}] Fetching Bangalore cars from OLX API (Direct Seller Classifieds)...")
    olx_raw = fetch_olx_cars(max_pages=15, max_price=max_price)
    cleaned_olx = enrich_olx(olx_raw)
    print(f"[{datetime.now()}] Fetched {len(cleaned_olx)} OLX cars.")

    print(f"[{datetime.now()}] Fetching Bangalore BMW inventory from OLX API (Targeted Luxury Pipeline)...")
    olx_bmw_raw = fetch_olx_cars(max_pages=4, make="bmw")
    cleaned_olx_bmw = enrich_olx(olx_bmw_raw)
    print(f"[{datetime.now()}] Fetched {len(cleaned_olx_bmw)} targeted BMW cars from OLX.")

    # Deduplicate OLX inventory by ad id
    olx_dedup_map = {}
    for c in (cleaned_olx + cleaned_olx_bmw):
        olx_dedup_map[c.get("id")] = c
    total_olx = list(olx_dedup_map.values())

    combined_cars = cleaned_spinny + cleaned_cars24 + cleaned_truwo + total_olx
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
    print(f"[{datetime.now()}] === Bangalore Combined Deals Screener ({price_label}) — Found {len(combined_cars)} Cars ({len(cleaned_spinny)} Spinny + {len(cleaned_cars24)} Cars24 + {len(cleaned_truwo)} Truwo + {len(total_olx)} OLX) ===")
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
            score = d.get('deal_score', 0)
            url = d.get('url', '')
            notify_mac(f"Top {plat} Deal Alert!", f"{title} for {price_l} ({km_k}, Score {score})")
            send_mobile_push(f"Top {plat} Deal: {title}", f"{price_l} · {km_k} · Score {score}/100", click_url=url)
        print(f"[{datetime.now()}] Alert & mobile push dispatched for {len(good_deals)} high-conviction deal(s).")
    elif not is_initial_run:
        print(f"[{datetime.now()}] Inventory refreshed. No new qualifying top deals (< ₹4L, Score 80+).")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bangalore Used Car Deals Screener & Monitor")
    parser.add_argument("--city", default="bangalore", help="Target city")
    parser.add_argument("--max-price", type=int, default=0, help="Max budget threshold (0 for unlimited)")
    parser.add_argument("--test-notify", action="store_true", help="Dispatch a test macOS notification")
    parser.add_argument("--test-push", action="store_true", help="Dispatch a test mobile push notification via ntfy")
    args = parser.parse_args()

    if args.test_notify or args.test_push:
        notify_mac("Top Deal Alert (Test)!", "2021 VW Polo TSI for ₹4.85L (Score 98, 22k km)")
        send_mobile_push("Top Deal (Test): 2021 VW Polo TSI", "₹4.85L · 22k km · Score 98/100 on Spinny", click_url="https://kiranpuli.github.io/bangalore-car-radar/")
        print(f"[{datetime.now()}] Test desktop banner and mobile push notification dispatched to ntfy.sh/{NTFY_TOPIC}.")
        sys.exit(0)
        sys.exit(0)

    max_p = None if args.max_price <= 0 else args.max_price
    run_monitor(city=args.city, max_price=max_p)
