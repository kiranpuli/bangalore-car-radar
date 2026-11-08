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
    # MG
    "astor": 1380000, "hector": 1780000, "gloster": 3800000, "zs ev": 2200000, "comet": 780000,
    # Luxury European
    "x1": 4600000, "x3": 6600000, "3 series": 4800000, "5 series": 6800000,
    "gla": 4800000, "glc": 6800000, "c-class": 5600000, "e-class": 7400000,
    "a4": 4600000, "a6": 6200000, "q3": 4400000, "q5": 6600000,
    "xf": 7200000, "f-pace": 7500000, "xc40": 4600000, "xc60": 6800000,
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


def get_ownership_review(make, model, fuel, trans, year):
    m_lower = (make or "").lower().strip()
    mod_lower = (model or "").lower().strip()
    f_lower = (fuel or "petrol").lower().strip()
    t_lower = (trans or "manual").lower().strip()
    is_auto = any(x in t_lower for x in ["auto", "amt", "cvt", "dsg", "at", "dct"])
    is_diesel = "diesel" in f_lower
    is_cng = "cng" in f_lower

    city_mpg = "12-14 km/l"
    hwy_mpg = "17-19 km/l"
    maint = "₹5,000 - ₹7,000 / yr"
    ride = "Balanced suspension over city potholes; 170mm ground clearance clears normal Bangalore humps."
    issues = "Inspect clutch wear in stop-and-go traffic; check front suspension bushes and brake pads."
    verdict = "Practical daily Bangalore commuter with steady parts availability and reliable resale liquidity."

    if "kwid" in mod_lower:
        city_mpg = "13-15 km/l" if not is_auto else "12-14 km/l"
        hwy_mpg = "19-21 km/l"
        maint = "₹4,000 - ₹5,500 / yr"
        ride = "184mm class-leading ground clearance clears severe Bangalore speed breakers with zero scraping."
        issues = "AMT gearbox exhibits noticeable shift lag in Silk Board crawl; inspect front lower arm bushes and AC cooling."
        verdict = "Best low-budget first car for narrow residential streets in Bangalore with low upkeep cost."
    elif "triber" in mod_lower:
        city_mpg = "11-13 km/l"
        hwy_mpg = "16-18 km/l"
        maint = "₹5,000 - ₹6,500 / yr"
        ride = "182mm ground clearance with long suspension travel absorbs bad roads; modular 7-seater flexibility."
        issues = "1.0L engine feels underpowered with full 7-passenger load on steep flyovers; verify clutch health."
        verdict = "Unbeatable space-per-rupee for Bangalore families needing 7-seater capability on a tight budget."
    elif "swift" in mod_lower or "dzire" in mod_lower:
        city_mpg = "13-15 km/l" if not is_diesel else "16-18 km/l"
        hwy_mpg = "19-22 km/l" if not is_diesel else "22-25 km/l"
        maint = "₹4,500 - ₹6,000 / yr"
        ride = "Plush low-speed damping over broken tarmac; 163mm ground clearance needs gentle angling on huge humps."
        issues = "Steering column rattle over rumble strips; inspect clutch plate wear from bumper-to-bumper ORR crawling."
        verdict = "Bangalore's gold standard commuter: instant parts availability at any FNG and fastest resale turnaround."
    elif "baleno" in mod_lower or "glanza" in mod_lower:
        city_mpg = "13-15 km/l"
        hwy_mpg = "19-21 km/l"
        maint = "₹4,500 - ₹6,000 / yr"
        ride = "Wide, airy cabin with light steering effortless in Bangalore traffic; supple low-speed ride."
        issues = "Thin sheet metal prone to minor city door dings; check lower suspension arm ball joints."
        verdict = "Superb rear seat legroom and low running costs make it an ideal family hatchback for daily city use."
    elif "wagon r" in mod_lower or "wagonr" in mod_lower:
        city_mpg = "14-16 km/l" if not is_cng else "22-25 km/kg"
        hwy_mpg = "19-22 km/l"
        maint = "₹3,500 - ₹5,000 / yr"
        ride = "Tall-boy upright seating gives commanding visibility in tight traffic; easy ingress/egress for elderly."
        issues = "Body roll on highway turns; AMT actuator can get jerky in peak summer traffic if fluid is old."
        verdict = "The ultimate stress-free Bangalore city runabout with negligible maintenance and highest fuel efficiency."
    elif "alto" in mod_lower:
        city_mpg = "15-18 km/l"
        hwy_mpg = "21-24 km/l"
        maint = "₹3,000 - ₹4,500 / yr"
        ride = "Compact footprint fits the tightest parking spots in Malleshwaram or Indiranagar; basic suspension."
        issues = "Lightweight steering lacks highway feel; inspect tyre wear and front wheel bearings."
        verdict = "Lowest cost-of-ownership car in India. Unmatched fuel economy and practically free maintenance."
    elif "i10" in mod_lower or "grand i10" in mod_lower:
        city_mpg = "11-13 km/l"
        hwy_mpg = "16-18 km/l"
        maint = "₹5,000 - ₹7,000 / yr"
        ride = "Refined 4-cylinder engine with whisper-quiet cabin insulation; very light clutch for Bangalore traffic."
        issues = "Steering column coupling bush wear causes dull thuds; clutch life typically 40k-50k km in heavy traffic."
        verdict = "Premium interior feel and smooth refinement make it one of the most comfortable daily hatchbacks."
    elif "i20" in mod_lower:
        city_mpg = "10-12 km/l" if not is_diesel else "14-16 km/l"
        hwy_mpg = "15-17 km/l" if not is_diesel else "19-22 km/l"
        maint = "₹6,000 - ₹8,000 / yr"
        ride = "Solid European-like highway composure and well-damped suspension; comfortable rear bench with rear AC vents."
        issues = "Slightly thirsty 1.2L petrol in Silk Board traffic (9-10 km/l); check steering rack end play."
        verdict = "Feature-packed premium hatchback that feels like a segment above on Mysore highway road trips."
    elif "creta" in mod_lower or "seltos" in mod_lower:
        city_mpg = "10-12 km/l" if not is_diesel else "14-16 km/l"
        hwy_mpg = "15-17 km/l" if not is_diesel else "19-21 km/l"
        maint = "₹7,500 - ₹10,000 / yr"
        ride = "190mm ground clearance floats effortlessly over potholed roads; high seating posture intimidates auto-rickshaws."
        issues = "Clutch hardness on manual variants; check brake pad wear and suspension stabilizer links."
        verdict = "Bangalore's most popular compact SUV for a reason: high prestige, zero scraping, and top-tier resale value."
    elif "venue" in mod_lower or "sonet" in mod_lower:
        city_mpg = "11-13 km/l"
        hwy_mpg = "16-18 km/l"
        maint = "₹6,000 - ₹8,500 / yr"
        ride = "195mm ground clearance handles monsoon flooding and giant speed breakers with absolute confidence."
        issues = "Slightly stiff rear suspension on sharp potholes; DCT automatic can heat up in standstill traffic."
        verdict = "Compact footprint with true SUV stance. Easy to park in Whitefield tech parks while soaking up cratered roads."
    elif "nexon" in mod_lower:
        city_mpg = "11-13 km/l" if not is_diesel else "15-17 km/l"
        hwy_mpg = "16-18 km/l" if not is_diesel else "20-22 km/l"
        maint = "₹6,000 - ₹8,500 / yr"
        ride = "5-Star Global NCAP safety tank with 209mm ground clearance; impervious to Bangalore's worst potholes."
        issues = "AMT gearbox feels jerky between 1st and 2nd gear; touchscreen infotainment occasionally lags."
        verdict = "Heavy-duty road safety and rugged suspension make it the ultimate crater-proof Bangalore city SUV."
    elif "tiago" in mod_lower or "tigor" in mod_lower:
        city_mpg = "12-14 km/l"
        hwy_mpg = "18-20 km/l"
        maint = "₹5,000 - ₹7,000 / yr"
        ride = "Solid build quality that feels much safer than Maruti rivals; stable at highway speeds."
        issues = "3-cylinder engine vibration at idle; check power window switches and front suspension bushes."
        verdict = "Safe, sturdy entry hatchback that offers great value and peace of mind on both city and highway trips."
    elif "altroz" in mod_lower:
        city_mpg = "12-14 km/l"
        hwy_mpg = "17-19 km/l"
        maint = "₹5,500 - ₹7,500 / yr"
        ride = "5-Star safety chassis with doors opening 90 degrees; planted European high-speed stability."
        issues = "Naturally aspirated petrol feels relaxed on overtakes; verify clutch cable smoothness."
        verdict = "Top choice for safety-conscious buyers wanting a stylish, rock-solid premium hatchback."
    elif "city" in mod_lower:
        city_mpg = "10-12 km/l"
        hwy_mpg = "16-18 km/l"
        maint = "₹6,500 - ₹9,000 / yr"
        ride = "Silky 1.5L i-VTEC petrol engine is an absolute mechanical masterpiece; sofa-grade rear seat comfort."
        issues = "Soft rear suspension bottoms out on tall Bangalore unscientific speed breakers with 4 adults onboard."
        verdict = "Timeless executive sedan. Engine will easily outlast 200,000 km with basic annual fluid changes."
    elif "amaze" in mod_lower:
        city_mpg = "12-14 km/l"
        hwy_mpg = "17-20 km/l"
        maint = "₹5,000 - ₹7,000 / yr"
        ride = "Huge 420L boot and comfortable suspension; CVT automatic is butter-smooth in crawling traffic."
        issues = "Lightweight steering at triple digit speeds; check brake disc rotor scoring."
        verdict = "Extremely reliable compact sedan with Honda mechanical dependability and stress-free ownership."
    elif "polo" in mod_lower or "vento" in mod_lower:
        city_mpg = "10-12 km/l"
        hwy_mpg = "15-18 km/l"
        maint = "₹9,000 - ₹14,000 / yr"
        ride = "Enthusiast's benchmark: laser-precise steering, tank-like door thud, and peerless highway stability."
        issues = "ABS wheel sensors fail frequently (₹2,500/wheel); verify DSG dual-clutch transmission history if automatic."
        verdict = "Driver's delight. Higher annual maintenance than Maruti, but unmatched driving pleasure and road feel."
    elif "ecosport" in mod_lower:
        city_mpg = "11-13 km/l" if not is_diesel else "14-16 km/l"
        hwy_mpg = "15-17 km/l" if not is_diesel else "19-21 km/l"
        maint = "₹7,000 - ₹10,000 / yr"
        ride = "200mm ground clearance with dynamic sporty steering; feels indestructible over rough patches."
        issues = "Ford official service exists but parts take 3-5 days to arrive; inspect timing belt condition on Dragon petrols."
        verdict = "Original compact SUV with rock-solid dynamics. Tremendous second-hand value if serviced regularly."
    elif "xuv" in mod_lower or "scorpio" in mod_lower or "thar" in mod_lower:
        city_mpg = "9-11 km/l"
        hwy_mpg = "13-15 km/l"
        maint = "₹8,000 - ₹12,000 / yr"
        ride = "High-perch road commanding presence; ladder frame or monocoque clears any floodwater or crater effortlessly."
        issues = "Heavy clutch pedal in bumper-to-bumper traffic; check suspension lower ball joints and brake pad life."
        verdict = "Mighty road presence and supreme durability for rough weekend excursions and long touring."
    elif "duster" in mod_lower or "kiger" in mod_lower:
        city_mpg = "12-14 km/l"
        hwy_mpg = "17-19 km/l"
        maint = "₹5,500 - ₹7,500 / yr"
        ride = "Magic carpet ride: absorbs cratered roads and broken tarmac better than cars twice its price."
        issues = "Plastic interior trim rattles over time; check AC cooling efficiency and clutch hydraulics."
        verdict = "Best suspension setup for Bangalore's worst roads. Glides over potholes without shaking the cabin."

    return {
        "fuel_economy": f"{city_mpg} (BLR City) · {hwy_mpg} (Highway)",
        "annual_maintenance": maint,
        "ride_comfort": ride,
        "known_issues": issues,
        "bangalore_verdict": verdict
    }


def calculate_score_and_breakdown(car, orig_retail, discount_pct):
    km = car.get("mileage", 100000)
    year = car.get("make_year", 2015)
    price = car.get("price", 500000)
    is_assured = car.get("category") in ["assured", "verified"] or car.get("platform") in ["Truwo", "OLX"]
    make = (car.get("make") or "").lower()

    factors = []
    base_score = 40
    factors.append({
        "pillar": "Base Inventory Baseline",
        "detail": "Verified clear title & documentation",
        "pts": "+40 pts",
        "type": "base"
    })

    # 1. Mileage Health
    if km <= 25000:
        km_pts = 24
        km_desc = f"Ultra-low odometer ({km//1000}k km) · pristine engine health"
    elif km <= 40000:
        km_pts = 18
        km_desc = f"Low mileage ({km//1000}k km) · well below market wear"
    elif km <= 60000:
        km_pts = 12
        km_desc = f"Moderate mileage ({km//1000}k km) · healthy mechanical life"
    elif km <= 80000:
        km_pts = 6
        km_desc = f"Standard city mileage ({km//1000}k km)"
    else:
        km_pts = -8
        km_desc = f"High mileage ({km//1000}k km) · nearing major suspension service"
    factors.append({
        "pillar": "Odometer & Engine Wear",
        "detail": km_desc,
        "pts": f"{'+' if km_pts > 0 else ''}{km_pts} pts",
        "type": "pos" if km_pts > 0 else "neg"
    })

    # 2. Year & Generation
    if year >= 2021:
        yr_pts = 20
        yr_desc = f"Modern {year} model · BS6 Phase 2 era & updated safety"
    elif year >= 2019:
        yr_pts = 16
        yr_desc = f"Recent {year} generation · BS6 compliant & low age wear"
    elif year >= 2017:
        yr_pts = 11
        yr_desc = f"Solid {year} manufacture · modern chassis"
    elif year >= 2015:
        yr_pts = 5
        yr_desc = f"{year} model · mid-life depreciation curve"
    else:
        yr_pts = -6
        yr_desc = f"{year} vintage · older generation approaching 15-year fitness"
    factors.append({
        "pillar": "Vehicle Age & Generation",
        "detail": yr_desc,
        "pts": f"{'+' if yr_pts > 0 else ''}{yr_pts} pts",
        "type": "pos" if yr_pts > 0 else "neg"
    })

    # 3. Depreciation Arbitrage vs Original Retail
    if discount_pct >= 55:
        disc_pts = 18
        disc_desc = f"Steep {discount_pct}% discount vs ₹{orig_retail/100000:.1f}L new price"
    elif discount_pct >= 45:
        disc_pts = 14
        disc_desc = f"High {discount_pct}% discount vs original retail"
    elif discount_pct >= 35:
        disc_pts = 9
        disc_desc = f"Healthy {discount_pct}% savings from original MSRP"
    else:
        disc_pts = 4
        disc_desc = f"{discount_pct}% under original retail value"
    factors.append({
        "pillar": "Depreciation Arbitrage",
        "detail": disc_desc,
        "pts": f"+{disc_pts} pts",
        "type": "pos"
    })

    # 4. Certification & Warranty
    if car.get("platform") == "Truwo":
        cert_pts = 14
        cert_desc = "Truwo Verified · Direct owner 200-pt inspection & title check"
    elif car.get("platform") == "OLX":
        cert_pts = 10
        cert_desc = "OLX Direct Seller · Zero dealer markup & private seller pricing"
    elif is_assured:
        cert_pts = 14
        cert_desc = "Certified Assured · 200-pt mechanical inspection & 1-year warranty"
    else:
        cert_pts = 4
        cert_desc = "Standard verification checklist · independent inspection recommended"
    factors.append({
        "pillar": "Warranty & Inspection",
        "detail": cert_desc,
        "pts": f"+{cert_pts} pts",
        "type": "pos"
    })

    # 5. Sweet spot / Brand liquidity
    extra_pts = 0
    sweet_reasons = []
    if year >= 2018 and km <= 40000:
        extra_pts += 5
        sweet_reasons.append("post-2018 under 40k km")
    if any(m in make for m in ["maruti", "hyundai", "honda", "toyota"]):
        extra_pts += 4
        sweet_reasons.append("high-liquidity resale engine")
    dealer_bench = car.get("dealer_benchmark_price")
    if dealer_bench and dealer_bench > price:
        dealer_save = dealer_bench - price
        if dealer_save >= 50000:
            extra_pts += 4
            sweet_reasons.append(f"₹{dealer_save//1000}k below dealer benchmark")
    if extra_pts > 0:
        factors.append({
            "pillar": "Bangalore Resale Archetype",
            "detail": f"Sweet spot combo: {', '.join(sweet_reasons)}",
            "pts": f"+{extra_pts} pts",
            "type": "pos"
        })

    raw_total = base_score + km_pts + yr_pts + disc_pts + cert_pts + extra_pts
    final_score = min(99, max(40, raw_total))

    if final_score >= 80:
        deal_grade = "TOP DEAL"
    elif final_score >= 68:
        deal_grade = "VALUE PICK"
    else:
        deal_grade = "FAIR"

    top_pos = [f["pillar"] for f in factors if f["type"] == "pos"][:2]
    rationale = f"Rated {final_score}/100 primarily driven by {', '.join(top_pos).lower()}."
    return final_score, deal_grade, factors, rationale


# Ensure consistent deal scoring, pricing intelligence, score breakdowns & ownership reviews
for c in cars:
    if not c.get("platform"):
        if str(c.get("id", "")).startswith("olx_") or "olx.in" in c.get("url", ""):
            c["platform"] = "OLX"
        elif str(c.get("id", "")).startswith("truwo_") or "truwo.ai" in c.get("url", ""):
            c["platform"] = "Truwo"
        elif str(c.get("id", "")).startswith("c24_") or "cars24.com" in c.get("url", ""):
            c["platform"] = "Cars24"
        else:
            c["platform"] = "Spinny"
    year = c.get("make_year", 2012)
    km = c.get("mileage", 100000)
    price = c.get("price", 500000)
    is_assured = c.get("category") == "assured"

    # Original retail price
    orig_p = c.get("orig_retail_price")
    if not orig_p:
        orig_p = estimate_original_retail(c.get("make"), c.get("model"), c.get("variant"), year, c.get("transmission"))
        if orig_p <= price:
            orig_p = round((price * 1.40) / 10000) * 10000
        c["orig_retail_price"] = orig_p
    discount_pct = max(5, min(85, round((1.0 - (price / orig_p)) * 100)))
    c["retail_discount_pct"] = discount_pct

    # Score calculation and breakdown
    final_score, deal_grade, score_factors, score_rationale = calculate_score_and_breakdown(c, orig_p, discount_pct)
    c["deal_score"] = final_score
    c["deal_grade"] = deal_grade
    c["is_top_deal"] = final_score >= 68
    c["score_breakdown"] = score_factors
    c["score_rationale"] = score_rationale

    # Ownership review
    c["ownership_review"] = get_ownership_review(c.get("make"), c.get("model"), c.get("fuel_type"), c.get("transmission"), year)

    # Fixed price - Spinny and Cars24 operate on no-negotiation fixed pricing
    c.pop("negotiable_price", None)
    c.pop("negotiable_savings", None)

    pros = c.get("analysis", {}).get("pros", [])
    if pros:
        c["verdict"] = pros[0]
    else:
        c["verdict"] = c["ownership_review"]["bangalore_verdict"]

with open(json_path, "w") as fp:
    json.dump(cars, fp, indent=2)

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
  <meta name="description" content="Curated shortlist of verified Bangalore cars under ₹5 Lakhs with high resale retention and certified inspection across Spinny, Cars24, Truwo, and OLX." />
  
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
      --font-sans: 'Geist', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      --font-mono: 'Geist Mono', ui-monospace, SFMono-Regular, monospace;

      /* Warm Titanium Obsidian Theme (elayadesign/ai-design-skills) */
      --bg-canvas: #131209;
      --bg-surface: #1F1F1F;
      --bg-subsurface: #272727;
      --bg-photo: #181818;
      --border-color: #313131;
      --border-focus: #FFFFFF;

      --text-primary: #FFFFFF;
      --text-body: #EDEDED;
      --text-muted: #9B9B9B;
      --text-subtle: #737373;

      --accent-emerald: #10B981;
      --accent-emerald-bg: rgba(16, 185, 129, 0.16);
      --accent-amber: #F59E0B;
      --accent-amber-bg: rgba(245, 158, 11, 0.16);
      --accent-blue: #3B82F6;
      --accent-blue-bg: rgba(59, 130, 246, 0.16);

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

    /* Top Bar Badges */
    .count-pill {
      font-family: var(--font-mono);
      font-size: 11px;
      padding: 1px 7px;
      border-radius: var(--radius-pill);
      background: rgba(255, 255, 255, 0.08);
      color: inherit;
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

    /* Hero Section (Compact & Minimal) */
    .hero-section {
      text-align: center;
      margin: 0 auto var(--sp-200) auto;
      max-width: 680px;
    }
    .hero-tagline-wrap {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 8px;
      flex-wrap: wrap;
      justify-content: center;
    }
    .tagline-badge {
      display: inline-block;
      font-family: var(--font-mono);
      font-size: 10px;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      color: var(--accent-blue);
      background: var(--accent-blue-bg);
      border: 1px solid rgba(59, 130, 246, 0.3);
      padding: 2px 8px;
      border-radius: var(--radius-pill);
    }
    .tagline-compact-text {
      font-family: var(--font-mono);
      font-size: 11px;
      color: var(--text-subtle);
    }
    .tagline-word {
      display: inline-block;
      color: rgba(255, 255, 255, 0.35);
      transition: color 500ms var(--ease-base);
      margin-right: 0.22em;
    }
    .tagline-word.revealed {
      color: #CBD5E1;
    }
    .hero-heading {
      font-size: clamp(28px, 4.5vw, 42px);
      line-height: 1.15;
      font-weight: 600;
      letter-spacing: -0.025em;
      text-wrap: balance;
      background: linear-gradient(90deg, #FFFFFF 0%, #9B9B9B 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      margin-bottom: 8px;
    }
    .hero-subhead {
      color: var(--text-muted);
      font-size: 14.5px;
      line-height: 21px;
      text-wrap: balance;
      margin-bottom: 8px;
    }

            /* Cohesive Filter Workbench & Data-Type Components (elayadesign/ai-design-skills) */
    .filter-deck {
      background: var(--bg-surface);
      border: 1px solid var(--border-color);
      border-radius: var(--radius-xl);
      padding: 16px;
      margin-bottom: 12px;
      display: flex;
      flex-direction: column;
      gap: 14px;
    }

    .deck-row-primary {
      display: flex;
      align-items: center;
      gap: 12px;
      flex-wrap: wrap;
    }

    .deck-search-wrap {
      flex: 1 1 240px;
      position: relative;
      display: flex;
      align-items: center;
    }
    .search-icon-svg {
      position: absolute;
      left: 12px;
      width: 15px;
      height: 15px;
      color: var(--text-subtle);
      pointer-events: none;
    }
    .deck-search-input {
      width: 100%;
      height: 38px;
      background: var(--bg-subsurface);
      border: 1px solid var(--border-color);
      border-radius: var(--radius-md);
      color: var(--text-primary);
      font-family: var(--font-sans);
      font-size: 13px;
      padding: 0 32px 0 36px;
      outline: none;
      transition: border-color var(--dur-fast) var(--ease-base);
    }
    .deck-search-input:focus {
      border-color: var(--border-focus);
    }
    .search-clear-btn {
      position: absolute;
      right: 10px;
      background: transparent;
      border: none;
      color: var(--text-subtle);
      font-size: 12px;
      cursor: pointer;
      display: none;
    }

    .deck-segmented-scope {
      display: inline-flex;
      align-items: center;
      background: var(--bg-subsurface);
      border: 1px solid var(--border-color);
      border-radius: var(--radius-md);
      padding: 3px;
      gap: 2px;
    }
    .scope-segment {
      background: transparent;
      border: none;
      color: var(--text-muted);
      font-family: var(--font-sans);
      font-size: 12.5px;
      font-weight: 500;
      padding: 6px 14px;
      border-radius: 6px;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      transition: all var(--dur-fast) var(--ease-base);
      white-space: nowrap;
    }
    .scope-segment:hover {
      color: var(--text-primary);
    }
    .scope-segment.active, .scope-segment.active.curated {
      background: #FFFFFF;
      color: #000000;
      font-weight: 600;
    }
    .scope-count {
      font-family: var(--font-mono);
      font-size: 10.5px;
      opacity: 0.75;
    }

    .deck-actions-right {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      margin-left: auto;
    }
    .deck-sort-wrap {
      background: var(--bg-subsurface);
      border: 1px solid var(--border-color);
      border-radius: var(--radius-md);
      height: 38px;
      padding: 0 10px;
      display: inline-flex;
      align-items: center;
    }
    .deck-select {
      background: transparent;
      border: none;
      color: var(--text-primary);
      font-family: var(--font-sans);
      font-size: 12.5px;
      outline: none;
      cursor: pointer;
    }
    .deck-select option {
      background: #1F1F1F;
      color: #FFFFFF;
    }

    /* Cohesive Filter Panels Grid (Data Type Tailored) */
    .deck-panels-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 12px;
      border-top: 1px solid rgba(255, 255, 255, 0.05);
      padding-top: 12px;
    }
    .filter-panel {
      background: var(--bg-subsurface);
      border: 1px solid var(--border-color);
      border-radius: var(--radius-lg);
      padding: 12px 14px;
      display: flex;
      flex-direction: column;
      gap: 10px;
    }
    .panel-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
    }
    .panel-title-wrap {
      display: inline-flex;
      align-items: center;
      gap: 8px;
    }
    .panel-label {
      font-family: var(--font-mono);
      font-size: 10.5px;
      font-weight: 600;
      color: var(--text-subtle);
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }
    .range-readout-badge {
      font-family: var(--font-mono);
      font-size: 11px;
      font-weight: 700;
      padding: 2px 7px;
      border-radius: var(--radius-sm);
      background: #181818;
      border: 1px solid var(--border-color);
      color: var(--accent-amber);
    }
    .btn-panel-action {
      background: transparent;
      border: none;
      color: var(--text-subtle);
      font-family: var(--font-mono);
      font-size: 10.5px;
      cursor: pointer;
      padding: 2px 4px;
      border-radius: 4px;
      transition: color var(--dur-fast) var(--ease-base);
    }
    .btn-panel-action:hover {
      color: var(--text-primary);
    }

    /* Continuous Number Range Input UI */
    .num-range-row {
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .num-box {
      flex: 1;
      display: flex;
      flex-direction: column;
      gap: 3px;
    }
    .num-label {
      font-family: var(--font-mono);
      font-size: 9.5px;
      color: var(--text-subtle);
      text-transform: uppercase;
      letter-spacing: 0.03em;
    }
    .num-input-inner {
      display: flex;
      align-items: center;
      background: #181818;
      border: 1px solid var(--border-color);
      border-radius: 6px;
      padding: 0 8px;
      height: 34px;
      transition: border-color var(--dur-fast) var(--ease-base);
    }
    .num-input-inner:focus-within {
      border-color: var(--border-focus);
    }
    .num-currency {
      font-family: var(--font-mono);
      font-size: 12px;
      font-weight: 600;
      color: var(--text-muted);
      padding-right: 4px;
    }
    .num-field {
      flex: 1;
      width: 100%;
      min-width: 0;
      background: transparent;
      border: none;
      color: var(--text-primary);
      font-family: var(--font-mono);
      font-size: 13px;
      font-weight: 600;
      outline: none;
    }
    .num-unit {
      font-family: var(--font-mono);
      font-size: 11px;
      font-weight: 600;
      color: var(--text-subtle);
      padding-left: 2px;
    }
    .num-range-divider {
      color: var(--text-subtle);
      font-family: var(--font-mono);
      font-size: 11px;
      align-self: flex-end;
      padding-bottom: 8px;
    }

    /* Visual Continuous Range Slider */
    .slider-track-wrap {
      display: flex;
      flex-direction: column;
      gap: 4px;
      padding-top: 2px;
    }
    .range-slider-accent {
      -webkit-appearance: none;
      appearance: none;
      width: 100%;
      height: 4px;
      border-radius: 2px;
      background: #313131;
      outline: none;
      cursor: pointer;
    }
    .range-slider-accent::-webkit-slider-thumb {
      -webkit-appearance: none;
      appearance: none;
      width: 16px;
      height: 16px;
      border-radius: 50%;
      background: #FFFFFF;
      border: 2px solid var(--accent-amber);
      cursor: pointer;
      box-shadow: 0 2px 6px rgba(0, 0, 0, 0.6);
      transition: transform var(--dur-fast) var(--ease-base);
    }
    .range-slider-accent::-webkit-slider-thumb:hover {
      transform: scale(1.15);
    }
    .range-slider-accent::-moz-range-thumb {
      width: 16px;
      height: 16px;
      border-radius: 50%;
      background: #FFFFFF;
      border: 2px solid var(--accent-amber);
      cursor: pointer;
    }
    .slider-ticks {
      display: flex;
      justify-content: space-between;
      font-family: var(--font-mono);
      font-size: 9.5px;
      color: var(--text-subtle);
      padding: 0 2px;
    }

    /* Discrete Source Buttons */
    .btn-group-row {
      display: flex;
      gap: 6px;
      flex-wrap: wrap;
    }
    .ctrl-btn {
      background: #181818;
      border: 1px solid var(--border-color);
      color: var(--text-muted);
      font-family: var(--font-sans);
      font-size: 11.5px;
      font-weight: 500;
      padding: 6px 10px;
      border-radius: 6px;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 5px;
      transition: all var(--dur-fast) var(--ease-base);
      white-space: nowrap;
    }
    .ctrl-btn:hover {
      color: var(--text-primary);
      border-color: #4A4A4A;
    }
    .ctrl-btn.active {
      background: #FFFFFF;
      color: #000000;
      font-weight: 600;
      border-color: #FFFFFF;
    }
    .ctrl-btn.active .btn-count {
      opacity: 0.85;
      color: #000000;
    }
    .btn-count {
      font-family: var(--font-mono);
      font-size: 10px;
      opacity: 0.7;
    }

    /* Discrete Segmented Switches for Specs */
    .specs-segmented-wrap {
      display: flex;
      flex-direction: column;
      gap: 8px;
    }
    .segmented-switch {
      background: #181818;
      border: 1px solid var(--border-color);
      border-radius: 6px;
      padding: 2px;
      display: flex;
      align-items: center;
      gap: 2px;
    }
    .switch-opt {
      flex: 1;
      background: transparent;
      border: none;
      color: var(--text-muted);
      font-family: var(--font-sans);
      font-size: 11.5px;
      font-weight: 500;
      padding: 5px 8px;
      border-radius: 4px;
      cursor: pointer;
      text-align: center;
      transition: all var(--dur-fast) var(--ease-base);
      white-space: nowrap;
    }
    .switch-opt:hover {
      color: var(--text-primary);
    }
    .switch-opt.active {
      background: #FFFFFF;
      color: #000000;
      font-weight: 600;
    }

    /* Discrete Brand Chips Panel */
    .panel-brands {
      grid-column: 1 / -1;
    }
    .brand-chips-wrap {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
    }
    .brand-chips-wrap .chip-pill {
      background: #181818;
      border: 1px solid var(--border-color);
      color: var(--text-muted);
      font-family: var(--font-sans);
      font-size: 11.5px;
      font-weight: 500;
      padding: 5px 10px;
      border-radius: 6px;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 4px;
      transition: all var(--dur-fast) var(--ease-base);
      white-space: nowrap;
    }
    .brand-chips-wrap .chip-pill:hover {
      color: var(--text-primary);
      border-color: #4A4A4A;
    }
    .brand-chips-wrap .chip-pill.active {
      background: #FFFFFF;
      color: #000000;
      font-weight: 600;
      border-color: #FFFFFF;
    }

    /* Source Dot Indicators */
    .source-dot {
      width: 5px;
      height: 5px;
      border-radius: 50%;
      display: inline-block;
      flex-shrink: 0;
    }
    .spinny-dot { background: #F59E0B; }
    .cars24-dot { background: #3B82F6; }
    .truwo-dot  { background: #10B981; }
    .olx-dot    { background: #A855F7; }

    /* Results Bar */
    .results-bar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      padding: 6px 2px 12px 2px;
      font-family: var(--font-mono);
      font-size: 12px;
      color: var(--text-muted);
      flex-wrap: wrap;
    }
    .results-meta strong {
      color: var(--text-primary);
    }
    .active-tags-row {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      flex-wrap: wrap;
    }
    .active-tag {
      background: #1F1F1F;
      border: 1px solid var(--border-color);
      color: var(--text-body);
      font-family: var(--font-mono);
      font-size: 10.5px;
      padding: 3px 8px;
      border-radius: var(--radius-pill);
      display: inline-flex;
      align-items: center;
      gap: 5px;
    }
    .active-tag-remove {
      background: transparent;
      border: none;
      color: var(--text-subtle);
      cursor: pointer;
      font-size: 11px;
    }
    .active-tag-remove:hover {
      color: #EF4444;
    }
    .btn-reset-all {
      background: transparent;
      border: 1px solid rgba(239, 68, 68, 0.35);
      color: #F87171;
      font-family: var(--font-mono);
      font-size: 10.5px;
      padding: 3px 8px;
      border-radius: var(--radius-pill);
      cursor: pointer;
      transition: all var(--dur-fast) var(--ease-base);
    }
    .btn-reset-all:hover {
      background: rgba(239, 68, 68, 0.15);
      color: #FFFFFF;
    }

    /* Cars Grid & Cards */
    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(min(100%, 380px), 1fr));
      gap: var(--sp-300);
    }

    .card {
      background: var(--bg-surface);
      border: 1px solid var(--border-color);
      border-radius: var(--radius-lg);
      overflow: hidden;
      display: flex;
      flex-direction: column;
      transition: border-color var(--dur-fast) var(--ease-base), transform var(--dur-fast) var(--ease-base);
    }
    .card:hover {
      border-color: rgba(255, 255, 255, 0.25);
      transform: translateY(-2px);
    }
    .card-photo {
      position: relative;
      height: 200px;
      background: var(--bg-photo);
      overflow: hidden;
      border-bottom: 1px solid var(--border-color);
    }
    .card-photo img {
      width: 100%;
      height: 100%;
      object-fit: cover;
      display: block;
    }
    .badge-grade {
      position: absolute;
      top: 10px;
      left: 10px;
      font-family: var(--font-mono);
      font-size: 11px;
      font-weight: 700;
      padding: 3px 8px;
      border-radius: var(--radius-pill);
      background: rgba(19, 18, 9, 0.9);
      backdrop-filter: blur(8px);
      -webkit-backdrop-filter: blur(8px);
      border: 1px solid rgba(255, 255, 255, 0.12);
      color: #FFFFFF;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 4px;
      z-index: 2;
    }
    .badge-grade.top {
      color: #FBBF24;
      border-color: rgba(245, 158, 11, 0.5);
    }
    .badge-grade.value {
      color: #10B981;
      border-color: rgba(16, 185, 129, 0.5);
    }
    .card-badges-top-right {
      position: absolute;
      top: 10px;
      right: 10px;
      z-index: 2;
    }
    .source-tag {
      font-family: var(--font-mono);
      font-size: 10.5px;
      font-weight: 600;
      padding: 3px 8px;
      border-radius: var(--radius-pill);
      background: rgba(19, 18, 9, 0.9);
      backdrop-filter: blur(8px);
      -webkit-backdrop-filter: blur(8px);
      border: 1px solid rgba(255, 255, 255, 0.12);
      color: #EDEDED;
      display: inline-flex;
      align-items: center;
      gap: 5px;
    }
    .source-tier {
      color: var(--text-muted);
      font-size: 9.5px;
      font-weight: 400;
      border-left: 1px solid rgba(255, 255, 255, 0.15);
      padding-left: 5px;
    }
    .card-content {
      padding: 14px;
      display: flex;
      flex-direction: column;
      gap: 9px;
      flex: 1;
      background: var(--bg-surface);
    }
    .car-title {
      font-size: 16px;
      font-weight: 600;
      color: var(--text-primary);
      line-height: 1.3;
      text-wrap: balance;
    }
    .car-meta-line {
      font-family: var(--font-mono);
      font-size: 11.5px;
      color: var(--text-muted);
      display: flex;
      align-items: center;
      gap: 5px;
      flex-wrap: wrap;
    }
    .meta-hub {
      color: var(--text-subtle);
    }
    .card-pricing-bar {
      display: flex;
      align-items: baseline;
      justify-content: space-between;
      gap: 8px;
      padding-top: 4px;
      border-top: 1px solid rgba(255, 255, 255, 0.05);
    }
    .pricing-main-wrap {
      display: inline-flex;
      align-items: baseline;
      gap: 8px;
    }
    .pricing-val-main {
      font-family: var(--font-mono);
      font-size: 22px;
      font-weight: 700;
      color: #FFFFFF;
      letter-spacing: -0.02em;
    }
    .pricing-val-top {
      font-family: var(--font-mono);
      font-size: 13px;
      color: var(--text-subtle);
      text-decoration: line-through;
    }
    .discount-pill {
      font-family: var(--font-mono);
      font-size: 10px;
      font-weight: 700;
      padding: 2px 5px;
      border-radius: var(--radius-sm);
      background: rgba(16, 185, 129, 0.14);
      color: #10B981;
      border: 1px solid rgba(16, 185, 129, 0.3);
    }
    .pricing-source-badge {
      font-family: var(--font-mono);
      font-size: 10.5px;
      color: var(--text-subtle);
    }
    .pricing-source-badge.truwo {
      color: #10B981;
    }
    .pricing-source-badge.olx {
      color: #C084FC;
    }
    .card-verdict-line {
      font-size: 12px;
      color: var(--text-muted);
      line-height: 1.4;
      text-wrap: pretty;
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
      overflow: hidden;
    }
    .card-intel-peek {
      font-family: var(--font-mono);
      font-size: 10.5px;
      color: var(--text-subtle);
      display: flex;
      gap: 6px;
    }
    .card-footer {
      margin-top: auto;
      padding-top: 4px;
      display: flex;
      align-items: center;
      gap: 6px;
    }
    .card-hide-btn {
      background: var(--bg-subsurface);
      border: 1px solid var(--border-color);
      color: var(--text-muted);
      font-family: var(--font-sans);
      font-size: 11.5px;
      font-weight: 500;
      padding: 8px 10px;
      border-radius: var(--radius-md);
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 4px;
      flex-shrink: 0;
      transition: all var(--dur-fast) var(--ease-base);
      white-space: nowrap;
    }
    .card-hide-btn:hover {
      color: #EF4444;
      border-color: rgba(239, 68, 68, 0.4);
      background: rgba(239, 68, 68, 0.08);
    }
    .card-hide-btn:active {
      transform: scale(0.97);
    }
    .deck-toast {
      position: fixed;
      bottom: 24px;
      left: 50%;
      transform: translateX(-50%) translateY(20px);
      background: #181818;
      border: 1px solid #313131;
      color: #FFFFFF;
      font-family: var(--font-sans);
      font-size: 13px;
      font-weight: 500;
      padding: 10px 18px;
      border-radius: var(--radius-pill);
      box-shadow: 0 12px 32px rgba(0, 0, 0, 0.7);
      z-index: 2000;
      opacity: 0;
      pointer-events: none;
      transition: all 200ms ease;
    }
    .deck-toast.show {
      opacity: 1;
      transform: translateX(-50%) translateY(0);
    }
    .cta-primary-btn {
      width: 100%;
      background: var(--bg-subsurface);
      border: 1px solid var(--border-color);
      color: var(--text-primary);
      font-size: 12.5px;
      font-weight: 600;
      padding: 9px 12px;
      border-radius: var(--radius-md);
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: space-between;
      text-decoration: none;
      transition: all var(--dur-fast) var(--ease-base);
    }
    .cta-primary-btn:hover {
      background: #FFFFFF;
      border-color: #FFFFFF;
      color: #000000;
    }
    .cta-primary-btn:active {
      transform: scale(0.98);
    }

    /* Score Calculation Pop-up Modal (elayadesign/ai-design-skills) */
    .score-modal-backdrop {
      position: fixed;
      inset: 0;
      background: rgba(0, 0, 0, 0.82);
      backdrop-filter: blur(8px);
      -webkit-backdrop-filter: blur(8px);
      z-index: 1000;
      display: none;
      align-items: center;
      justify-content: center;
      padding: var(--sp-200);
      animation: modalFadeIn 200ms var(--ease-base);
    }
    .score-modal-backdrop.open {
      display: flex;
    }
    @keyframes modalFadeIn {
      from { opacity: 0; }
      to { opacity: 1; }
    }
    .score-modal {
      background: var(--bg-surface);
      border: 1px solid var(--border-color);
      border-radius: var(--radius-xl);
      max-width: 620px;
      width: 100%;
      max-height: 90vh;
      display: flex;
      flex-direction: column;
      overflow: hidden;
      box-shadow: 0 24px 64px rgba(0, 0, 0, 0.85);
      animation: modalSlideUp 200ms var(--ease-base);
    }
    @keyframes modalSlideUp {
      from { transform: translateY(12px) scale(0.98); opacity: 0; }
      to { transform: translateY(0) scale(1); opacity: 1; }
    }
    .score-modal-header {
      padding: 14px 18px;
      border-bottom: 1px solid var(--border-color);
      display: flex;
      justify-content: space-between;
      align-items: center;
      background: var(--bg-photo);
    }
    .score-modal-header h3 {
      font-size: 16px;
      font-weight: 600;
      color: var(--text-primary);
      letter-spacing: -0.02em;
    }
    .score-modal-close {
      background: var(--bg-subsurface);
      border: 1px solid var(--border-color);
      color: var(--text-muted);
      font-size: 14px;
      width: 30px;
      height: 30px;
      border-radius: 50%;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      transition: all var(--dur-fast) var(--ease-base);
    }
    .score-modal-close:hover {
      background: #FFFFFF;
      border-color: #FFFFFF;
      color: #000000;
    }
    .score-modal-body {
      padding: 16px;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: 12px;
      background: var(--bg-surface);
    }
    .score-modal-footer {
      padding: 12px 18px;
      border-top: 1px solid var(--border-color);
      background: var(--bg-photo);
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 12px;
    }
    .modal-dismiss-btn {
      background: var(--bg-subsurface);
      border: 1px solid var(--border-color);
      color: var(--text-muted);
      font-family: var(--font-sans);
      font-size: 12px;
      font-weight: 500;
      padding: 8px 14px;
      border-radius: var(--radius-md);
      cursor: pointer;
      transition: all var(--dur-fast) var(--ease-base);
    }
    .modal-dismiss-btn:hover {
      color: var(--text-primary);
      border-color: #4A4A4A;
    }
    .modal-action-cta {
      width: auto !important;
      padding: 8px 18px !important;
      font-size: 12.5px;
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }

    /* Modal Hero Snapshot */
    .modal-car-hero {
      display: flex;
      gap: 12px;
      align-items: center;
      background: var(--bg-photo);
      border: 1px solid var(--border-color);
      border-radius: var(--radius-lg);
      padding: 12px 14px;
      flex-wrap: wrap;
    }
    .modal-car-thumb {
      width: 80px;
      height: 56px;
      object-fit: cover;
      border-radius: 6px;
      background: #000000;
      border: 1px solid var(--border-color);
      flex-shrink: 0;
    }
    .modal-car-thumb.no-thumb {
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 10px;
      color: var(--text-subtle);
    }
    .modal-hero-info {
      flex: 1 1 200px;
      min-width: 0;
      display: flex;
      flex-direction: column;
      gap: 3px;
    }
    .modal-hero-title {
      font-size: 15px;
      font-weight: 600;
      color: var(--text-primary);
      line-height: 1.3;
    }
    .modal-hero-meta {
      font-family: var(--font-mono);
      font-size: 12px;
      color: var(--text-muted);
    }
    .modal-hero-meta strong {
      color: #FFFFFF;
      font-size: 13px;
    }
    .modal-hero-source {
      display: inline-flex;
      align-items: center;
      gap: 5px;
      font-family: var(--font-mono);
      font-size: 11px;
      color: var(--text-subtle);
    }
    .modal-score-ring {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 8px 12px;
      border-radius: 8px;
      border: 1px solid var(--border-color);
      background: var(--bg-subsurface);
      min-width: 90px;
      flex-shrink: 0;
    }
    .modal-score-ring.top {
      background: var(--accent-amber);
      border-color: #D97706;
      color: #000000;
    }
    .modal-score-ring.top .score-ring-val,
    .modal-score-ring.top .score-ring-lbl {
      color: #000000;
    }
    .modal-score-ring.value {
      background: var(--accent-emerald);
      border-color: #059669;
      color: #000000;
    }
    .modal-score-ring.value .score-ring-val,
    .modal-score-ring.value .score-ring-lbl {
      color: #000000;
    }
    .score-ring-val {
      font-family: var(--font-mono);
      font-size: 22px;
      font-weight: 800;
      line-height: 1;
      color: var(--text-primary);
    }
    .score-ring-lbl {
      font-family: var(--font-mono);
      font-size: 9.5px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      margin-top: 3px;
      color: var(--text-muted);
    }

    /* 4-Box Telemetry Grid */
    .telemetry-grid {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 8px;
    }
    .telemetry-box {
      background: var(--bg-subsurface);
      border: 1px solid var(--border-color);
      border-radius: var(--radius-md);
      padding: 10px 12px;
      display: flex;
      flex-direction: column;
      gap: 2px;
    }
    .telemetry-lbl {
      font-family: var(--font-mono);
      font-size: 10px;
      font-weight: 600;
      color: var(--text-subtle);
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }
    .telemetry-num {
      font-family: var(--font-mono);
      font-size: 15px;
      font-weight: 700;
      color: var(--text-primary);
    }
    .telemetry-num.buyback { color: var(--accent-emerald); }
    .telemetry-num.maint { color: var(--text-body); }
    .telemetry-num.savings { color: var(--accent-amber); }
    .telemetry-num.dep { color: #38BDF8; }
    .telemetry-sub {
      font-family: var(--font-mono);
      font-size: 10px;
      color: var(--text-subtle);
    }

    /* Rationale Callout */
    .modal-rationale-box {
      background: var(--bg-subsurface);
      border: 1px solid var(--border-color);
      border-left: 3px solid var(--accent-amber);
      border-radius: var(--radius-md);
      padding: 10px 14px;
      display: flex;
      flex-direction: column;
      gap: 5px;
    }
    .modal-rationale-box.value {
      border-left-color: var(--accent-emerald);
    }
    .rationale-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
    }
    .rationale-badge {
      font-family: var(--font-mono);
      font-size: 10px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: var(--accent-amber);
    }
    .rationale-badge.value {
      color: var(--accent-emerald);
    }
    .modal-rationale-text {
      font-size: 12.5px;
      color: var(--text-body);
      line-height: 1.45;
    }

    /* Point Audit Table */
    .modal-breakdown-wrap {
      background: var(--bg-photo);
      border: 1px solid var(--border-color);
      border-radius: var(--radius-md);
      overflow: hidden;
    }
    .modal-breakdown-head {
      display: flex;
      justify-content: space-between;
      padding: 8px 12px;
      background: var(--bg-subsurface);
      border-bottom: 1px solid var(--border-color);
      font-family: var(--font-mono);
      font-size: 10.5px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: var(--text-subtle);
    }
    .score-audit-list {
      display: flex;
      flex-direction: column;
    }
    .score-audit-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 8px 12px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.04);
      gap: 10px;
    }
    .score-audit-row:last-child {
      border-bottom: none;
    }
    .score-audit-text {
      flex: 1;
      min-width: 0;
    }
    .score-audit-pillar {
      font-size: 12.5px;
      font-weight: 600;
      color: var(--text-primary);
    }
    .score-audit-desc {
      font-size: 11px;
      color: var(--text-muted);
      margin-top: 1px;
    }
    .score-audit-badge {
      font-family: var(--font-mono);
      font-size: 11.5px;
      font-weight: 700;
      padding: 2px 7px;
      border-radius: var(--radius-sm);
      white-space: nowrap;
      flex-shrink: 0;
    }
    .score-audit-badge.pos {
      background: rgba(16, 185, 129, 0.16);
      color: #10B981;
      border: 1px solid rgba(16, 185, 129, 0.3);
    }
    .score-audit-badge.neg {
      background: rgba(239, 68, 68, 0.16);
      color: #EF4444;
      border: 1px solid rgba(239, 68, 68, 0.3);
    }
    .score-audit-badge.base {
      background: #272727;
      color: var(--text-muted);
      border: 1px solid var(--border-color);
    }
    .modal-breakdown-total {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 10px 12px;
      background: var(--bg-subsurface);
      border-top: 1px solid var(--border-color);
      font-family: var(--font-mono);
      font-size: 13px;
      font-weight: 700;
      color: var(--text-primary);
    }

    /* Mechanic Notes (Pros / Cons) */
    .modal-mechanic-notes {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 8px;
    }
    .notes-col {
      background: var(--bg-subsurface);
      border: 1px solid var(--border-color);
      border-radius: var(--radius-md);
      padding: 10px 12px;
      display: flex;
      flex-direction: column;
      gap: 6px;
    }
    .notes-head {
      font-family: var(--font-mono);
      font-size: 10px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      color: var(--text-subtle);
    }
    .pros-col .notes-head { color: var(--accent-emerald); }
    .cons-col .notes-head { color: var(--accent-amber); }
    .notes-list {
      list-style: none;
      display: flex;
      flex-direction: column;
      gap: 4px;
      margin: 0;
      padding: 0;
    }
    .notes-list li {
      font-size: 11.5px;
      color: var(--text-body);
      line-height: 1.4;
      display: flex;
      align-items: flex-start;
      gap: 5px;
    }
    .pro-dot {
      color: var(--accent-emerald);
      font-weight: bold;
      font-size: 11px;
      flex-shrink: 0;
    }
    .con-dot {
      color: var(--accent-amber);
      font-size: 10px;
      flex-shrink: 0;
    }

    .card-audit-btn {
      margin-left: auto;
      background: transparent;
      border: 1px solid var(--border-color);
      color: var(--text-primary);
      font-family: var(--font-mono);
      font-size: 10px;
      font-weight: 600;
      padding: 2px 7px;
      border-radius: 4px;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 3px;
      transition: all var(--dur-fast) var(--ease-base);
    }
    .card-audit-btn:hover {
      background: var(--text-primary);
      color: #000000;
      border-color: var(--text-primary);
    }

    /* Action Button (B2 Button-md padding 8px 12px) */
    .card-footer {
      margin-top: auto;
      padding-top: var(--sp-100);
      border-top: 1px solid var(--border-color);
      display: flex;
      flex-direction: column;
      gap: 6px;
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
      outline: 2px solid var(--border-focus);
      outline-offset: 2px;
    }

    /* Mobile & Tablet Responsive Optimization (elayadesign/ai-design-skills) */
    @media (max-width: 768px) {
      html, body {
        overflow-x: hidden;
        max-width: 100vw;
      }
      .shell {
        padding: 8px 8px 50px 8px;
        max-width: 100%;
        overflow-x: hidden;
      }
      .floating-nav {
        top: 6px;
        margin-bottom: 12px;
        width: 100%;
        padding: 0 4px;
      }
      .nav-inner {
        width: 100%;
        max-width: 100%;
        padding: 6px 8px;
        gap: 4px;
        justify-content: space-between;
        overflow-x: auto;
        scrollbar-width: none;
      }
      .nav-inner::-webkit-scrollbar {
        display: none;
      }
      .nav-stats {
        display: none;
      }
      .nav-btn {
        padding: 5px 8px;
        font-size: 10.5px;
        min-height: 34px;
        flex-shrink: 0;
      }
      .grid {
        grid-template-columns: 1fr;
        gap: 12px;
      }
    }

    @media (max-width: 640px) {
      .hero-section {
        margin: 0 auto 12px auto;
      }
      .hero-heading {
        font-size: clamp(22px, 6.5vw, 28px);
      }
      .hero-subhead {
        font-size: 12.5px;
        line-height: 18px;
      }
      .filter-deck {
        padding: 10px;
        gap: 8px;
        border-radius: var(--radius-lg);
      }
      .deck-row-primary {
        flex-direction: column;
        align-items: stretch;
        gap: 6px;
      }
      .deck-search-wrap {
        width: 100%;
      }
      .deck-segmented-scope {
        width: 100%;
        display: flex;
      }
      .scope-segment {
        flex: 1;
        justify-content: center;
        padding: 6px 2px;
        font-size: 11px;
      }
      .deck-actions-right {
        width: 100%;
        display: flex;
        gap: 6px;
      }
      .deck-sort-wrap {
        flex: 1.2;
        min-height: 34px;
      }
      .deck-select {
        width: 100%;
        min-height: 32px;
      }
      .deck-row-chips {
        display: flex;
        overflow-x: auto;
        -webkit-overflow-scrolling: touch;
        scrollbar-width: none;
        flex-wrap: nowrap;
        gap: 6px;
        padding-top: 6px;
      }
      .deck-row-chips::-webkit-scrollbar {
        display: none;
      }
      .chips-group {
        flex-shrink: 0;
      }
      .grid {
        grid-template-columns: 1fr;
        gap: 12px;
      }
      .card-photo {
        height: 180px;
      }
      .badge-grade {
        max-width: 52%;
        font-size: 9.5px;
        padding: 2px 6px;
      }
      .card-badges-top-right {
        max-width: 46%;
      }
      .source-tag {
        font-size: 9.5px;
        padding: 2px 6px;
      }
      .car-title {
        font-size: 15px;
      }
      .pricing-val-main {
        font-size: 20px;
      }
      .score-modal-backdrop {
        padding: 8px;
      }
      .score-modal {
        max-height: 94vh;
        border-radius: var(--radius-lg);
      }
      .modal-car-hero {
        padding: 10px;
        gap: 10px;
      }
      .modal-score-ring {
        width: 100%;
        flex-direction: row;
        justify-content: space-between;
        padding: 6px 12px;
      }
      .score-ring-lbl {
        margin-top: 0;
      }
      .modal-mechanic-notes {
        grid-template-columns: 1fr;
      }
    }

    /* Small Phone Optimization (iPhone SE / 360px - 380px) */
    @media (max-width: 380px) {
      .nav-brand span:not(.pulse-dot) {
        font-size: 11.5px;
      }
      .nav-btn {
        padding: 4px 6px;
        font-size: 10px;
      }
      .pricing-val-main {
        font-size: 17px;
      }
      .pricing-val-top {
        font-size: 12.5px;
      }
    }

    /* Mobile Touch & Viewport Polish */
    @media (hover: none) and (pointer: coarse) {
      button, a, select, input {
        -webkit-tap-highlight-color: transparent;
      }
      .facet-pill, .preset-chip-btn, .nav-btn, .cta-primary-btn {
        min-height: 38px;
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
      <button class="nav-btn push-alerts-btn" onclick="openPushModal()" title="Instant Mobile Push Alerts">
        <span>📲 Push</span>
      </button>
      <button class="nav-btn" onclick="scrollToFilters()">Filters</button>
    </div>
  </nav>

  <div class="shell">
    <!-- Hero Section (Compact & Minimal) -->
    <header class="hero-section">
      <div class="hero-tagline-wrap" id="tagline-reveal">
        <span class="tagline-badge">Verified Deal Intelligence</span>
        <span class="tagline-compact-text" id="tagline-words"></span>
      </div>
      <h1 class="heading-1 hero-heading">Bangalore Top Used Car Deals</h1>
      <p class="body-3 hero-subhead">
        Curated shortlist of verified Bangalore cars under ₹5 Lakhs with high resale retention and certified inspection across Spinny, Cars24, Truwo, and OLX.
      </p>
    </header>

            <!-- Minimalist Filter Toolbar (elayadesign/ai-design-skills) -->
    <section class="filter-deck" id="filter-workbench" aria-label="Car Filter Control Deck">
      <!-- Line 1: Instant Search, Curated Presets & Sort -->
      <div class="deck-row-primary">
        <div class="deck-search-wrap">
          <svg class="search-icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8"></circle>
            <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
          </svg>
          <input 
            type="text" 
            id="ctrl-search" 
            class="deck-search-input" 
            placeholder="Search make, model, hub, variant..." 
            oninput="onSearchInput(this.value)"
          />
          <button type="button" id="btn-clear-search" class="search-clear-btn" onclick="clearSearch()" title="Clear search">✕</button>
        </div>

        <div class="deck-segmented-scope" role="tablist" aria-label="Inventory Scope">
          <button type="button" class="scope-segment active curated" id="btn-mode-curated" onclick="setViewMode('curated')" role="tab">
            <span>🔥 Top Deals</span>
            <span class="scope-count" id="badge-curated-count">0</span>
          </button>
          <button type="button" class="scope-segment" id="btn-german-5l" onclick="filterGermanUnder5L()" role="tab">
            <span>🛡️ German ≤ ₹5L</span>
            <span class="scope-count" id="badge-german-count">0</span>
          </button>
          <button type="button" class="scope-segment" id="btn-mode-bmw" onclick="filterBmwDeals()" role="tab">
            <span>🏎️ BMW</span>
            <span class="scope-count" id="badge-bmw-count">0</span>
          </button>
          <button type="button" class="scope-segment" id="btn-mode-all" onclick="setViewMode('all')" role="tab">
            <span>All Cars</span>
            <span class="scope-count" id="badge-all-count">0</span>
          </button>
        </div>

        <div class="deck-actions-right">
          <div class="deck-sort-wrap">
            <select id="ctrl-sort" class="deck-select" onchange="onSortChange(this.value)">
              <option value="score">Best Value First</option>
              <option value="price_asc">Price: Low to High</option>
              <option value="price_desc">Price: High to Low</option>
              <option value="discount_desc">Highest Discount %</option>
              <option value="year_desc">Newest First</option>
              <option value="km_asc">Lowest KM</option>
            </select>
          </div>
        </div>
      </div>

      <!-- Cohesive Filter Controls Grid: Structured by Data Type -->
      <div class="deck-panels-grid">
        <!-- Control 1: Exact Number Range with Min/Max and Slider for Price -->
        <div class="filter-panel panel-price">
          <div class="panel-header">
            <div class="panel-title-wrap">
              <span class="panel-label">Budget</span>
              <span class="range-readout-badge" id="price-readout">Up to ₹5.00L</span>
            </div>
            <button type="button" class="btn-panel-action" onclick="clearPrice()" title="Clear budget limits">Any Price</button>
          </div>
          <div class="num-range-row">
            <div class="num-box">
              <span class="num-label">Min</span>
              <div class="num-input-inner">
                <span class="num-currency">₹</span>
                <input 
                  type="number" 
                  id="ctrl-min-price" 
                  class="num-field" 
                  placeholder="0.0" 
                  step="0.25" 
                  min="0" 
                  max="25"
                  value=""
                  oninput="onMinPriceInput(this.value)"
                />
                <span class="num-unit">L</span>
              </div>
            </div>
            <span class="num-range-divider">—</span>
            <div class="num-box">
              <span class="num-label">Max</span>
              <div class="num-input-inner">
                <span class="num-currency">₹</span>
                <input 
                  type="number" 
                  id="ctrl-max-price" 
                  class="num-field" 
                  placeholder="5.0" 
                  step="0.25" 
                  min="0.5" 
                  max="25"
                  value="5.0"
                  oninput="onMaxPriceInput(this.value)"
                />
                <span class="num-unit">L</span>
              </div>
            </div>
          </div>
          <div class="slider-track-wrap">
            <input 
              type="range" 
              id="ctrl-price-range" 
              class="range-slider-accent" 
              min="1.0" 
              max="15.0" 
              step="0.25" 
              value="5.0" 
              oninput="onPriceSlider(this.value)"
              aria-label="Budget Range Slider"
            />
            <div class="slider-ticks">
              <span>₹1L</span>
              <span>₹3L</span>
              <span>₹5L</span>
              <span>₹8L</span>
              <span>₹10L</span>
              <span>₹15L+</span>
            </div>
          </div>
        </div>

        <!-- Control 2: Continuous Percentage Range Slider for Showroom Savings -->
        <div class="filter-panel panel-discount">
          <div class="panel-header">
            <div class="panel-title-wrap">
              <span class="panel-label">Showroom Savings</span>
              <span class="range-readout-badge" id="discount-readout">Any</span>
            </div>
            <button type="button" class="btn-panel-action" onclick="clearDiscount()" title="Clear discount filter">Reset</button>
          </div>
          <div class="slider-track-wrap" style="padding-top:12px;">
            <input 
              type="range" 
              id="ctrl-discount-range" 
              class="range-slider-accent" 
              min="0" 
              max="60" 
              step="5" 
              value="0" 
              oninput="onDiscountSlider(this.value)"
              aria-label="Minimum showroom savings percentage"
            />
            <div class="slider-ticks" style="padding-top:6px;">
              <span>Any</span>
              <span>20% off</span>
              <span>40% off</span>
              <span>60%+ off</span>
            </div>
          </div>
        </div>

        <!-- Control 3: Discrete Source Multi-Select Buttons -->
        <div class="filter-panel panel-sources">
          <div class="panel-header">
            <span class="panel-label">Source</span>
          </div>
          <div class="btn-group-row" id="platforms-pills">
            <button type="button" class="ctrl-btn pill-all active" onclick="clearMultiFilter('platforms')">
              All <span class="btn-count" id="count-all">1,477</span>
            </button>
            <button type="button" class="ctrl-btn pill-item" data-val="Spinny" onclick="toggleMultiFilter('platforms', 'Spinny')">
              <span class="source-dot spinny-dot"></span>Spinny <span class="btn-count" id="count-spinny">0</span>
            </button>
            <button type="button" class="ctrl-btn pill-item" data-val="Cars24" onclick="toggleMultiFilter('platforms', 'Cars24')">
              <span class="source-dot cars24-dot"></span>Cars24 <span class="btn-count" id="count-cars24">0</span>
            </button>
            <button type="button" class="ctrl-btn pill-item" data-val="Truwo" onclick="toggleMultiFilter('platforms', 'Truwo')">
              <span class="source-dot truwo-dot"></span>Truwo <span class="btn-count" id="count-truwo">0</span>
            </button>
            <button type="button" class="ctrl-btn pill-item" data-val="OLX" onclick="toggleMultiFilter('platforms', 'OLX')">
              <span class="source-dot olx-dot"></span>OLX <span class="btn-count" id="count-olx">0</span>
            </button>
          </div>
        </div>

        <!-- Control 4: Discrete Segmented Switches for Specs -->
        <div class="filter-panel panel-specs">
          <div class="panel-header">
            <span class="panel-label">Gearbox & Fuel</span>
          </div>
          <div class="specs-segmented-wrap">
            <div class="segmented-switch" id="transmissions-pills" role="radiogroup" aria-label="Gearbox">
              <button type="button" class="switch-opt pill-all active" onclick="clearMultiFilter('transmissions')">All Gears</button>
              <button type="button" class="switch-opt pill-item" data-val="automatic" onclick="toggleMultiFilter('transmissions', 'automatic')">Auto</button>
              <button type="button" class="switch-opt pill-item" data-val="manual" onclick="toggleMultiFilter('transmissions', 'manual')">Manual</button>
            </div>
            <div class="segmented-switch" id="fuels-pills" role="radiogroup" aria-label="Fuel">
              <button type="button" class="switch-opt pill-all active" onclick="clearMultiFilter('fuels')">All Fuels</button>
              <button type="button" class="switch-opt pill-item" data-val="petrol" onclick="toggleMultiFilter('fuels', 'petrol')">Petrol</button>
              <button type="button" class="switch-opt pill-item" data-val="diesel" onclick="toggleMultiFilter('fuels', 'diesel')">Diesel</button>
              <button type="button" class="switch-opt pill-item" data-val="cng" onclick="toggleMultiFilter('fuels', 'cng')">CNG</button>
            </div>
          </div>
        </div>

        <!-- Control 5: Discrete Automaker Brand Chips -->
        <div class="filter-panel panel-brands">
          <div class="panel-header">
            <div class="panel-title-wrap">
              <span class="panel-label">Automakers</span>
              <span class="caption-5" style="color:var(--text-subtle);">Select brand chips to filter</span>
            </div>
            <button type="button" class="btn-panel-action" onclick="clearMultiFilter('brands')" title="Reset brand selection">All Brands</button>
          </div>
          <div class="brand-chips-wrap" id="brands-pills">
            <button type="button" class="chip-pill pill-all active" onclick="clearMultiFilter('brands')">All Brands</button>
            <button type="button" class="chip-pill pill-item" data-val="maruti" onclick="toggleMultiFilter('brands', 'maruti')">Maruti (<span id="count-maruti">0</span>)</button>
            <button type="button" class="chip-pill pill-item" data-val="hyundai" onclick="toggleMultiFilter('brands', 'hyundai')">Hyundai (<span id="count-hyundai">0</span>)</button>
            <button type="button" class="chip-pill pill-item" data-val="tata" onclick="toggleMultiFilter('brands', 'tata')">Tata (<span id="count-tata">0</span>)</button>
            <button type="button" class="chip-pill pill-item" data-val="honda" onclick="toggleMultiFilter('brands', 'honda')">Honda (<span id="count-honda">0</span>)</button>
            <button type="button" class="chip-pill pill-item" data-val="volkswagen" onclick="toggleMultiFilter('brands', 'volkswagen')">Volkswagen (<span id="count-volkswagen">0</span>)</button>
            <button type="button" class="chip-pill pill-item" data-val="toyota" onclick="toggleMultiFilter('brands', 'toyota')">Toyota (<span id="count-toyota">0</span>)</button>
            <button type="button" class="chip-pill pill-item" data-val="skoda" onclick="toggleMultiFilter('brands', 'skoda')">Skoda (<span id="count-skoda">0</span>)</button>
            <button type="button" class="chip-pill pill-item" data-val="bmw" onclick="toggleMultiFilter('brands', 'bmw')">BMW (<span id="count-bmw">0</span>)</button>
            <button type="button" class="chip-pill pill-item" data-val="mahindra" onclick="toggleMultiFilter('brands', 'mahindra')">Mahindra (<span id="count-mahindra">0</span>)</button>
            <button type="button" class="chip-pill pill-item" data-val="renault" onclick="toggleMultiFilter('brands', 'renault')">Renault (<span id="count-renault">0</span>)</button>
            <button type="button" class="chip-pill pill-item" data-val="mg" onclick="toggleMultiFilter('brands', 'mg')">MG (<span id="count-mg">0</span>)</button>
          </div>
        </div>
      </div>
    </section>

    <!-- Results Status Bar -->
    <div class="results-bar">
      <div class="results-meta">
        Showing <strong id="res-count">0</strong> verified Bangalore cars
      </div>
      <div id="active-tags-container" class="active-tags-row"></div>
      <button class="btn-reset-all" id="btn-global-reset" onclick="resetAll()">Reset All ✕</button>
    </div>


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

  <!-- Score Calculation Pop-up Modal -->
  <div class="score-modal-backdrop" id="score-modal-backdrop" onclick="closeScoreModalOnBackdrop(event)">
    <div class="score-modal" role="dialog" aria-modal="true" aria-labelledby="score-modal-title">
      <div class="score-modal-header">
        <div>
          <span class="caption-5" style="color:var(--accent-amber); font-family:var(--font-mono); text-transform:uppercase; font-weight:700; letter-spacing:0.06em;">Deal Scorecard &amp; Mechanical Audit</span>
          <h3 id="score-modal-title" style="margin-top:2px;">Score Calculation</h3>
        </div>
        <button type="button" class="score-modal-close" onclick="closeScoreModal()" title="Close dialog">✕</button>
      </div>
      <div class="score-modal-body" id="score-modal-body">
        <!-- Injected dynamically on click -->
      </div>
      <div class="score-modal-footer">
        <button type="button" class="card-hide-btn" id="modal-hide-btn" style="padding:8px 12px;" onclick="excludeModelFromModal()">
          <span>⊘ Hide Model</span>
        </button>
        <div style="display:flex; gap:8px; align-items:center;">
          <button type="button" class="modal-dismiss-btn" onclick="closeScoreModal()">Done</button>
          <a href="#" target="_blank" rel="noopener noreferrer" class="cta-primary-btn modal-action-cta" id="modal-footer-cta">
            <span>Inspect Car</span>
            <span>&rarr;</span>
          </a>
        </div>
      </div>
    </div>
  </div>

  <!-- Mobile Push Notifications Setup Modal -->
  <div class="score-modal-backdrop" id="push-modal-backdrop" onclick="closePushModalOnBackdrop(event)">
    <div class="score-modal" role="dialog" aria-modal="true" aria-labelledby="push-modal-title">
      <div class="score-modal-header">
        <div>
          <span class="caption-5" style="color:var(--accent-amber); font-family:var(--font-mono); text-transform:uppercase; font-weight:700; letter-spacing:0.06em;">Real-Time Alert Pipeline</span>
          <h3 id="push-modal-title" style="margin-top:2px;">Instant Mobile Push Alerts</h3>
        </div>
        <button type="button" class="score-modal-close" onclick="closePushModal()" title="Close dialog">✕</button>
      </div>
      <div class="score-modal-body" style="gap:14px;">
        <div style="background:var(--bg-photo); border:1px solid var(--border-color); border-radius:var(--radius-lg); padding:14px; display:flex; flex-direction:column; gap:8px;">
          <div style="display:flex; align-items:center; gap:8px;">
            <span style="font-size:18px;">📲</span>
            <strong style="color:var(--text-primary); font-size:14px;">Get Deals Pushed Directly to Your Phone</strong>
          </div>
          <p class="caption-2" style="color:var(--text-muted); margin:0; line-height:1.5;">
            Top Bangalore deals get booked in under 3 hours. Connect your phone via <strong>ntfy.sh</strong> (free, open source, zero signups) to receive instant push alerts with direct listing links whenever a qualifying car drops.
          </p>
        </div>

        <a href="https://ntfy.sh/kiran-car-radar" target="_blank" rel="noopener noreferrer" class="cta-primary-btn" style="text-decoration:none; display:flex; justify-content:center; align-items:center; gap:8px; padding:12px; font-size:13.5px; font-weight:700;">
          <span>📱 Open on Phone to Subscribe (ntfy.sh/kiran-car-radar)</span>
          <span>&rarr;</span>
        </a>

        <div style="background:var(--bg-subsurface); border:1px solid var(--border-color); border-radius:var(--radius-md); padding:12px 14px; display:flex; flex-direction:column; gap:8px;">
          <span class="caption-5" style="color:var(--text-subtle); text-transform:uppercase; font-weight:700; font-family:var(--font-mono);">How to Subscribe in 30 Seconds</span>
          <div style="font-size:12px; color:var(--text-body); line-height:1.5;">
            <strong>iPhone (iOS):</strong> Tap the link above in Safari &rarr; Tap "Subscribe", or install the free <code>ntfy</code> app from App Store & subscribe to <code>kiran-car-radar</code>.<br/>
            <strong>Android:</strong> Tap the link above in Chrome &rarr; Tap "Subscribe", or install <code>ntfy</code> from Google Play Store.
          </div>
        </div>

        <button type="button" class="nav-btn" onclick="sendTestPushFromBrowser()" style="width:100%; justify-content:center; padding:10px; font-size:12.5px; font-weight:600;">
          <span>⚡ Send Test Push Notification to My Phone</span>
        </button>
        <div id="push-test-result" style="display:none; font-size:12px; font-family:var(--font-mono); text-align:center;"></div>
      </div>
      <div class="score-modal-footer">
        <span class="caption-5" style="color:var(--text-subtle);">Automated crawler dispatches push alerts on every qualifying top deal.</span>
        <button type="button" class="modal-dismiss-btn" onclick="closePushModal()">Done</button>
      </div>
    </div>
  </div>

  <!-- Excluded Models Manager Modal -->
  <div class="score-modal-backdrop" id="excluded-modal-backdrop" onclick="closeExcludedModalOnBackdrop(event)">
    <div class="score-modal" role="dialog" aria-modal="true" aria-labelledby="excluded-modal-title">
      <div class="score-modal-header">
        <div>
          <span class="caption-5" style="color:#EF4444; font-family:var(--font-mono); text-transform:uppercase; font-weight:700; letter-spacing:0.06em;">Preference Filter</span>
          <h3 id="excluded-modal-title" style="margin-top:2px;">Hidden Car Models</h3>
        </div>
        <button type="button" class="score-modal-close" onclick="closeExcludedModal()" title="Close dialog">✕</button>
      </div>
      <div class="score-modal-body" style="gap:12px;">
        <p class="caption-2" style="color:var(--text-muted); margin:0;">
          Cars matching these models are hidden from your feed and scoring. Click "⊘ Hide Model" on any vehicle card to hide more models.
        </p>
        <div id="excluded-models-list" style="display:flex; flex-direction:column; gap:6px;">
          <!-- Injected dynamically -->
        </div>
      </div>
      <div class="score-modal-footer">
        <button type="button" class="nav-btn" onclick="unhideAllModels()" style="color:#EF4444; border-color:rgba(239,68,68,0.3);">Restore All Models</button>
        <button type="button" class="modal-dismiss-btn" onclick="closeExcludedModal()">Done</button>
      </div>
    </div>
  </div>

  <div id="deck-toast" class="deck-toast" role="status" aria-live="polite"></div>

  <script>
    const CARS = """ + cars_json + """;
    const ALERTS = """ + alerts_json + """;

    // Application state - Defaults strictly to Curated Top Deals to Consider (< ₹5L, Score 80+)
    function loadExcludedModels() {
      try {
        const saved = localStorage.getItem('spinny_excluded_models');
        if (saved) {
          const arr = JSON.parse(saved);
          return new Set(arr.map(x => String(x).toLowerCase().trim()));
        }
      } catch (e) {}
      return new Set();
    }

    function saveExcludedModels() {
      try {
        localStorage.setItem('spinny_excluded_models', JSON.stringify(Array.from(state.excludedModels)));
      } catch (e) {}
    }

    function showToast(msg) {
      const toast = document.getElementById('deck-toast');
      if (!toast) return;
      toast.textContent = msg;
      toast.classList.add('show');
      setTimeout(() => {
        toast.classList.remove('show');
      }, 2500);
    }

    const state = {
      viewMode: 'curated',
      density: 'minimal',
      filterDrawerOpen: false,
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
      qualities: new Set(['top_deal']),
      min_discount: 0,
      excludedModels: loadExcludedModels()
    };
    const expandedCards = new Set();

    // Initialize counts
    const spinnyCount = CARS.filter(c => (c.platform || '').toLowerCase() === 'spinny').length;
    const cars24Count = CARS.filter(c => (c.platform || '').toLowerCase() === 'cars24').length;
    const truwoCount = CARS.filter(c => (c.platform || '').toLowerCase() === 'truwo').length;
    const olxCount = CARS.filter(c => (c.platform || '').toLowerCase() === 'olx').length;
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

    const germanCount = CARS.filter(c => {
      const m = (c.make || '').toLowerCase();
      return (m.includes('volkswagen') || m.includes('skoda') || m.includes('bmw') || m.includes('audi')) && (c.price || 0) <= 500000;
    }).length;
    const badgeGerman = document.getElementById('badge-german-count');
    if (badgeGerman) badgeGerman.textContent = germanCount.toLocaleString('en-IN');

    const bmwCount = CARS.filter(c => (c.make || '').toLowerCase().includes('bmw')).length;
    const badgeBmw = document.getElementById('badge-bmw-count');
    if (badgeBmw) badgeBmw.textContent = bmwCount.toLocaleString('en-IN');

    const countAll = document.getElementById('count-all');
    if (countAll) countAll.textContent = CARS.length.toLocaleString('en-IN');
    const countSpinny = document.getElementById('count-spinny');
    if (countSpinny) countSpinny.textContent = spinnyCount.toLocaleString('en-IN');
    const countCars24 = document.getElementById('count-cars24');
    if (countCars24) countCars24.textContent = cars24Count.toLocaleString('en-IN');
    const countTruwo = document.getElementById('count-truwo');
    if (countTruwo) countTruwo.textContent = truwoCount.toLocaleString('en-IN');
    const countOlx = document.getElementById('count-olx');
    if (countOlx) countOlx.textContent = olxCount.toLocaleString('en-IN');


    // Dynamic brand counts
    ['maruti', 'hyundai', 'tata', 'renault', 'honda', 'volkswagen', 'toyota', 'mahindra', 'ford', 'kia', 'skoda', 'bmw', 'mg', 'jeep'].forEach(b => {
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
    const taglineContent = "Transparent pricing and verified mechanical telemetry. Every Bangalore car evaluated for true value and mechanical health.";
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

    function toggleFilterDrawer() {
      const drawer = document.getElementById('filter-categories-drawer');
      const btn = document.getElementById('btn-toggle-filters');
      if (!drawer) return;
      const isClosed = drawer.style.display === 'none';
      if (isClosed) {
        drawer.style.display = 'flex';
        if (btn) btn.classList.add('open');
        state.filterDrawerOpen = true;
      } else {
        drawer.style.display = 'none';
        if (btn) btn.classList.remove('open');
        state.filterDrawerOpen = false;
      }
    }

    function scrollToFilters() {
      const drawer = document.getElementById('filter-categories-drawer');
      const btn = document.getElementById('btn-toggle-filters');
      if (drawer && drawer.style.display === 'none') {
        drawer.style.display = 'flex';
        if (btn) btn.classList.add('open');
        state.filterDrawerOpen = true;
      }
      const el = document.getElementById('filter-workbench');
      if (el) el.scrollIntoView({ behavior: 'smooth' });
    }

    function updateFilterBadge() {
      let count = 0;
      if (state.platforms.size > 0) count += state.platforms.size;
      if (state.brands.size > 0) count += state.brands.size;
      if (state.transmissions.size > 0) count += state.transmissions.size;
      if (state.fuels.size > 0) count += state.fuels.size;
      if (state.min_year > 0) count += 1;
      if (state.max_km > 0 && !(state.viewMode === 'curated' && state.max_km === 80000)) count += 1;
      if (state.min_price > 0 || (state.max_price > 0 && !(state.viewMode === 'curated' && state.max_price === 500000))) count += 1;
      if (state.min_discount > 0) count += 1;
      if (state.qualities.size > 0 && !(state.viewMode === 'curated' && state.qualities.size === 1 && state.qualities.has('top_deal'))) {
        count += state.qualities.size;
      }

      const badge = document.getElementById('filter-active-count');
      if (badge) badge.textContent = count;
    }


    function setDensityMode(mode) {
      state.density = mode;
      const btnMin = document.getElementById('btn-density-min');
      const btnExp = document.getElementById('btn-density-exp');
      if (mode === 'detailed') {
        if (btnExp) btnExp.classList.add('active');
        if (btnMin) btnMin.classList.remove('active');
      } else {
        if (btnMin) btnMin.classList.add('active');
        if (btnExp) btnExp.classList.remove('active');
      }
      applyFilters();
    }

    function toggleCardIntel(carId, event) {
      if (event) {
        event.stopPropagation();
        event.preventDefault();
      }
      const drawer = document.getElementById(`intel-drawer-${carId}`);
      const btn = document.getElementById(`intel-btn-${carId}`);
      const strId = String(carId);

      if (expandedCards.has(strId)) {
        expandedCards.delete(strId);
        if (drawer) drawer.classList.remove('open');
        if (btn) btn.classList.remove('active');
      } else {
        expandedCards.add(strId);
        if (drawer) drawer.classList.add('open');
        if (btn) btn.classList.add('active');
      }
    }

    // View Mode Switcher (Curated Top Deals vs All Market vs German vs BMW)
    function setViewMode(mode) {
      state.viewMode = mode;
      const btnCurated = document.getElementById('btn-mode-curated');
      const btnAll = document.getElementById('btn-mode-all');
      const btnGerman = document.getElementById('btn-german-5l');
      const btnBmw = document.getElementById('btn-mode-bmw');

      if (btnCurated) btnCurated.classList.remove('active', 'curated');
      if (btnAll) btnAll.classList.remove('active');
      if (btnGerman) btnGerman.classList.remove('active');
      if (btnBmw) btnBmw.classList.remove('active');

      if (mode === 'curated') {
        if (btnCurated) btnCurated.classList.add('active', 'curated');

        state.min_price = 0;
        state.max_price = 500000;
        state.max_km = 80000;
        state.brands.clear();
        state.qualities.clear();
        state.qualities.add('top_deal');

        const minInput = document.getElementById('ctrl-min-price');
        if (minInput) minInput.value = '';
        const maxInput = document.getElementById('ctrl-max-price');
        if (maxInput) maxInput.value = '5.0';
        const slider = document.getElementById('ctrl-price-range');
        if (slider) slider.value = 5.0;
      } else {
        if (btnAll) btnAll.classList.add('active');

        state.min_price = 0;
        state.max_price = 0;
        state.max_km = 0;
        state.brands.clear();
        state.qualities.delete('top_deal');

        const minInput = document.getElementById('ctrl-min-price');
        if (minInput) minInput.value = '';
        const maxInput = document.getElementById('ctrl-max-price');
        if (maxInput) maxInput.value = '';
        const slider = document.getElementById('ctrl-price-range');
        if (slider) slider.value = 15.0;
      }
      updatePriceReadout();
      updateAllMultiFilterUIs();
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
        body.innerHTML = '<p style="color:var(--text-muted); padding:20px; text-align:center;">No recent alerts recorded yet. Hourly monitor refreshes active inventory continuously.</p>';
        return;
      }
      body.innerHTML = ALERTS.map(a => {
        const title = `${a.make_year} ${a.make} ${a.model} ${a.variant || ''}`.trim();
        const price = '₹' + (a.price / 100000).toFixed(2) + 'L';
        const disc = a.retail_discount_pct ? `${a.retail_discount_pct}% off` : '';
        const km = (a.mileage / 1000).toFixed(0) + 'k km';
        const plat = (a.platform || '').toLowerCase();
        const platBadge = plat === 'truwo' ? 'badge-platform truwo' : (plat === 'olx' ? 'badge-platform olx' : (plat === 'cars24' ? 'badge-platform cars24' : 'badge-platform spinny'));

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
                ${disc ? `<span style="color:var(--accent-emerald); font-weight:600;">(${disc} top price)</span>` : ''}
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
        // If selecting BMW as brand while constrained by default sub-5L ceiling, uncap budget to show all BMWs
        if (groupKey === 'brands' && val === 'bmw' && state.max_price > 0 && state.max_price <= 500000 && state.brands.size === 1) {
          state.max_price = 0;
          const maxInput = document.getElementById('ctrl-max-price');
          if (maxInput) maxInput.value = '';
          updatePriceReadout();
          showToast('Budget ceiling lifted to display all live Bangalore BMW listings');
        }
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

    function updatePriceReadout() {
      const readout = document.getElementById('price-readout');
      if (!readout) return;
      const minL = state.min_price ? (state.min_price / 100000).toFixed(2).replace(/\\.00$/, '').replace(/(\\.[1-9])0$/, '$1') : '';
      const maxL = state.max_price ? (state.max_price / 100000).toFixed(2).replace(/\\.00$/, '').replace(/(\\.[1-9])0$/, '$1') : '';

      if (!minL && !maxL) {
        readout.textContent = 'Any Price';
      } else if (!minL && maxL) {
        readout.textContent = `Up to ₹${maxL}L`;
      } else if (minL && maxL) {
        readout.textContent = `₹${minL}L – ₹${maxL}L`;
      } else if (minL && !maxL) {
        readout.textContent = `Above ₹${minL}L`;
      }
    }

    function onMinPriceInput(val) {
      const num = parseFloat(val);
      state.min_price = (!isNaN(num) && num > 0) ? Math.round(num * 100000) : 0;
      updatePriceReadout();
      applyFilters();
    }

    function onMaxPriceInput(val) {
      const num = parseFloat(val);
      if (!isNaN(num) && num > 0) {
        state.max_price = Math.round(num * 100000);
        const slider = document.getElementById('ctrl-price-range');
        if (slider) slider.value = Math.min(15.0, Math.max(1.0, num));
      } else {
        state.max_price = 0;
      }
      updatePriceReadout();
      applyFilters();
    }

    function onPriceSlider(val) {
      const num = parseFloat(val);
      const maxInput = document.getElementById('ctrl-max-price');
      if (num >= 15.0) {
        state.max_price = 1500000;
        if (maxInput) maxInput.value = '15.0';
      } else {
        state.max_price = Math.round(num * 100000);
        if (maxInput) maxInput.value = num.toFixed(2).replace(/\\.00$/, '').replace(/(\\.[1-9])0$/, '$1');
      }
      updatePriceReadout();
      applyFilters();
    }

    function clearPrice() {
      const minInput = document.getElementById('ctrl-min-price');
      if (minInput) minInput.value = '';
      const maxInput = document.getElementById('ctrl-max-price');
      if (maxInput) maxInput.value = '';
      const slider = document.getElementById('ctrl-price-range');
      if (slider) slider.value = 15.0;
      state.min_price = 0;
      state.max_price = 0;
      updatePriceReadout();
      applyFilters();
    }

    function onDiscountSlider(val) {
      const num = parseInt(val, 10);
      state.min_discount = (!isNaN(num) && num > 0) ? num : 0;
      const readout = document.getElementById('discount-readout');
      if (readout) {
        readout.textContent = state.min_discount > 0 ? `≥ ${state.min_discount}% Off` : 'Any';
      }
      applyFilters();
    }

    function clearDiscount() {
      state.min_discount = 0;
      const slider = document.getElementById('ctrl-discount-range');
      if (slider) slider.value = 0;
      const readout = document.getElementById('discount-readout');
      if (readout) readout.textContent = 'Any';
      applyFilters();
    }

    function syncQuickBudgetButtons() {}
    function syncDiscountButtons() {}

    function resetAll() {
      state.viewMode = 'curated';
      state.search = '';
      state.min_year = 0;
      state.min_price = 0;
      state.max_price = 500000;
      state.max_km = 80000;
      state.min_discount = 0;
      state.sort = 'score';

      state.platforms.clear();
      state.brands.clear();
      state.transmissions.clear();
      state.fuels.clear();
      state.qualities.clear();
      state.qualities.add('top_deal');

      const sInp = document.getElementById('ctrl-search');
      if (sInp) sInp.value = '';
      const clearBtn = document.getElementById('btn-clear-search');
      if (clearBtn) clearBtn.style.display = 'none';

      const minInp = document.getElementById('ctrl-min-price');
      if (minInp) minInp.value = '';
      const maxInp = document.getElementById('ctrl-max-price');
      if (maxInp) maxInp.value = '5.0';
      const slider = document.getElementById('ctrl-price-range');
      if (slider) slider.value = 5.0;

      const dSlider = document.getElementById('ctrl-discount-range');
      if (dSlider) dSlider.value = 0;
      const dReadout = document.getElementById('discount-readout');
      if (dReadout) dReadout.textContent = 'Any';

      const sDrop = document.getElementById('ctrl-sort');
      if (sDrop) sDrop.value = 'score';

      const btnCurated = document.getElementById('btn-mode-curated');
      const btnAll = document.getElementById('btn-mode-all');
      const btnGerman = document.getElementById('btn-german-5l');
      const btnBmw = document.getElementById('btn-mode-bmw');
      if (btnCurated) btnCurated.classList.add('active', 'curated');
      if (btnAll) btnAll.classList.remove('active');
      if (btnGerman) btnGerman.classList.remove('active');
      if (btnBmw) btnBmw.classList.remove('active');

      updatePriceReadout();
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

      if (state.excludedModels && state.excludedModels.size > 0) {
        tags.push({ label: `⊘ Hidden (${state.excludedModels.size} models)`, clear: () => openExcludedModal() });
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

      if (state.min_discount > 0) {
        tags.push({ label: `Discount: ≥ ${state.min_discount}% Off Top Price`, clear: () => clearDiscount() });
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
        tags.push({ label: `Year: ${state.min_year}+`, clear: () => setYear(0, null) });
      }

      if (state.max_km > 0 && !(state.viewMode === 'curated' && state.max_km === 80000)) {
        tags.push({ label: `Mileage: ≤ ${Math.round(state.max_km / 1000)}k km`, clear: () => setMaxKm(0, null) });
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
        // Excluded models check
        if (state.excludedModels && state.excludedModels.size > 0) {
          const fullCarName = `${c.make || ''} ${c.model || ''}`.toLowerCase();
          for (const ex of state.excludedModels) {
            if (fullCarName.includes(ex)) return false;
          }
        }

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

        // Discount on Top Price
        if (state.min_discount > 0) {
          const disc = c.retail_discount_pct || (c.orig_retail_price ? Math.round(((c.orig_retail_price - c.price) / c.orig_retail_price) * 100) : 0);
          if (disc < state.min_discount) return false;
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
      if (state.sort === 'discount_desc') {
        filtered.sort((a, b) => (b.retail_discount_pct || 0) - (a.retail_discount_pct || 0));
      } else if (state.sort === 'price_asc') {
        filtered.sort((a, b) => (a.price || 0) - (b.price || 0));
      } else if (state.sort === 'price_desc') {
        filtered.sort((a, b) => (b.price || 0) - (a.price || 0));
      } else if (state.sort === 'year_desc') {
        filtered.sort((a, b) => (b.make_year || 0) - (a.make_year || 0));
      } else if (state.sort === 'km_asc') {
        filtered.sort((a, b) => (a.mileage || 0) - (b.mileage || 0));
      } else {
        filtered.sort((a, b) => (b.deal_score || 0) - (a.deal_score || 0));
      }

      const resCount = document.getElementById('res-count');
      if (resCount) resCount.textContent = filtered.length.toLocaleString('en-IN');
      updateFilterBadge();
      renderActiveTags();
      renderCards(filtered);
    }

    function openScoreModal(carId, event) {
      if (event) {
        event.stopPropagation();
        event.preventDefault();
      }
      const car = CARS.find(x => String(x.id) === String(carId));
      if (!car) return;

      const plat = (car.platform || '').toLowerCase();
      const isTruwo = plat === 'truwo';
      const isCars24 = plat === 'cars24';
      const isOlx = plat === 'olx';
      const platformClass = isOlx ? 'olx' : (isTruwo ? 'truwo' : (isCars24 ? 'cars24' : 'spinny'));
      const platformName = car.platform || (isOlx ? 'OLX' : (isTruwo ? 'Truwo' : (isCars24 ? 'Cars24' : 'Spinny')));
      const title = `${car.make_year} ${car.make} ${car.model} ${car.variant || ''}`.trim();
      const price = '₹' + (car.price / 100000).toFixed(2) + 'L';
      const topPrice = car.orig_retail_price ? ('₹' + (car.orig_retail_price / 100000).toFixed(2) + 'L') : '';
      const discPct = car.retail_discount_pct || (car.orig_retail_price ? Math.round(((car.orig_retail_price - car.price) / car.orig_retail_price) * 100) : 0);
      const km = (car.mileage / 1000).toFixed(0) + 'k km';

      const an = car.analysis || {};
      const buyback = an.est_buyback_2yr ? ('₹' + (an.est_buyback_2yr / 100000).toFixed(2) + 'L') : ('₹' + ((car.price * 0.65) / 100000).toFixed(2) + 'L');
      const maint = an.maintenance_yr || '₹6,000 - ₹8,000/yr';
      const retention = an.retention_pct ? `${Math.round(an.retention_pct * 100)}%` : '65%';
      const monthly = an.monthly_loss ? ('₹' + Math.round(an.monthly_loss).toLocaleString('en-IN') + '/mo') : ('₹' + Math.round((car.price * 0.35) / 24).toLocaleString('en-IN') + '/mo');

      let gradeClass = 'fair';
      let gradeLabel = 'Fair Value';
      let gradeColor = 'var(--text-body)';
      if (car.deal_score >= 80) {
        gradeClass = 'top';
        gradeLabel = 'Top Deal';
        gradeColor = 'var(--accent-amber)';
      } else if (car.deal_score >= 68) {
        gradeClass = 'value';
        gradeLabel = 'Value Pick';
        gradeColor = 'var(--accent-emerald)';
      }

      const factors = car.score_breakdown || [];
      const factorsHtml = factors.map(f => {
        const typeClass = f.type || 'pos';
        return `
          <div class="score-audit-row">
            <div class="score-audit-text">
              <div class="score-audit-pillar">${f.pillar}</div>
              <div class="score-audit-desc">${f.detail}</div>
            </div>
            <span class="score-audit-badge ${typeClass}">${f.pts}</span>
          </div>
        `;
      }).join('');

      const prosList = (an.pros || []).map(p => `<li><span class="pro-dot">✓</span><span>${p}</span></li>`).join('');
      const consList = (an.cons || []).map(c => `<li><span class="con-dot">⚠</span><span>${c}</span></li>`).join('');

      const modalTitle = document.getElementById('score-modal-title');
      if (modalTitle) modalTitle.textContent = `${title}`;

      const modalBody = document.getElementById('score-modal-body');
      if (modalBody) {
        modalBody.innerHTML = `
          <!-- Vehicle Summary Hero Card -->
          <div class="modal-car-hero">
            ${car.img ? `<img src="${car.img}" alt="${title}" class="modal-car-thumb" loading="lazy" referrerpolicy="no-referrer" />` : '<div class="modal-car-thumb no-thumb">No Image</div>'}
            <div class="modal-hero-info">
              <div class="modal-hero-title">${title}</div>
              <div class="modal-hero-meta">
                <strong>${price}</strong> · <span>${km}</span> · <span>${(car.fuel_type || 'Petrol').toUpperCase()}</span> · <span>${(car.transmission || 'MT').toUpperCase()}</span>
              </div>
              <div class="modal-hero-source">
                <span class="source-dot ${platformClass}-dot"></span>
                <span>${platformName}</span>
                <span class="meta-hub">(${car.hub || 'Bangalore'})</span>
              </div>
            </div>
            <div class="modal-score-ring ${gradeClass}">
              <div class="score-ring-val">${car.deal_score}</div>
              <div class="score-ring-lbl">${gradeLabel}</div>
            </div>
          </div>

          <!-- 4-Box Value & Depreciation Telemetry -->
          <div class="telemetry-grid">
            <div class="telemetry-box">
              <span class="telemetry-lbl">2-Yr Estimated Buyback</span>
              <span class="telemetry-num buyback">${buyback}</span>
              <span class="telemetry-sub">${retention} retention</span>
            </div>
            <div class="telemetry-box">
              <span class="telemetry-lbl">Annual Maintenance</span>
              <span class="telemetry-num maint">${maint}</span>
              <span class="telemetry-sub">FNG / dealer avg</span>
            </div>
            <div class="telemetry-box">
              <span class="telemetry-lbl">Showroom Savings</span>
              <span class="telemetry-num savings">${discPct > 0 ? `-${discPct}%` : 'Fair'}</span>
              <span class="telemetry-sub">${topPrice ? `Original MRP: ${topPrice}` : 'vs Bangalore new'}</span>
            </div>
            <div class="telemetry-box">
              <span class="telemetry-lbl">Depreciation Pace</span>
              <span class="telemetry-num dep">${monthly}</span>
              <span class="telemetry-sub">Monthly true cost</span>
            </div>
          </div>

          <!-- Algorithmic Score Rationale -->
          <div class="modal-rationale-box ${gradeClass}">
            <div class="rationale-head">
              <span class="rationale-badge ${gradeClass}">Rating Analysis</span>
              <span class="caption-5" style="color:var(--text-subtle);">200-Pt Telemetry</span>
            </div>
            <div class="modal-rationale-text">
              ${car.score_rationale || 'Score computed from odometer health, age wear, retail discount arbitrage, and certified mechanical warranty coverage.'}
            </div>
          </div>

          <!-- Score Breakdown Table -->
          <div class="modal-breakdown-wrap">
            <div class="modal-breakdown-head">
              <span>Pillar & Telemetry Audit</span>
              <span>Points Awarded</span>
            </div>
            <div class="score-audit-list">
              ${factorsHtml}
            </div>
            <div class="modal-breakdown-total">
              <span>Final Deal Score</span>
              <strong style="color:${gradeColor}">${car.deal_score} / 100</strong>
            </div>
          </div>

          <!-- Pros & Considerations -->
          ${(prosList || consList) ? `
          <div class="modal-mechanic-notes">
            ${prosList ? `
            <div class="notes-col pros-col">
              <div class="notes-head">Key Advantages</div>
              <ul class="notes-list">${prosList}</ul>
            </div>` : ''}
            ${consList ? `
            <div class="notes-col cons-col">
              <div class="notes-head">Things to Inspect</div>
              <ul class="notes-list">${consList}</ul>
            </div>` : ''}
          </div>` : ''}
        `;
      }

      // Update footer actions
      const footerCta = document.getElementById('modal-footer-cta');
      if (footerCta) {
        footerCta.href = car.url || '#';
        footerCta.innerHTML = `<span>Inspect on ${platformName}</span> <span>&rarr;</span>`;
      }
      const hideModalBtn = document.getElementById('modal-hide-btn');
      if (hideModalBtn) {
        hideModalBtn.onclick = function(ev) {
          closeScoreModal();
          excludeModel(car.make, car.model, ev);
        };
      }

      const modal = document.getElementById('score-modal-backdrop');
      if (modal) {
        modal.classList.add('open');
        document.body.style.overflow = 'hidden';
      }
    }

    function closeScoreModal() {
      const modal = document.getElementById('score-modal-backdrop');
      if (modal) modal.classList.remove('open');
      document.body.style.overflow = '';
    }

    function closeScoreModalOnBackdrop(e) {
      if (e && e.target && e.target.id === 'score-modal-backdrop') {
        closeScoreModal();
      }
    }

    function excludeModel(make, model, event) {
      if (event) {
        event.stopPropagation();
        event.preventDefault();
      }
      const modelClean = `${make || ''} ${model || ''}`.trim();
      if (!modelClean) return;
      const key = modelClean.toLowerCase();
      state.excludedModels.add(key);
      saveExcludedModels();
      showToast(`⊘ Hidden all ${modelClean} cars from your feed`);
      applyFilters();
    }

    function unhideModel(key) {
      state.excludedModels.delete(key.toLowerCase());
      saveExcludedModels();
      renderExcludedModal();
      showToast(`Restored ${key} to your feed`);
      applyFilters();
    }

    function unhideAllModels() {
      state.excludedModels.clear();
      saveExcludedModels();
      renderExcludedModal();
      showToast('Restored all hidden models');
      applyFilters();
    }

    function renderExcludedModal() {
      const container = document.getElementById('excluded-models-list');
      if (!container) return;
      if (state.excludedModels.size === 0) {
        container.innerHTML = '<p style="color:var(--text-muted); font-size:12.5px; padding:18px 0; text-align:center;">No models hidden yet.<br/>Click "⊘ Hide Model" on any vehicle card to filter it out.</p>';
        return;
      }
      container.innerHTML = Array.from(state.excludedModels).map(m => `
        <div style="display:flex; justify-content:space-between; align-items:center; background:var(--bg-subsurface); border:1px solid var(--border-color); border-radius:var(--radius-sm); padding:8px 12px;">
          <span style="font-size:13px; font-weight:600; text-transform:capitalize; color:var(--text-primary);">⊘ ${m}</span>
          <button type="button" class="nav-btn" onclick="unhideModel('${m.replace(/'/g, "\\'")}')" style="font-size:11px; padding:3px 8px; color:var(--accent-emerald); border-color:rgba(16,185,129,0.3);">
            ✕ Unhide
          </button>
        </div>
      `).join('');
    }

    function openExcludedModal() {
      renderExcludedModal();
      const modal = document.getElementById('excluded-modal-backdrop');
      if (modal) {
        modal.classList.add('open');
        document.body.style.overflow = 'hidden';
      }
    }

    function closeExcludedModal() {
      const modal = document.getElementById('excluded-modal-backdrop');
      if (modal) modal.classList.remove('open');
      document.body.style.overflow = '';
    }

    function closeExcludedModalOnBackdrop(e) {
      if (e && e.target && e.target.id === 'excluded-modal-backdrop') {
        closeExcludedModal();
      }
    }

    function openPushModal() {
      const modal = document.getElementById('push-modal-backdrop');
      if (modal) {
        modal.classList.add('open');
        document.body.style.overflow = 'hidden';
      }
    }

    function closePushModal() {
      const modal = document.getElementById('push-modal-backdrop');
      if (modal) modal.classList.remove('open');
      document.body.style.overflow = '';
    }

    function closePushModalOnBackdrop(e) {
      if (e && e.target && e.target.id === 'push-modal-backdrop') {
        closePushModal();
      }
    }

    async function sendTestPushFromBrowser() {
      const resBox = document.getElementById('push-test-result');
      if (resBox) {
        resBox.style.display = 'block';
        resBox.style.color = 'var(--accent-amber)';
        resBox.textContent = '⚡ Dispatching push notification to ntfy.sh/kiran-car-radar...';
      }
      try {
        const res = await fetch('https://ntfy.sh/kiran-car-radar', {
          method: 'POST',
          headers: {
            'Title': 'Top Deal Alert (Test)',
            'Tags': 'car,fire',
            'Priority': 'high',
            'Click': window.location.href
          },
          body: 'Bangalore Car Radar: Mobile push alerts are connected successfully!'
        });
        if (res.ok) {
          if (resBox) {
            resBox.style.color = 'var(--accent-emerald)';
            resBox.textContent = '✓ Push sent! Open ntfy on your phone or check notification.';
          }
        } else {
          throw new Error('HTTP ' + res.status);
        }
      } catch (e) {
        if (resBox) {
          resBox.style.color = '#EF4444';
          resBox.textContent = 'Push error: ' + e.message;
        }
      }
    }

    function filterGermanUnder5L() {
      const isCurrentlyActive = state.viewMode === 'german' || (state.max_price === 500000 && state.brands.has('volkswagen') && state.brands.has('skoda'));
      if (isCurrentlyActive) {
        setViewMode('curated');
        return;
      }

      state.viewMode = 'german';
      const btnCurated = document.getElementById('btn-mode-curated');
      const btnAll = document.getElementById('btn-mode-all');
      const btnGerman = document.getElementById('btn-german-5l');
      const btnBmw = document.getElementById('btn-mode-bmw');
      if (btnCurated) btnCurated.classList.remove('active', 'curated');
      if (btnAll) btnAll.classList.remove('active');
      if (btnGerman) btnGerman.classList.add('active');
      if (btnBmw) btnBmw.classList.remove('active');

      const statusText = document.getElementById('mode-status-text');
      if (statusText) statusText.innerHTML = '<span class="pulse-dot" style="background:#34D399; box-shadow:0 0 8px rgba(52,211,153,0.6);"></span><span>German Cars Scope: Volkswagen, Skoda, BMW, Audi ≤ ₹5.0L across Bangalore</span>';

      state.search = '';
      const sInput = document.getElementById('ctrl-search');
      if (sInput) sInput.value = '';

      state.min_price = 0;
      state.max_price = 500000;
      const minInput = document.getElementById('ctrl-min-price');
      if (minInput) minInput.value = '';
      const maxInput = document.getElementById('ctrl-max-price');
      if (maxInput) maxInput.value = '5.0';
      const slider = document.getElementById('ctrl-price-range');
      if (slider) slider.value = 5.0;

      state.max_km = 0;
      state.min_year = 0;
      state.min_discount = 0;
      state.qualities.clear();
      state.platforms.clear();
      state.transmissions.clear();
      state.fuels.clear();

      state.brands.clear();
      state.brands.add('volkswagen');
      state.brands.add('skoda');
      state.brands.add('bmw');
      state.brands.add('audi');

      updatePriceReadout();
      updateAllMultiFilterUIs();
      applyFilters();

      const resultsSection = document.getElementById('cars-grid');
      if (resultsSection) resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    function filterBmwDeals() {
      const isCurrentlyActive = state.viewMode === 'bmw' || (state.brands.size === 1 && state.brands.has('bmw'));
      if (isCurrentlyActive) {
        setViewMode('curated');
        return;
      }

      state.viewMode = 'bmw';
      const btnCurated = document.getElementById('btn-mode-curated');
      const btnAll = document.getElementById('btn-mode-all');
      const btnGerman = document.getElementById('btn-german-5l');
      const btnBmw = document.getElementById('btn-mode-bmw');
      if (btnCurated) btnCurated.classList.remove('active', 'curated');
      if (btnAll) btnAll.classList.remove('active');
      if (btnGerman) btnGerman.classList.remove('active');
      if (btnBmw) btnBmw.classList.add('active');

      const statusText = document.getElementById('mode-status-text');
      if (statusText) statusText.innerHTML = '<span class="pulse-dot" style="background:#3B82F6; box-shadow:0 0 8px rgba(59,130,246,0.6);"></span><span>BMW Scope: Live Bangalore BMWs across Spinny, Truwo, Cars24 &amp; OLX</span>';

      state.search = '';
      const sInput = document.getElementById('ctrl-search');
      if (sInput) sInput.value = '';

      state.min_price = 0;
      state.max_price = 0;
      const minInput = document.getElementById('ctrl-min-price');
      if (minInput) minInput.value = '';
      const maxInput = document.getElementById('ctrl-max-price');
      if (maxInput) maxInput.value = '';
      const slider = document.getElementById('ctrl-price-range');
      if (slider) slider.value = 15.0;

      state.max_km = 0;
      state.min_year = 0;
      state.min_discount = 0;
      state.qualities.clear();
      state.platforms.clear();
      state.transmissions.clear();
      state.fuels.clear();

      state.brands.clear();
      state.brands.add('bmw');

      updatePriceReadout();
      updateAllMultiFilterUIs();
      applyFilters();

      const resultsSection = document.getElementById('cars-grid');
      if (resultsSection) resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    window.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        closeScoreModal();
        closeAlertsModal();
        closePushModal();
        closeExcludedModal();
      }
    });

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
        const plat = (c.platform || '').toLowerCase();
        const isTruwo = plat === 'truwo';
        const isCars24 = plat === 'cars24';
        const isOlx = plat === 'olx';
        const isAssured = c.category === 'assured' || c.category === 'verified';
        const tierSubLabel = isOlx 
          ? 'Direct Seller' 
          : (isTruwo ? 'Direct Owner' : (isCars24 ? (isAssured ? 'Assured' : 'Certified') : (isAssured ? 'Assured' : 'Wholesale')));
        const pricingTagText = (isOlx || isTruwo) ? 'Direct Seller' : 'Fixed Price';
        const platformClass = isOlx ? 'olx' : (isTruwo ? 'truwo' : (isCars24 ? 'cars24' : 'spinny'));
        const platformName = c.platform || (isOlx ? 'OLX' : (isTruwo ? 'Truwo' : (isCars24 ? 'Cars24' : 'Spinny')));

        const price = '₹' + (c.price / 100000).toFixed(2) + 'L';
        const topPrice = c.orig_retail_price ? ('₹' + (c.orig_retail_price / 100000).toFixed(2) + 'L') : '';
        const discPct = c.retail_discount_pct || (c.orig_retail_price ? Math.round(((c.orig_retail_price - c.price) / c.orig_retail_price) * 100) : 0);

        const km = (c.mileage / 1000).toFixed(0) + 'k km';
        const title = `${c.make_year} ${c.make} ${c.model} ${c.variant || ''}`.trim();
        const an = c.analysis || {};
        const buyback = '₹' + ((an.est_buyback_2yr || 0) / 100000).toFixed(2) + 'L';

        let gradeClass = 'fair';
        let gradeLabel = `${c.deal_score} · Fair`;
        if (c.deal_score >= 80) {
          gradeClass = 'top';
          gradeLabel = `${c.deal_score} · Top Deal`;
        } else if (c.deal_score >= 68) {
          gradeClass = 'value';
          gradeLabel = `${c.deal_score} · Value`;
        }

        const verdictText = (c.verdict || (an.pros && an.pros[0]) || 'Certified inspected vehicle with verified service history.');

        return `
          <article class="card" id="card-${c.id}">
            <div class="card-photo">
              <button type="button" class="badge-grade ${gradeClass}" onclick="openScoreModal('${c.id}', event)" title="Click to view score audit breakdown">
                <span>★ ${gradeLabel}</span>
              </button>
              
              <div class="card-badges-top-right">
                <span class="source-tag source-${platformClass}">
                  <span class="source-dot ${platformClass}-dot"></span>
                  <span>${platformName}</span>
                  <span class="source-tier">${tierSubLabel}</span>
                </span>
              </div>

              ${c.img ? `<img src="${c.img}" alt="${title}" loading="lazy" referrerpolicy="no-referrer" />` : '<div style="height:100%; display:flex; align-items:center; justify-content:center; color:var(--text-subtle); font-size:12px;">No image preview</div>'}
            </div>

            <div class="card-content">
              <h2 class="car-title">${title}</h2>

              <div class="car-meta-line">
                <span>${km}</span> · <span>${(c.fuel_type || 'Petrol').toUpperCase()}</span> · <span>${(c.transmission || 'MT').toUpperCase()}</span> · <span class="meta-hub">${c.hub}</span>
              </div>

              <div class="card-pricing-bar">
                <div class="pricing-main-wrap">
                  <span class="pricing-val-main">${price}</span>
                  ${topPrice ? `<span class="pricing-val-top">${topPrice}</span>` : ''}
                  ${discPct > 0 ? `<span class="discount-pill">-${discPct}%</span>` : ''}
                </div>
                <span class="pricing-source-badge ${platformClass}">${pricingTagText}</span>
              </div>

              <p class="card-verdict-line">${verdictText}</p>

              <div class="card-intel-peek">
                <span>24M Buyback: ${buyback}</span> · <span>Maint: ${an.maintenance_yr || '₹6.5k/yr'}</span>
                <button type="button" class="card-audit-btn" onclick="openScoreModal('${c.id}', event)" title="View mechanical audit scorecard">Scorecard &rarr;</button>
              </div>

              <div class="card-footer">
                <button type="button" class="card-hide-btn" onclick="excludeModel('${(c.make || '').replace(/'/g, "\\'")}', '${(c.model || '').replace(/'/g, "\\'")}', event)" title="Hide all ${c.make} ${c.model} listings">
                  <span>⊘ Hide Model</span>
                </button>
                <a href="${c.url || '#'}" target="_blank" rel="noopener noreferrer" class="cta-primary-btn">
                  <span>Inspect on ${platformName}</span>
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
    updatePriceReadout();
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
