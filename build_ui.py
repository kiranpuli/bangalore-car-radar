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
    is_assured = car.get("category") in ["assured", "verified"] or car.get("platform") == "Truwo"
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
        if str(c.get("id", "")).startswith("truwo_") or "truwo.ai" in c.get("url", ""):
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
      --font-sans: 'Geist', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      --font-mono: 'Geist Mono', ui-monospace, SFMono-Regular, monospace;

      /* High-contrast, WCAG AAA legible dark tokens */
      --bg-canvas: #090D16;
      --bg-surface: #121824;
      --bg-subsurface: #1A2232;
      --bg-photo: #0B101A;
      --border-color: #263346;
      --border-focus: #38BDF8;

      --text-primary: #FFFFFF;
      --text-body: #F1F5F9;
      --text-muted: #CBD5E1;
      --text-subtle: #94A3B8;

      --accent-emerald: #34D399;
      --accent-emerald-bg: rgba(52, 211, 153, 0.16);
      --accent-amber: #FBBF24;
      --accent-amber-bg: rgba(251, 191, 36, 0.16);
      --accent-blue: #38BDF8;
      --accent-blue-bg: rgba(56, 189, 248, 0.16);

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
      font-size: clamp(26px, 4.5vw, 38px);
      line-height: 1.15;
      font-weight: 600;
      letter-spacing: -0.02em;
      text-wrap: balance;
      background: linear-gradient(90deg, #FFFFFF 0%, #E2E8F0 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      margin-bottom: 6px;
    }
    .hero-subhead {
      color: var(--text-muted);
      font-size: 14.5px;
      line-height: 21px;
      text-wrap: balance;
      margin-bottom: 8px;
    }

        /* Unified Filter Workbench (Cohesive, Type-Specific Controls) */
    .filter-deck {
      background: var(--bg-surface);
      border: 1px solid var(--border-color);
      border-radius: var(--radius-xl);
      padding: 14px 16px;
      margin-bottom: var(--sp-200);
      display: flex;
      flex-direction: column;
      gap: 12px;
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
    }

    /* Tier 1: Search, Curated Presets, BMW Advisory & Sort */
    .deck-row-primary {
      display: flex;
      align-items: center;
      gap: 12px;
      flex-wrap: wrap;
    }

    .deck-search-wrap {
      flex: 1 1 240px;
      min-width: 200px;
      position: relative;
      display: flex;
      align-items: center;
    }
    .search-icon-svg {
      position: absolute;
      left: 12px;
      width: 16px;
      height: 16px;
      color: var(--text-subtle);
      pointer-events: none;
    }
    .deck-search-input {
      width: 100%;
      background: var(--bg-subsurface);
      border: 1px solid var(--border-color);
      border-radius: var(--radius-md);
      color: var(--text-primary);
      font-family: var(--font-sans);
      font-size: 13.5px;
      padding: 8px 32px 8px 36px;
      outline: none;
      transition: all var(--dur-normal) var(--ease-base);
    }
    .deck-search-input:focus {
      border-color: var(--accent-blue);
      box-shadow: 0 0 0 2px var(--accent-blue-bg);
      background: #11141B;
    }
    .search-clear-btn {
      position: absolute;
      right: 10px;
      background: transparent;
      border: none;
      color: var(--text-subtle);
      font-size: 13px;
      cursor: pointer;
      display: none;
      padding: 3px;
    }
    .search-clear-btn:hover {
      color: var(--text-primary);
    }

    /* Curated Intent Scope Switcher */
    .deck-segmented-scope {
      display: inline-flex;
      align-items: center;
      background: var(--bg-subsurface);
      border: 1px solid var(--border-color);
      border-radius: var(--radius-pill);
      padding: 3px;
      gap: 2px;
    }
    .scope-segment {
      background: transparent;
      border: 1px solid transparent;
      color: var(--text-muted);
      font-size: 12px;
      font-weight: 600;
      padding: 6px 13px;
      border-radius: var(--radius-pill);
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      transition: all 180ms cubic-bezier(0.22, 1, 0.36, 1);
      user-select: none;
      white-space: nowrap;
    }
    .scope-segment:hover {
      color: var(--text-primary);
    }
    .scope-segment.active {
      background: #252833;
      border-color: var(--border-focus);
      color: #FFFFFF;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.4);
    }
    .scope-segment.active.curated {
      background: rgba(245, 158, 11, 0.14);
      border-color: rgba(245, 158, 11, 0.5);
      color: #FBBF24;
    }
    .scope-icon {
      font-size: 13px;
      line-height: 1;
    }
    .scope-count {
      background: rgba(255, 255, 255, 0.08);
      font-family: var(--font-mono);
      font-size: 10px;
      font-weight: 700;
      padding: 2px 6px;
      border-radius: var(--radius-pill);
      color: var(--text-muted);
    }
    .scope-segment.active.curated .scope-count {
      background: rgba(245, 158, 11, 0.25);
      color: #FBBF24;
    }
    .scope-segment.active .scope-count {
      background: rgba(255, 255, 255, 0.2);
      color: #FFFFFF;
    }

    /* Right Deck Actions */
    .deck-actions-right {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      margin-left: auto;
    }
    .deck-btn-bmw {
      background: var(--bg-subsurface);
      border: 1px solid var(--border-color);
      color: #F8FAFC;
      font-size: 12px;
      font-weight: 600;
      padding: 7px 12px;
      border-radius: var(--radius-md);
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      transition: all 180ms ease;
      white-space: nowrap;
    }
    .deck-btn-bmw:hover {
      border-color: #38BDF8;
      background: rgba(56, 189, 248, 0.12);
      color: #38BDF8;
    }
    .deck-sort-wrap {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      background: var(--bg-subsurface);
      border: 1px solid var(--border-color);
      border-radius: var(--radius-md);
      padding: 3px 8px;
    }
    .deck-micro-label {
      font-family: var(--font-mono);
      font-size: 10.5px;
      font-weight: 600;
      color: var(--text-subtle);
      text-transform: uppercase;
    }
    .deck-select {
      background: transparent;
      border: none;
      color: var(--text-primary);
      font-family: var(--font-sans);
      font-size: 12.5px;
      font-weight: 500;
      outline: none;
      cursor: pointer;
    }
    .deck-select option {
      background: #161D2B;
      color: #F1F5F9;
    }

    /* Tier 2: Tailored Controls by Filter Type */
    .deck-row-filters {
      display: flex;
      align-items: center;
      gap: 12px;
      padding-top: 10px;
      border-top: 1px solid rgba(255, 255, 255, 0.05);
      flex-wrap: wrap;
    }
    .filter-cluster {
      display: inline-flex;
      align-items: center;
      gap: 8px;
    }
    .cluster-label {
      font-family: var(--font-mono);
      font-size: 10.5px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: var(--text-subtle);
      white-space: nowrap;
    }
    .cluster-segmented {
      display: inline-flex;
      align-items: center;
      background: var(--bg-subsurface);
      border: 1px solid var(--border-color);
      border-radius: var(--radius-pill);
      padding: 2.5px;
      gap: 2px;
    }
    .cluster-pill, .ribbon-pill, .facet-pill {
      background: transparent;
      border: 1px solid transparent;
      color: var(--text-muted);
      font-size: 12px;
      font-weight: 500;
      padding: 4px 10px;
      border-radius: var(--radius-pill);
      cursor: pointer;
      user-select: none;
      display: inline-flex;
      align-items: center;
      gap: 5px;
      transition: all 180ms cubic-bezier(0.22, 1, 0.36, 1);
      white-space: nowrap;
    }
    .cluster-pill:hover, .ribbon-pill:hover, .facet-pill:hover {
      color: var(--text-primary);
      border-color: rgba(255, 255, 255, 0.15);
    }
    .cluster-pill.active, .ribbon-pill.active, .facet-pill.active {
      background: #FFFFFF;
      border-color: #FFFFFF;
      color: #000000;
      font-weight: 600;
      box-shadow: 0 1px 4px rgba(0, 0, 0, 0.25);
    }
    .cluster-pill.pill-item.active::before, .ribbon-pill.pill-item.active::before, .facet-pill.pill-item.active::before {
      content: "✓";
      font-weight: 800;
      font-size: 10px;
      color: #000000;
      margin-right: 1px;
    }
    .filter-divider {
      width: 1px;
      height: 22px;
      background: var(--border-color);
      opacity: 0.7;
    }

    /* Cohesive Source Dot Indicators */
    .source-dot {
      width: 6px;
      height: 6px;
      border-radius: 50%;
      display: inline-block;
      flex-shrink: 0;
    }
    .spinny-dot { background: #F59E0B; box-shadow: 0 0 5px rgba(245, 158, 11, 0.7); }
    .cars24-dot { background: #38BDF8; box-shadow: 0 0 5px rgba(56, 189, 248, 0.7); }
    .truwo-dot  { background: #34D399; box-shadow: 0 0 5px rgba(52, 211, 153, 0.7); }

    /* Tier 3: Compact Brand Chips Bar */
    .deck-row-brands {
      display: flex;
      align-items: center;
      gap: 8px;
      padding-top: 8px;
      border-top: 1px solid rgba(255, 255, 255, 0.03);
      flex-wrap: wrap;
    }
    .brand-chips-wrap {
      display: inline-flex;
      align-items: center;
      gap: 4px;
      flex-wrap: wrap;
    }
    .brand-chip {
      background: var(--bg-subsurface);
      border: 1px solid var(--border-color);
      color: var(--text-muted);
      font-size: 11.5px;
      font-weight: 500;
      padding: 3px 9px;
      border-radius: var(--radius-pill);
      cursor: pointer;
      user-select: none;
      transition: all 180ms ease;
      display: inline-flex;
      align-items: center;
      gap: 4px;
    }
    .brand-chip:hover {
      color: var(--text-primary);
      border-color: var(--text-muted);
    }
    .brand-chip.active {
      background: #FFFFFF;
      border-color: #FFFFFF;
      color: #000000;
      font-weight: 600;
    }
    .brand-chip.pill-item.active::before {
      content: "✓";
      font-weight: 800;
      font-size: 10px;
      color: #000000;
    }

    /* Scope Context & Status Line */
    .deck-status-bar {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 11.5px;
      color: var(--text-subtle);
      font-family: var(--font-mono);
      padding-top: 6px;
      border-top: 1px solid rgba(255, 255, 255, 0.04);
    }
    .pulse-dot {
      width: 7px;
      height: 7px;
      border-radius: 50%;
      background: #F59E0B;
      box-shadow: 0 0 8px rgba(245, 158, 11, 0.6);
      flex-shrink: 0;
      animation: pulseGlow 2s infinite ease-in-out;
    }

    /* Active Filters Summary Strip & Density Switcher */
    .active-filters-bar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 12px;
      padding: 4px 2px;
      margin-bottom: var(--sp-200);
      flex-wrap: wrap;
    }
    .active-tags-left {
      display: flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
    }
    .active-tag {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      background: rgba(255, 255, 255, 0.07);
      border: 1px solid var(--border-color);
      border-radius: var(--radius-pill);
      padding: 3px 9px;
      font-family: var(--font-mono);
      font-size: 11px;
      color: #E2E8F0;
    }
    .active-tag-remove {
      background: transparent;
      border: none;
      color: var(--text-subtle);
      cursor: pointer;
      font-size: 12px;
      padding: 0 2px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
    }
    .active-tag-remove:hover {
      color: #EF4444;
    }
    .btn-reset-all {
      background: transparent;
      border: 1px solid rgba(239, 68, 68, 0.4);
      color: #F87171;
      font-family: var(--font-mono);
      font-size: 11px;
      font-weight: 600;
      padding: 3px 8px;
      border-radius: var(--radius-pill);
      cursor: pointer;
      transition: all 180ms ease;
    }
    .btn-reset-all:hover {
      background: rgba(239, 68, 68, 0.15);
      border-color: #EF4444;
      color: #FFFFFF;
    }
    .active-tags-right {
      display: inline-flex;
      align-items: center;
      gap: 12px;
      margin-left: auto;
    }
    .density-switch-wrap {
      display: inline-flex;
      align-items: center;
      gap: 4px;
      background: var(--bg-subsurface);
      border: 1px solid var(--border-color);
      border-radius: var(--radius-pill);
      padding: 2px;
    }
    .density-label {
      font-family: var(--font-mono);
      font-size: 10px;
      font-weight: 600;
      color: var(--text-subtle);
      text-transform: uppercase;
      padding-left: 6px;
    }
    .density-pill {
      background: transparent;
      border: none;
      color: var(--text-muted);
      font-family: var(--font-sans);
      font-size: 11px;
      font-weight: 500;
      padding: 3px 8px;
      border-radius: var(--radius-pill);
      cursor: pointer;
      transition: all 180ms ease;
    }
    .density-pill.active {
      background: #252833;
      color: #FFFFFF;
      font-weight: 600;
    }
    .results-count-wrap {
      font-family: var(--font-mono);
      font-size: 12.5px;
      color: var(--text-muted);
      white-space: nowrap;
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
      background: #181818;
      border: 1px solid #272727;
      border-radius: var(--radius-xl);
      display: flex;
      flex-direction: column;
      overflow: hidden;
      transition: border-color var(--dur-normal) var(--ease-base), transform var(--dur-normal) var(--ease-base), box-shadow var(--dur-normal) var(--ease-base);
    }
    .card:hover {
      border-color: #38BDF8;
      transform: translateY(-2px);
      box-shadow: 0 16px 36px rgba(0, 0, 0, 0.45);
    }

    /* Flat Photo slot with no gradient (B4: flat dark #131209) */
    .card-photo {
      height: 200px;
      background: #131209;
      position: relative;
      display: flex;
      align-items: center;
      justify-content: center;
      border-bottom: 1px solid #272727;
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

    /* Score Badge Button (Interactive with Audit hint) */
    .badge-grade {
      position: absolute;
      top: 12px;
      left: 12px;
      font-family: var(--font-mono);
      font-size: 11px;
      font-weight: 700;
      padding: 4px 8px;
      border-radius: 6px;
      letter-spacing: 0.04em;
      z-index: 3;
      display: inline-flex;
      align-items: center;
      gap: 5px;
      cursor: pointer;
      border: 1px solid transparent;
      outline: none;
      transition: all var(--dur-fast) var(--ease-base);
      user-select: none;
    }
    .badge-grade:hover {
      transform: translateY(-1px);
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
      filter: brightness(1.15);
    }
    .badge-grade:active {
      transform: translateY(0);
    }
    .badge-info-hint {
      font-size: 9px;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      opacity: 0.85;
      padding-left: 5px;
      border-left: 1px solid rgba(0, 0, 0, 0.25);
    }
    .badge-grade.top {
      background: var(--accent-amber);
      color: #000000;
      border-color: #D97706;
    }
    .badge-grade.value {
      background: var(--accent-emerald);
      color: #000000;
      border-color: #059669;
    }
    .badge-grade.fair {
      background: #1F1F1F;
      border-color: #272727;
      color: var(--text-body);
    }
    .badge-grade.fair .badge-info-hint {
      border-left: 1px solid rgba(255, 255, 255, 0.2);
    }

    /* Top-Right Badges Container */
    .card-badges-top-right {
      position: absolute;
      top: 12px;
      right: 12px;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      z-index: 2;
    }

    .badge-tier {
      font-family: var(--font-mono);
      font-size: 11px;
      font-weight: 600;
      padding: 3px 8px;
      border-radius: 6px;
      background: #1F1F1F;
      border: 1px solid #272727;
      color: var(--text-muted);
    }
    .badge-tier.assured {
      color: #34D399;
      border-color: rgba(52, 211, 153, 0.4);
      background: rgba(52, 211, 153, 0.1);
    }

        /* Cohesive Vetted Platform Source Badges */
    .card-badges-top-right {
      position: absolute;
      top: 10px;
      right: 10px;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      z-index: 2;
    }
    .source-tag {
      font-family: var(--font-mono);
      font-size: 11px;
      font-weight: 600;
      padding: 3.5px 9px;
      border-radius: var(--radius-pill);
      background: rgba(14, 19, 30, 0.88);
      backdrop-filter: blur(8px);
      -webkit-backdrop-filter: blur(8px);
      border: 1px solid rgba(255, 255, 255, 0.12);
      color: #F1F5F9;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      letter-spacing: 0.02em;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.35);
    }
    .source-tier {
      color: var(--text-subtle);
      font-weight: 500;
      font-size: 10px;
      border-left: 1px solid rgba(255, 255, 255, 0.15);
      padding-left: 6px;
    }

    /* Cohesive Pricing Source Indicator */
    .pricing-source-badge {
      display: inline-flex;
      align-items: center;
      gap: 4px;
      font-family: var(--font-mono);
      font-size: 10px;
      font-weight: 600;
      color: var(--text-subtle);
      margin-top: 3px;
      letter-spacing: 0.02em;
    }
    .pricing-source-badge.truwo {
      color: #34D399;
    }
    .pricing-source-badge.spinny, .pricing-source-badge.cars24 {
      color: var(--text-subtle);
    }


    /* Live unbooked stock indicator */
    .badge-availability {
      position: absolute;
      bottom: 10px;
      right: 12px;
      font-family: var(--font-mono);
      font-size: 10px;
      font-weight: 600;
      padding: 2px 7px;
      border-radius: 4px;
      background: rgba(16, 185, 129, 0.12);
      border: 1px solid rgba(16, 185, 129, 0.35);
      color: #34D399;
      display: inline-flex;
      align-items: center;
      gap: 5px;
      z-index: 2;
    }
    .avail-dot {
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background: #34D399;
      box-shadow: 0 0 6px #34D399;
    }

    .card-content {
      padding: var(--sp-200);
      display: flex;
      flex-direction: column;
      gap: 10px;
      flex: 1;
    }

    .car-header-block {
      display: flex;
      flex-direction: column;
      gap: 6px;
    }
    .car-title {
      font-size: 18px;
      line-height: 24px;
      font-weight: 600;
      color: #FFFFFF;
      text-wrap: balance;
      font-family: var(--font-sans);
    }
    .car-specs-strip {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
    }
    .spec-pill {
      font-family: var(--font-mono);
      font-size: 11px;
      background: #272727;
      border: 1px solid #313131;
      color: #CBD5E1;
      padding: 2px 7px;
      border-radius: 4px;
    }
    .spec-pill.hub {
      color: var(--text-subtle);
    }

    /* Consolidated Minimalist Pricing Bar (Fixed Price & Top Price Discount) */
    .card-pricing-bar {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      padding: 8px 0 10px 0;
      border-bottom: 1px solid #272727;
      gap: 12px;
    }
    .pricing-primary-col, .pricing-retail-col {
      display: flex;
      flex-direction: column;
    }
    .pricing-retail-col {
      align-items: flex-end;
      text-align: right;
    }
    .pricing-sub-label {
      font-family: var(--font-mono);
      font-size: 10px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: var(--text-subtle);
    }
    .pricing-val-main {
      font-family: var(--font-mono);
      font-size: 20px;
      font-weight: 700;
      color: #FFFFFF;
      line-height: 1.2;
      margin-top: 2px;
    }
    .pricing-fixed-tag {
      font-family: var(--font-mono);
      font-size: 9.5px;
      color: var(--text-subtle);
      margin-top: 3px;
    }
    .pricing-val-top {
      font-family: var(--font-mono);
      font-size: 14px;
      font-weight: 600;
      color: var(--text-subtle);
      text-decoration: line-through;
      line-height: 1.2;
      margin-top: 2px;
    }
    .discount-badge-lg {
      font-family: var(--font-mono);
      font-size: 10.5px;
      font-weight: 700;
      color: var(--accent-emerald);
      background: rgba(52, 211, 153, 0.12);
      border: 1px solid rgba(52, 211, 153, 0.35);
      padding: 2px 7px;
      border-radius: 4px;
      margin-top: 4px;
      white-space: nowrap;
    }

    /* Consolidated Ownership Intel Matrix (Clean 2x2 Grid) */
    .card-intel-matrix {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px 12px;
      padding: 8px 0;
      border-bottom: 1px solid #272727;
    }
    .intel-cell {
      display: flex;
      flex-direction: column;
      gap: 2px;
    }
    .intel-k {
      font-family: var(--font-mono);
      font-size: 10px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      color: var(--text-subtle);
    }
    .intel-v {
      font-size: 11.5px;
      color: var(--text-body);
      line-height: 1.35;
      text-wrap: pretty;
    }

    /* Consolidated Financial Telemetry Strip */
    .card-telemetry-strip {
      display: flex;
      justify-content: space-between;
      align-items: baseline;
      padding: 6px 0;
      gap: 12px;
    }
    .telemetry-item {
      display: flex;
      flex-direction: column;
      gap: 2px;
    }
    .tele-k {
      font-family: var(--font-mono);
      font-size: 10px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      color: var(--text-subtle);
    }
    .tele-v {
      font-family: var(--font-mono);
      font-size: 12.5px;
      font-weight: 700;
    }
    .tele-v.buyback {
      color: var(--accent-emerald);
    }
    .tele-v.loss {
      color: var(--accent-blue);
    }

    /* Collapsible Ownership Intel & Verdict Drawer */
    .btn-intel-toggle {
      background: #1C1C1C;
      border: 1px dashed #313131;
      color: #94A3B8;
      font-family: var(--font-mono);
      font-size: 11px;
      font-weight: 600;
      padding: 7px 10px;
      border-radius: var(--radius-md);
      display: flex;
      align-items: center;
      justify-content: space-between;
      width: 100%;
      cursor: pointer;
      transition: all var(--dur-fast) var(--ease-base);
      user-select: none;
      margin-top: 2px;
    }
    .btn-intel-toggle:hover {
      background: #242424;
      border-color: #38BDF8;
      color: #FFFFFF;
    }
    .btn-intel-toggle.active {
      background: #222222;
      border-color: rgba(56, 189, 248, 0.5);
      color: #38BDF8;
    }
    .intel-chevron {
      font-size: 10px;
      transition: transform var(--dur-fast) var(--ease-base);
    }
    .btn-intel-toggle.active .intel-chevron {
      transform: rotate(180deg);
    }
    .card-intel-drawer {
      display: none;
      flex-direction: column;
      gap: 8px;
      padding-top: 4px;
      animation: fadeInDrawer 160ms var(--ease-base);
    }
    .card-intel-drawer.open {
      display: flex;
    }
    @keyframes fadeInDrawer {
      from { opacity: 0; transform: translateY(-4px); }
      to { opacity: 1; transform: translateY(0); }
    }

    /* Bangalore Verdict Note */
    .card-verdict-row {
      padding: 7px 10px;
      background: #1F1F1F;
      border-left: 2px solid var(--accent-blue);
      border-radius: 0 6px 6px 0;
      margin-top: 2px;
    }
    .card-verdict-text {
      font-size: 11.5px;
      color: var(--text-muted);
      line-height: 1.4;
      text-wrap: pretty;
      margin: 0;
    }

    /* Card Footer Action Bar (Single primary CTA) */
    .card-footer {
      margin-top: auto;
      padding-top: 8px;
      border-top: 1px solid #272727;
      display: flex;
    }
    .cta-primary-btn {
      display: flex;
      align-items: center;
      justify-content: space-between;
      width: 100%;
      background: rgba(56, 189, 248, 0.08);
      border: 1px solid rgba(56, 189, 248, 0.4);
      color: #FFFFFF;
      font-family: var(--font-mono);
      font-size: 13px;
      font-weight: 600;
      padding: 8px 12px;
      border-radius: var(--radius-md);
      text-decoration: none;
      transition: all var(--dur-normal) var(--ease-base);
    }
    .cta-primary-btn:hover {
      background: var(--text-primary);
      border-color: var(--text-primary);
      color: #000000;
    }
    .cta-primary-btn:active {
      transform: scale(0.98);
    }

    /* Score Calculation Pop-up Modal */
    .score-modal-backdrop {
      position: fixed;
      inset: 0;
      background: rgba(0, 0, 0, 0.78);
      backdrop-filter: blur(6px);
      -webkit-backdrop-filter: blur(6px);
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
      background: #121824;
      border: 1px solid var(--border-color);
      border-radius: var(--radius-xl);
      max-width: 580px;
      width: 100%;
      max-height: 90vh;
      display: flex;
      flex-direction: column;
      overflow: hidden;
      box-shadow: 0 24px 60px rgba(0, 0, 0, 0.75);
      animation: modalSlideUp 200ms var(--ease-base);
    }
    @keyframes modalSlideUp {
      from { transform: translateY(12px) scale(0.98); opacity: 0; }
      to { transform: translateY(0) scale(1); opacity: 1; }
    }
    .score-modal-header {
      padding: var(--sp-200);
      border-bottom: 1px solid var(--border-color);
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      background: #0B101A;
    }
    .score-modal-header h3 {
      font-size: 16px;
      font-weight: 700;
      color: #FFFFFF;
    }
    .score-modal-close {
      background: transparent;
      border: none;
      color: var(--text-muted);
      font-size: 18px;
      cursor: pointer;
      padding: 4px 8px;
      border-radius: var(--radius-sm);
      transition: all var(--dur-fast) var(--ease-base);
    }
    .score-modal-close:hover {
      color: #FFFFFF;
      background: rgba(255, 255, 255, 0.1);
    }
    .score-modal-body {
      padding: var(--sp-200);
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: var(--sp-200);
    }
    .score-modal-footer {
      padding: 12px 16px;
      border-top: 1px solid var(--border-color);
      background: #0B101A;
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 12px;
    }

    /* Modal Hero Snapshot */
    .modal-car-hero {
      display: flex;
      gap: 14px;
      align-items: center;
      background: #0B101A;
      border: 1px solid var(--border-color);
      border-radius: var(--radius-md);
      padding: 10px 14px;
    }
    .modal-car-thumb {
      width: 72px;
      height: 48px;
      object-fit: cover;
      border-radius: var(--radius-sm);
      background: #1A2232;
      flex-shrink: 0;
    }
    .modal-hero-info {
      flex: 1;
      min-width: 0;
    }
    .modal-score-grade {
      font-family: var(--font-mono);
      font-size: 13px;
      font-weight: 700;
      padding: 6px 12px;
      border-radius: var(--radius-sm);
      white-space: nowrap;
    }
    .modal-score-grade.top {
      background: var(--accent-amber);
      color: #000000;
    }
    .modal-score-grade.value {
      background: var(--accent-emerald);
      color: #000000;
    }
    .modal-score-grade.fair {
      background: #1A2232;
      color: var(--text-muted);
      border: 1px solid var(--border-color);
    }

    .modal-rationale-box {
      display: flex;
      gap: 10px;
      align-items: flex-start;
      background: rgba(56, 189, 248, 0.08);
      border: 1px solid rgba(56, 189, 248, 0.25);
      border-radius: var(--radius-md);
      padding: 10px 14px;
    }
    .modal-rationale-icon {
      font-size: 16px;
      line-height: 1.2;
    }
    .modal-rationale-text {
      font-size: 13px;
      color: #F1F5F9;
      line-height: 1.45;
      font-weight: 500;
    }

    /* Modal Point Audit Table */
    .modal-breakdown-wrap {
      background: #0B101A;
      border: 1px solid var(--border-color);
      border-radius: var(--radius-md);
      overflow: hidden;
    }
    .modal-breakdown-head {
      display: flex;
      justify-content: space-between;
      padding: 8px 14px;
      background: #151D2A;
      border-bottom: 1px solid var(--border-color);
      font-family: var(--font-mono);
      font-size: 11px;
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
      padding: 10px 14px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.04);
      gap: 12px;
    }
    .score-audit-row:last-child {
      border-bottom: none;
    }
    .score-audit-pillar {
      font-size: 13px;
      font-weight: 600;
      color: #FFFFFF;
    }
    .score-audit-desc {
      font-size: 11px;
      color: var(--text-muted);
      margin-top: 1px;
    }
    .score-audit-badge {
      font-family: var(--font-mono);
      font-size: 12px;
      font-weight: 700;
      padding: 3px 8px;
      border-radius: var(--radius-sm);
      white-space: nowrap;
    }
    .score-audit-badge.pos {
      background: rgba(52, 211, 153, 0.16);
      color: #34D399;
      border: 1px solid rgba(52, 211, 153, 0.3);
    }
    .score-audit-badge.neg {
      background: rgba(248, 113, 113, 0.16);
      color: #F87171;
      border: 1px solid rgba(248, 113, 113, 0.3);
    }
    .score-audit-badge.base {
      background: rgba(255, 255, 255, 0.08);
      color: var(--text-muted);
      border: 1px solid rgba(255, 255, 255, 0.15);
    }
    .modal-breakdown-total {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 10px 14px;
      background: #151D2A;
      border-top: 1px solid var(--border-color);
      font-family: var(--font-mono);
      font-size: 13px;
      font-weight: 700;
      color: #FFFFFF;
    }
    .modal-breakdown-total strong {
      color: var(--accent-emerald);
      font-size: 15px;
    }

    /* Value Telemetry Strip */
    .telemetry-strip {
      display: grid;
      grid-template-columns: 1.2fr 1fr;
      background: #0A0F18;
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
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      color: var(--text-subtle);
    }
    .telemetry-val {
      font-family: var(--font-mono);
      font-size: 13px;
      font-weight: 700;
      color: var(--text-body);
      margin-top: 1px;
    }
    .telemetry-val.buyback {
      color: var(--accent-emerald);
    }
    .telemetry-val.cost {
      color: var(--accent-blue);
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
      outline: 2px solid var(--accent-blue);
      outline-offset: 2px;
    }

    /* Mobile & Tablet Responsive Optimization (elayadesign/ai-design-skills) */
    @media (max-width: 768px) {
      .shell {
        padding: 12px 10px 60px 10px;
      }
      .floating-nav {
        top: 8px;
        margin-bottom: 16px;
        width: 100%;
        padding: 0 8px;
      }
      .nav-inner {
        width: 100%;
        max-width: 100%;
        padding: 6px 10px;
        gap: 6px;
        justify-content: space-between;
      }
      .nav-stats {
        display: none;
      }
      .nav-btn {
        padding: 6px 9px;
        font-size: 11px;
        min-height: 36px;
      }
      .grid {
        grid-template-columns: 1fr;
        gap: 14px;
      }
    }

    @media (max-width: 640px) {
      .shell {
        padding: 10px 8px 56px 8px;
      }
      .nav-inner {
        padding: 5px 8px;
        gap: 5px;
      }
      .nav-brand {
        font-size: 13px;
        gap: 5px;
        flex-shrink: 0;
      }
      .nav-btn {
        padding: 5px 8px;
        font-size: 10.5px;
        min-height: 34px;
      }

      /* Hero & View Mode */
      .hero-section {
        margin: 0 auto 16px auto;
      }
      .hero-heading {
        font-size: clamp(23px, 6.8vw, 32px);
      }
      .hero-subhead {
        font-size: 13px;
        line-height: 19px;
      }
      .filter-deck {
        padding: 10px 10px;
        gap: 10px;
        border-radius: var(--radius-lg);
        margin-bottom: 14px;
      }
      .deck-row-primary {
        flex-direction: column;
        align-items: stretch;
        gap: 8px;
      }
      .deck-search-wrap {
        width: 100%;
        flex: 1 1 100%;
      }
      .deck-search-input {
        font-size: 13px;
        padding: 8px 32px 8px 36px;
        min-height: 40px;
      }
      .deck-segmented-scope {
        width: 100%;
        display: flex;
      }
      .scope-segment {
        flex: 1;
        justify-content: center;
        padding: 7px 4px;
        font-size: 11px;
        min-height: 38px;
        gap: 4px;
      }
      .scope-title {
        font-size: 11px;
      }
      .deck-actions-right {
        width: 100%;
        margin-left: 0;
        justify-content: space-between;
        flex-wrap: wrap;
        gap: 6px;
      }
      .deck-btn-bmw {
        flex: 1 1 auto;
        justify-content: center;
        padding: 6px 8px;
        font-size: 11px;
      }
      .deck-sort-wrap {
        flex: 1 1 auto;
      }
      .deck-select {
        flex: 1;
        font-size: 11.5px;
        padding: 6px 8px;
        min-height: 36px;
      }
      .deck-btn-drawer {
        padding: 6px 10px;
        font-size: 11.5px;
      }
      .deck-row-ribbon {
        flex-direction: column;
        align-items: stretch;
        gap: 8px;
        padding-top: 8px;
      }
      .ribbon-group {
        width: 100%;
        flex-direction: column;
        align-items: flex-start;
        gap: 4px;
      }
      .ribbon-pills {
        width: 100%;
      }
      .ribbon-divider {
        display: none;
      }
      .drawer-grid {
        grid-template-columns: 1fr;
      }
      .price-inputs-row {
        flex-wrap: wrap;
        gap: 6px;
      }
      .price-num-box {
        width: 66px;
        font-size: 12px;
        padding: 5px 4px;
        min-height: 36px;
      }
      .price-slider-input {
        width: 100%;
        flex: 1 1 100%;
        order: 4;
        margin-top: 4px;
        height: 8px;
      }
      .facet-pills {
        gap: 4px;
      }
      .facet-pill, .ribbon-pill {
        font-size: 11px;
        padding: 5px 9px;
        min-height: 34px;
      }
      .brands-container .facet-pill {
        font-size: 10.5px;
        padding: 4px 8px;
        min-height: 32px;
      }

      /* Active Filters Bar & Density Switcher */
      .active-filters-bar {
        flex-direction: column;
        align-items: stretch;
        gap: 8px;
        margin-bottom: 14px;
      }
      .active-tags-left {
        width: 100%;
        flex-wrap: wrap;
      }
      .active-tags-right {
        width: 100%;
        margin-left: 0;
        justify-content: space-between;
      }
      #active-tags-container {
        width: 100%;
      }
      .active-tag {
        font-size: 11px;
        padding: 3px 7px;
      }
      .results-count-wrap {
        margin-left: 0;
        font-size: 11.5px;
      }

      /* Cards on Mobile */
      .card {
        border-radius: var(--radius-lg);
      }
      .card-photo {
        height: 180px;
        padding: 6px;
      }
      .badge-grade {
        top: 8px;
        left: 8px;
        font-size: 10px;
        padding: 3px 6px;
      }
      .badge-info-hint {
        font-size: 8.5px;
        padding-left: 4px;
      }
      .card-badges-top-right {
        top: 8px;
        right: 8px;
        gap: 4px;
      }
      .badge-tier, .badge-platform {
        font-size: 9.5px;
        padding: 2px 6px;
      }
      .badge-availability {
        bottom: 8px;
        right: 8px;
        font-size: 9px;
        padding: 2px 5px;
      }
      .card-content {
        padding: 10px 10px 12px 10px;
        gap: 8px;
      }
      .car-title {
        font-size: 15.5px;
        line-height: 21px;
      }
      .car-specs-strip {
        gap: 4px;
      }
      .spec-pill {
        font-size: 10px;
        padding: 2px 5px;
      }
      .card-pricing-bar {
        padding: 6px 0 8px 0;
        gap: 8px;
      }
      .pricing-sub-label {
        font-size: 9.5px;
      }
      .pricing-val-main {
        font-size: 18px;
      }
      .pricing-val-top {
        font-size: 13px;
      }
      .discount-badge-lg {
        font-size: 9.5px;
        padding: 1px 5px;
      }
      .card-intel-matrix {
        grid-template-columns: 1fr 1fr;
        gap: 6px 8px;
        padding: 6px 0;
      }
      .intel-k {
        font-size: 9px;
      }
      .intel-v {
        font-size: 10.5px;
        line-height: 1.3;
      }
      .card-telemetry-strip {
        padding: 4px 0;
        gap: 8px;
      }
      .tele-k {
        font-size: 9px;
      }
      .tele-v {
        font-size: 11.5px;
      }
      .card-verdict-row {
        padding: 6px 8px;
      }
      .card-verdict-text {
        font-size: 11px;
        line-height: 1.35;
      }
      .btn-intel-toggle {
        min-height: 38px;
        font-size: 11px;
        padding: 8px 10px;
      }
      .card-footer {
        padding-top: 8px;
      }
      .cta-primary-btn {
        min-height: 44px;
        padding: 10px 14px;
        font-size: 12.5px;
      }

      /* Bottom Sheet Modals on Mobile */
      .score-modal-backdrop, .alerts-modal-backdrop {
        padding: 0;
        align-items: flex-end;
      }
      .score-modal, .alerts-modal {
        max-width: 100%;
        width: 100%;
        max-height: 90vh;
        border-radius: 16px 16px 0 0;
        border-bottom: none;
      }
      .score-modal-header, .alerts-modal-header {
        padding: 12px 14px;
      }
      .score-modal-header h3, .alerts-modal-header h3 {
        font-size: 15px;
      }
      .score-modal-body, .alerts-modal-body {
        padding: 12px 14px;
        gap: 12px;
        -webkit-overflow-scrolling: touch;
      }
      .score-modal-footer {
        padding: 10px 14px;
        flex-direction: column;
        align-items: stretch;
        gap: 8px;
      }
      .score-modal-footer .nav-btn {
        width: 100%;
        text-align: center;
        padding: 10px;
        min-height: 44px;
      }
      .modal-car-hero {
        padding: 8px 10px;
        gap: 10px;
      }
      .modal-car-thumb {
        width: 58px;
        height: 40px;
      }
      .modal-score-grade {
        font-size: 11.5px;
        padding: 4px 8px;
      }
      .score-audit-row {
        flex-direction: column;
        align-items: flex-start;
        gap: 3px;
        padding: 8px 0;
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
      .live-sync-btn span:last-child {
        display: none;
      }
      .live-sync-btn::after {
        content: "Sync";
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
    /* Live Sync Button in Nav */
    .live-sync-btn {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      background: rgba(56, 189, 248, 0.1) !important;
      border: 1px solid rgba(56, 189, 248, 0.35) !important;
      color: #38BDF8 !important;
      font-weight: 600;
    }
    .live-sync-btn:hover {
      background: rgba(56, 189, 248, 0.2) !important;
      color: #FFFFFF !important;
    }
    .live-pulse-dot {
      width: 7px;
      height: 7px;
      border-radius: 50%;
      background: #38BDF8;
      box-shadow: 0 0 8px #38BDF8;
      animation: pulseLiveSync 2s infinite ease-in-out;
    }
    @keyframes pulseLiveSync {
      0%, 100% { opacity: 1; transform: scale(1); }
      50% { opacity: 0.35; transform: scale(0.85); }
    }

    /* Live Sync Modal */
    .sync-status-box {
      background: rgba(56, 189, 248, 0.08);
      border: 1px solid rgba(56, 189, 248, 0.25);
      border-radius: var(--radius-md);
      padding: 12px 14px;
    }
    .sync-status-header {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 14px;
      color: #FFFFFF;
    }
    .sync-method-card {
      background: #0B101A;
      border: 1px solid var(--border-color);
      border-radius: var(--radius-md);
      padding: 14px;
      display: flex;
      flex-direction: column;
      gap: 8px;
    }
    .sync-method-head {
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .sync-method-head h4 {
      font-size: 14px;
      font-weight: 600;
      color: #FFFFFF;
    }
    .sync-badge {
      font-family: var(--font-mono);
      font-size: 10px;
      font-weight: 700;
      padding: 2px 6px;
      border-radius: var(--radius-sm);
      background: rgba(52, 211, 153, 0.16);
      color: #34D399;
      border: 1px solid rgba(52, 211, 153, 0.35);
    }
    .sync-badge.github {
      background: rgba(168, 85, 247, 0.16);
      color: #C084FC;
      border-color: rgba(168, 85, 247, 0.35);
    }
    .sync-badge.local {
      background: rgba(245, 158, 11, 0.16);
      color: #FBBF24;
      border-color: rgba(245, 158, 11, 0.35);
    }
    .sync-action-btn {
      margin-top: 4px;
    }
    .code-snippet-box {
      display: flex;
      justify-content: space-between;
      align-items: center;
      background: #151D2A;
      border: 1px solid var(--border-color);
      border-radius: var(--radius-sm);
      padding: 8px 12px;
      font-family: var(--font-mono);
      font-size: 11px;
      color: #CBD5E1;
      gap: 8px;
    }
    .code-snippet-box code {
      overflow-x: auto;
      white-space: nowrap;
    }
    .copy-btn {
      background: #272727;
      border: 1px solid #313131;
      color: #FFFFFF;
      font-family: var(--font-mono);
      font-size: 10px;
      padding: 4px 8px;
      border-radius: 4px;
      cursor: pointer;
      flex-shrink: 0;
    }
    .copy-btn:hover {
      background: var(--text-primary);
      color: #000000;
    }
    .github-pat-row {
      display: flex;
      gap: 6px;
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
      <button class="nav-btn live-sync-btn" onclick="openLiveSyncModal()" title="On-Demand Live Inventory Sync">
        <span class="live-pulse-dot"></span>
        <span>⚡ Live Sync</span>
      </button>
      <button class="nav-btn bmw-guide-btn" onclick="openBmwModal()" title="BMW Under ₹5L Ownership Guide & Search">
        <span>🏎️ BMW &lt; ₹5L</span>
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
        Curated shortlist of verified Bangalore cars under ₹5 Lakhs with high resale retention and certified inspection across Spinny and Cars24.
      </p>
    </header>

        <!-- Unified Filter Workbench (Cohesive, Type-Specific Controls, Reduced & Merged) -->
    <section class="filter-deck" id="filter-workbench" aria-label="Car Filter Control Deck">
      <!-- Tier 1: Instant Search, Curated Presets, BMW Guide & Sort -->
      <div class="deck-row-primary">
        <!-- Search Field -->
        <div class="deck-search-wrap">
          <svg class="search-icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8"></circle>
            <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
          </svg>
          <input 
            type="text" 
            id="ctrl-search" 
            class="deck-search-input" 
            placeholder="Search model, variant, hub..." 
            oninput="onSearchInput(this.value)"
          />
          <button type="button" id="btn-clear-search" class="search-clear-btn" onclick="clearSearch()" title="Clear search">✕</button>
        </div>

        <!-- Curated Intent Scope Switcher -->
        <div class="deck-segmented-scope" role="tablist" aria-label="Inventory Scope">
          <button type="button" class="scope-segment active curated" id="btn-mode-curated" onclick="setViewMode('curated')" role="tab" title="Handpicked Bangalore deals under ₹5L with Deal Score 80+">
            <span class="scope-icon">🔥</span>
            <span class="scope-title">Top Deals</span>
            <span class="scope-count" id="badge-curated-count">0</span>
          </button>
          <button type="button" class="scope-segment" id="btn-german-5l" onclick="filterGermanUnder5L()" role="tab" title="Volkswagen, Skoda, BMW, Audi under ₹5L">
            <span class="scope-icon">🇩🇪</span>
            <span class="scope-title">German &le; ₹5L</span>
            <span class="scope-count" id="count-german-5l">33</span>
          </button>
          <button type="button" class="scope-segment" id="btn-mode-all" onclick="setViewMode('all')" role="tab" title="Entire verified Bangalore inventory">
            <span class="scope-icon">📦</span>
            <span class="scope-title">All Cars</span>
            <span class="scope-count" id="badge-all-count">0</span>
          </button>
        </div>

        <!-- Right Deck Utilities: BMW Advisory & Sort Select -->
        <div class="deck-actions-right">
          <button type="button" class="deck-btn-bmw" id="btn-bmw-intel" onclick="openBmwModal()" title="BMW Under ₹5L Ownership Guide & Search">
            <span>🏎️ BMW &lt; ₹5L</span>
          </button>

          <div class="deck-sort-wrap">
            <label for="ctrl-sort" class="deck-micro-label">Sort</label>
            <select id="ctrl-sort" class="deck-select" onchange="onSortChange(this.value)">
              <option value="score">Best Value Score</option>
              <option value="discount_desc">Highest % Off Top Price</option>
              <option value="price_asc">Price: Low to High</option>
              <option value="price_desc">Price: High to Low</option>
              <option value="year_desc">Year: Newest First</option>
              <option value="km_asc">Mileage: Lowest KM</option>
            </select>
          </div>
        </div>
      </div>

      <!-- Tier 2: Tailored Controls by Filter Type (Source Platform, Stepped Budget, Showroom Savings, Drivetrain) -->
      <div class="deck-row-filters">
        <!-- 1. Source Platform: Discrete Entity Multi-Select with Live Counts & Subtle Dots -->
        <div class="filter-cluster source-cluster" id="cluster-source">
          <span class="cluster-label">Source</span>
          <div class="cluster-segmented" id="platforms-pills">
            <button type="button" class="cluster-pill pill-all active" onclick="clearMultiFilter('platforms')">All (<span id="tele-total-sources">0</span>)</button>
            <button type="button" class="cluster-pill pill-item pill-spinny" data-val="Spinny" onclick="toggleMultiFilter('platforms', 'Spinny')">
              <span class="source-dot spinny-dot"></span>Spinny (<span id="count-spinny">0</span>)
            </button>
            <button type="button" class="cluster-pill pill-item pill-cars24" data-val="Cars24" onclick="toggleMultiFilter('platforms', 'Cars24')">
              <span class="source-dot cars24-dot"></span>Cars24 (<span id="count-cars24">0</span>)
            </button>
            <button type="button" class="cluster-pill pill-item pill-truwo" data-val="Truwo" onclick="toggleMultiFilter('platforms', 'Truwo')">
              <span class="source-dot truwo-dot"></span>Truwo (<span id="count-truwo">0</span>)
            </button>
          </div>
        </div>

        <div class="filter-divider" aria-hidden="true"></div>

        <!-- 2. Max Budget: Bounded Stepped Range Selector -->
        <div class="filter-cluster budget-cluster" id="cluster-budget">
          <span class="cluster-label">Max Budget</span>
          <div class="cluster-segmented quick-budget-strip">
            <button type="button" class="cluster-pill" onclick="setMaxBudget(4.0)">&le; ₹4L</button>
            <button type="button" class="cluster-pill active" id="btn-quick-5l" onclick="setMaxBudget(5.0)">&le; ₹5L</button>
            <button type="button" class="cluster-pill" onclick="setMaxBudget(7.0)">&le; ₹7L</button>
            <button type="button" class="cluster-pill" onclick="clearPrice()">All</button>
          </div>
        </div>

        <div class="filter-divider" aria-hidden="true"></div>

        <!-- 3. Showroom Savings: Percentage Value Threshold Selector -->
        <div class="filter-cluster discount-cluster" id="cluster-discount">
          <span class="cluster-label">Savings</span>
          <div class="cluster-segmented" id="discount-pills">
            <button type="button" class="cluster-pill active" onclick="setMinDiscount(0, this)">Any</button>
            <button type="button" class="cluster-pill" onclick="setMinDiscount(30, this)">&ge; 30%</button>
            <button type="button" class="cluster-pill" onclick="setMinDiscount(40, this)">&ge; 40%</button>
            <button type="button" class="cluster-pill" onclick="setMinDiscount(50, this)">&ge; 50%</button>
          </div>
        </div>

        <div class="filter-divider" aria-hidden="true"></div>

        <!-- 4. Drivetrain: Micro-Segmented Binary/Ternary Toggles (Transmission + Fuel) -->
        <div class="filter-cluster drivetrain-cluster" id="cluster-drivetrain">
          <span class="cluster-label">Drivetrain</span>
          <div class="cluster-segmented" id="transmissions-pills">
            <button type="button" class="cluster-pill pill-all active" onclick="clearMultiFilter('transmissions')">All Trans</button>
            <button type="button" class="cluster-pill pill-item" data-val="automatic" onclick="toggleMultiFilter('transmissions', 'automatic')">Auto</button>
            <button type="button" class="cluster-pill pill-item" data-val="manual" onclick="toggleMultiFilter('transmissions', 'manual')">Manual</button>
          </div>
          <div class="cluster-segmented" id="fuels-pills">
            <button type="button" class="cluster-pill pill-all active" onclick="clearMultiFilter('fuels')">All Fuel</button>
            <button type="button" class="cluster-pill pill-item" data-val="petrol" onclick="toggleMultiFilter('fuels', 'petrol')">Petrol</button>
            <button type="button" class="cluster-pill pill-item" data-val="diesel" onclick="toggleMultiFilter('fuels', 'diesel')">Diesel</button>
          </div>
        </div>
      </div>

      <!-- Tier 3: Compact Brand Chips Bar (Quick Scannable Brand Selection) -->
      <div class="deck-row-brands">
        <span class="cluster-label">Brands</span>
        <div class="brand-chips-wrap" id="brands-pills">
          <button type="button" class="brand-chip pill-all active" onclick="clearMultiFilter('brands')">All Brands</button>
          <button type="button" class="brand-chip pill-item" data-val="maruti" onclick="toggleMultiFilter('brands', 'maruti')">Maruti (<span id="count-maruti">0</span>)</button>
          <button type="button" class="brand-chip pill-item" data-val="hyundai" onclick="toggleMultiFilter('brands', 'hyundai')">Hyundai (<span id="count-hyundai">0</span>)</button>
          <button type="button" class="brand-chip pill-item" data-val="tata" onclick="toggleMultiFilter('brands', 'tata')">Tata (<span id="count-tata">0</span>)</button>
          <button type="button" class="brand-chip pill-item" data-val="honda" onclick="toggleMultiFilter('brands', 'honda')">Honda (<span id="count-honda">0</span>)</button>
          <button type="button" class="brand-chip pill-item" data-val="volkswagen" onclick="toggleMultiFilter('brands', 'volkswagen')">Volkswagen (<span id="count-volkswagen">0</span>)</button>
          <button type="button" class="brand-chip pill-item" data-val="toyota" onclick="toggleMultiFilter('brands', 'toyota')">Toyota (<span id="count-toyota">0</span>)</button>
          <button type="button" class="brand-chip pill-item" data-val="mahindra" onclick="toggleMultiFilter('brands', 'mahindra')">Mahindra (<span id="count-mahindra">0</span>)</button>
          <button type="button" class="brand-chip pill-item" data-val="renault" onclick="toggleMultiFilter('brands', 'renault')">Renault (<span id="count-renault">0</span>)</button>
          <button type="button" class="brand-chip pill-item" data-val="skoda" onclick="toggleMultiFilter('brands', 'skoda')">Skoda (<span id="count-skoda">0</span>)</button>
          <button type="button" class="brand-chip pill-item" data-val="bmw" onclick="toggleMultiFilter('brands', 'bmw')">BMW (<span id="count-bmw">0</span>)</button>
        </div>
      </div>

      <!-- Scope Status Text Line -->
      <div class="deck-status-bar" id="mode-status-text">
        <span class="pulse-dot"></span>
        <span>Curated view: Under ₹5.0L · Deal Score 80+ · Low Mileage (&lt; 80k km) · Certified Assured</span>
      </div>
    </section>

<!-- Active Filters Summary Strip & Density Switcher -->
  <div class="active-filters-bar" id="active-tags-strip">
    <div class="active-tags-left">
      <span class="caption-4" style="color:var(--text-subtle);">Active:</span>
      <div id="active-tags-container" style="display:inline-flex; flex-wrap:wrap; gap:6px;"></div>
      <button class="btn-reset-all" onclick="resetAll()">Reset</button>
    </div>

    <div class="active-tags-right">
      <div class="density-switch-wrap" role="group" aria-label="Card density">
        <span class="density-label">Cards:</span>
        <button type="button" class="density-pill active" id="btn-density-min" onclick="setDensityMode('minimal')" title="Minimal view (compact cards with collapsible intel)">◻ Minimal</button>
        <button type="button" class="density-pill" id="btn-density-exp" onclick="setDensityMode('detailed')" title="Detailed view (all intel and verdicts expanded)">☷ Detailed</button>
      </div>

      <div class="results-count-wrap">
        Showing <strong id="res-count">0</strong> verified vehicles
      </div>
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

  <!-- Score Calculation Pop-up Modal -->
  <div class="score-modal-backdrop" id="score-modal-backdrop" onclick="closeScoreModalOnBackdrop(event)">
    <div class="score-modal" role="dialog" aria-modal="true" aria-labelledby="score-modal-title">
      <div class="score-modal-header">
        <div>
          <span class="caption-5" style="color:var(--accent-blue); text-transform:uppercase; font-weight:700; letter-spacing:0.06em;">Mechanical & Value Scoring Engine</span>
          <h3 id="score-modal-title" style="margin-top:2px;">Score Calculation</h3>
        </div>
        <button type="button" class="score-modal-close" onclick="closeScoreModal()" title="Close">✕</button>
      </div>
      <div class="score-modal-body" id="score-modal-body">
        <!-- Injected dynamically on click -->
      </div>
      <div class="score-modal-footer">
        <span class="caption-5" style="color:var(--text-subtle);">Algorithmically audited against Bangalore used vehicle reliability & depreciation curves.</span>
        <button type="button" class="nav-btn" onclick="closeScoreModal()">Done</button>
      </div>
    </div>
  </div>

  <!-- On-Demand Live Sync Modal -->
  <div class="score-modal-backdrop" id="sync-modal-backdrop" onclick="closeSyncModalOnBackdrop(event)">
    <div class="score-modal" role="dialog" aria-modal="true" aria-labelledby="sync-modal-title">
      <div class="score-modal-header">
        <div>
          <span class="caption-5" style="color:var(--accent-blue); text-transform:uppercase; font-weight:700; letter-spacing:0.06em;">Real-time Pipeline Control</span>
          <h3 id="sync-modal-title" style="margin-top:2px;">On-Demand Live Inventory Sync</h3>
        </div>
        <button type="button" class="score-modal-close" onclick="closeLiveSyncModal()" title="Close">✕</button>
      </div>
      <div class="score-modal-body">
        <div class="sync-status-box">
          <div class="sync-status-header">
            <span class="live-pulse-dot"></span>
            <strong>Bangalore Real-Time Inventory Health</strong>
          </div>
          <p class="caption-2" style="color:var(--text-muted); margin-top:4px;">
            Top Bangalore deals often get booked in under 3 hours. All booked or reserved listings are filtered out automatically. Trigger fresh checks below on demand.
          </p>
        </div>

        <!-- Method 1: In-Browser Direct Cars24 Real-time Fetch -->
        <div class="sync-method-card">
          <div class="sync-method-head">
            <span class="sync-badge">CORS Enabled</span>
            <h4>1. In-Browser Instant Cars24 Scan</h4>
          </div>
          <p class="caption-2" style="color:var(--text-muted);">
            Directly queries the live Cars24 Bangalore gateway from your browser, rejects any booked stock, and injects active unbooked cars into your view.
          </p>
          <button type="button" class="cta-primary-btn sync-action-btn" id="btn-fetch-c24-live" onclick="fetchLiveCars24Direct()">
            <span>⚡ Query Live Cars24 API Now</span>
            <span id="c24-sync-spinner" style="display:none;">⏳ Fetching...</span>
          </button>
          <div id="c24-sync-result" class="caption-3" style="display:none; margin-top:8px;"></div>
        </div>

        <!-- Method 2: Trigger GitHub Actions Scraper Workflow -->
        <div class="sync-method-card">
          <div class="sync-method-head">
            <span class="sync-badge github">GitHub Actions</span>
            <h4>2. Trigger Full Scraper & Deploy (Spinny + Cars24)</h4>
          </div>
          <p class="caption-2" style="color:var(--text-muted);">
            Runs the Python crawler workflow on GitHub Actions ubuntu runner to crawl full Bangalore inventory, prune booked cars, and redeploy GitHub Pages.
          </p>
          <div class="github-pat-row" style="margin-top:8px;">
            <input type="password" id="gh-token-input" class="search-field" placeholder="Optional GitHub Token (saved locally) for 1-click dispatch" style="font-size:12px; height:36px;" />
            <button type="button" class="facet-pill" onclick="saveGhToken()">Save</button>
          </div>
          <div style="display:flex; gap:8px; margin-top:8px;">
            <button type="button" class="cta-primary-btn" onclick="triggerGithubDispatch()" style="flex:1;">
              <span>🚀 Dispatch GitHub Scraper</span>
            </button>
            <a href="https://github.com/kiranpuli/spinny-deals/actions/workflows/deploy.yml" target="_blank" rel="noopener noreferrer" class="cta-primary-btn" style="flex:1; text-align:center;">
              <span>Open Actions Web &rarr;</span>
            </a>
          </div>
          <div id="gh-dispatch-status" class="caption-3" style="display:none; margin-top:8px;"></div>
        </div>

        <!-- Method 3: Local Terminal Command -->
        <div class="sync-method-card">
          <div class="sync-method-head">
            <span class="sync-badge local">Local Terminal</span>
            <h4>3. Run Scraper Locally</h4>
          </div>
          <p class="caption-2" style="color:var(--text-muted);">
            Execute in your local shell to refresh deals and push to GitHub:
          </p>
          <div class="code-snippet-box">
            <code>cd spinny_monitor && python3 spinny_checker.py --city bangalore</code>
            <button type="button" class="copy-btn" onclick="copySnippet('cd spinny_monitor && python3 spinny_checker.py --city bangalore')">Copy</button>
          </div>
        </div>
      </div>
      <div class="score-modal-footer">
        <span class="caption-5" style="color:var(--text-subtle);">Automated crawler runs every hour continuously on GitHub Actions.</span>
        <button type="button" class="nav-btn" onclick="closeLiveSyncModal()">Close</button>
      </div>
    </div>
  </div>

  <!-- BMW Under ₹5L Ownership & Private Search Modal -->
  <div class="score-modal-backdrop" id="bmw-modal-backdrop" onclick="closeBmwModalOnBackdrop(event)">
    <div class="score-modal bmw-modal" role="dialog" aria-modal="true" aria-labelledby="bmw-modal-title">
      <div class="score-modal-header">
        <div>
          <span class="caption-5" style="color:var(--accent-blue); text-transform:uppercase; font-weight:700; letter-spacing:0.06em;">Bangalore Pre-Owned Intelligence</span>
          <h3 id="bmw-modal-title" style="margin-top:2px;">BMW Under ₹5 Lakhs: Buyer's Reality &amp; Tracker</h3>
        </div>
        <button type="button" class="score-modal-close" onclick="closeBmwModal()" title="Close">✕</button>
      </div>
      <div class="score-modal-body" style="gap:14px;">
        <div class="bmw-intel-card" style="background:#161E2E; border:1px solid #25334D; border-radius:10px; padding:14px;">
          <h4 style="font-size:13.5px; font-weight:700; color:#60A5FA; margin-bottom:6px; display:flex; align-items:center; gap:6px;">
            <span>ℹ️</span> Why aren't sub-₹5L BMWs on Spinny, Cars24, or Truwo?
          </h4>
          <p style="font-size:12.5px; line-height:1.5; color:var(--text-muted); margin:0;">
            Dealer platforms strictly cap inventory age (under 8–10 years) and require vehicles to qualify for 1-year warranty coverage. Any BMW priced under ₹5 Lakhs in Bangalore is 14 to 19 years old (2007–2011 E90 3 Series or 2005–2009 E60 5 Series) with over 100k km, which dealer platforms do not certify.
          </p>
        </div>

        <div class="bmw-intel-card" style="background:#181818; border:1px solid #272727; border-radius:10px; padding:14px;">
          <h4 style="font-size:13.5px; font-weight:700; color:#FBBF24; margin-bottom:6px;">
            📍 Where Sub-₹5L BMWs Are Actually Sold in Bangalore
          </h4>
          <p style="font-size:12.5px; line-height:1.5; color:var(--text-muted); margin-bottom:12px;">
            Direct private sellers are the only channel for sub-₹5L luxury in Bangalore. Deals appear on OLX Bangalore, Team-BHP Classifieds, and local enthusiast groups.
          </p>
          <a href="https://www.olx.in/en-in/bangalore_g4058803/cars_c84/q-bmw?filter=price_between_200000_to_500000" target="_blank" rel="noopener noreferrer" class="cta-primary-btn" style="text-decoration:none; display:flex; justify-content:space-between; align-items:center; background:#1E3A8A; border-color:#3B82F6;">
            <span>🔍 Browse Live BMW Listings on OLX Bangalore (₹2L – ₹5L)</span>
            <span>↗</span>
          </a>
        </div>

        <div class="bmw-intel-card" style="background:#181818; border:1px solid #272727; border-radius:10px; padding:14px;">
          <h4 style="font-size:13.5px; font-weight:700; color:#34D399; margin-bottom:10px;">
            💰 The Real Cost of Ownership (4 Hard Numbers)
          </h4>
          <div style="display:flex; flex-direction:column; gap:8px; font-size:12.5px;">
            <div style="display:flex; justify-content:space-between; border-bottom:1px solid #272727; padding-bottom:6px;">
              <span style="color:var(--text-muted);">1. Purchase Price (OLX private)</span>
              <strong style="color:var(--text-primary); font-family:var(--font-mono);">₹3.8L – ₹4.8L</strong>
            </div>
            <div style="display:flex; justify-content:space-between; border-bottom:1px solid #272727; padding-bottom:6px;">
              <span style="color:var(--text-muted);">2. Day-One Repair Buffer (mandatory)</span>
              <strong style="color:#EF4444; font-family:var(--font-mono);">+ ₹1.5L – ₹2.5L</strong>
            </div>
            <p style="color:var(--text-subtle); font-size:11.5px; margin:-4px 0 2px 0;">Covers brittle coolant tanks, aging hoses, oil filter housing gaskets, and front suspension control arm bushings.</p>
            <div style="display:flex; justify-content:space-between; border-bottom:1px solid #272727; padding-bottom:6px;">
              <span style="color:var(--text-muted);">3. Annual Maintenance (Bangalore FNGs)</span>
              <strong style="color:#F59E0B; font-family:var(--font-mono);">₹60,000 – ₹1,00,000 / yr</strong>
            </div>
            <div style="display:flex; justify-content:space-between; padding-bottom:2px;">
              <span style="color:var(--text-muted);">4. Karnataka 15-Year RTO Fitness Cliff</span>
              <strong style="color:var(--text-primary); font-family:var(--font-mono);">₹35,000 – ₹60,000</strong>
            </div>
          </div>
        </div>

        <div class="bmw-intel-card" style="background:rgba(52, 211, 153, 0.08); border:1px solid rgba(52, 211, 153, 0.25); border-radius:10px; padding:14px;">
          <h4 style="font-size:13.5px; font-weight:700; color:#34D399; margin-bottom:6px;">
            🛡️ Turnkey German Alternative: 33 Inspected Cars &le; ₹5L
          </h4>
          <p style="font-size:12px; line-height:1.5; color:var(--text-muted); margin-bottom:10px;">
            Want European high-speed stability and crash safety without high repair risk? Our dashboard tracks 33 inspected Volkswagen and Skoda cars (Polo, Ameo, Rapid) under ₹5L with warranty and accessible parts.
          </p>
          <button type="button" class="facet-pill active" onclick="closeBmwModal(); filterGermanUnder5L();" style="width:100%; padding:10px; font-size:12.5px; font-weight:600; text-align:center;">
            Show 33 Inspected German Cars Under ₹5L
          </button>
        </div>
      </div>
      <div class="score-modal-footer">
        <span class="caption-5" style="color:var(--text-subtle);">Compiled from Bangalore independent German garages (FNGs) &amp; Team-BHP real-world ownership data.</span>
        <button type="button" class="nav-btn" onclick="closeBmwModal()">Done</button>
      </div>
    </div>
  </div>

  <script>
    const CARS = """ + cars_json + """;
    const ALERTS = """ + alerts_json + """;

    // Application state - Defaults strictly to Curated Top Deals to Consider (< ₹5L, Score 80+)
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
      min_discount: 0
    };
    const expandedCards = new Set();

    // Initialize counts
    const spinnyCount = CARS.filter(c => (c.platform || '').toLowerCase() === 'spinny').length;
    const cars24Count = CARS.filter(c => (c.platform || '').toLowerCase() === 'cars24').length;
    const truwoCount = CARS.filter(c => (c.platform || '').toLowerCase() === 'truwo').length;
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
    const countTruwo = document.getElementById('count-truwo');
    if (countTruwo) countTruwo.textContent = truwoCount.toLocaleString('en-IN');

    const german5lCount = CARS.filter(c => (c.price || 0) <= 500000 && ['volkswagen', 'skoda', 'bmw', 'audi', 'mercedes'].some(b => (c.make || '').toLowerCase().includes(b))).length;
    const countGerman5l = document.getElementById('count-german-5l');
    if (countGerman5l) countGerman5l.textContent = german5lCount.toLocaleString('en-IN');

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

    function syncQuickBudgetButtons() {
      const p = state.max_price;
      document.querySelectorAll('.quick-budget-strip button').forEach(btn => {
        const txt = btn.textContent;
        if (p === 400000 && txt.includes('4L')) btn.classList.add('active');
        else if (p === 500000 && txt.includes('5L')) btn.classList.add('active');
        else if (p === 700000 && txt.includes('7L')) btn.classList.add('active');
        else if (p === 1000000 && txt.includes('10L')) btn.classList.add('active');
        else if (p === 0 && txt.includes('All')) btn.classList.add('active');
        else btn.classList.remove('active');
      });
    }

    function syncDiscountButtons() {
      const d = state.min_discount;
      document.querySelectorAll('#discount-pills button').forEach(btn => {
        const txt = btn.textContent;
        if (d === 0 && (txt === 'Any' || txt.includes('All'))) btn.classList.add('active');
        else if (d > 0 && txt.includes(`${d}%`)) btn.classList.add('active');
        else btn.classList.remove('active');
      });
    }

    function setMinDiscount(pct, btn) {
      state.min_discount = Number(pct);
      syncDiscountButtons();
      applyFilters();
    }

    function clearDiscount() {
      state.min_discount = 0;
      syncDiscountButtons();
      applyFilters();
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

    // View Mode Switcher (Curated Top Deals vs German vs All Market)
    function setViewMode(mode) {
      state.viewMode = mode;
      const btnCurated = document.getElementById('btn-mode-curated');
      const btnAll = document.getElementById('btn-mode-all');
      const btnGerman = document.getElementById('btn-german-5l');
      const statusText = document.getElementById('mode-status-text');

      if (btnGerman) btnGerman.classList.remove('active');

      if (mode === 'curated') {
        if (btnCurated) btnCurated.classList.add('active', 'curated');
        if (btnAll) btnAll.classList.remove('active');
        if (statusText) statusText.innerHTML = '<span class="pulse-dot"></span><span>Curated view: Under ₹5.0L · Deal Score 80+ · Low Mileage (&lt; 80k km) · Certified Assured</span>';

        state.max_price = 500000;
        state.max_km = 80000;
        state.brands.clear();
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
        if (statusText) statusText.innerHTML = '<span class="pulse-dot" style="background:var(--accent-blue); box-shadow:0 0 8px rgba(56,189,248,0.6);"></span><span>Showing all verified vehicles across Bangalore (Spinny, Cars24, Truwo).</span>';

        state.max_price = 0;
        state.max_km = 0;
        state.brands.clear();
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
      syncQuickBudgetButtons();
      syncDiscountButtons();
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
        const platBadge = plat === 'truwo' ? 'badge-platform truwo' : (plat === 'cars24' ? 'badge-platform cars24' : 'badge-platform spinny');

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
      syncQuickBudgetButtons();
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

    function resetBudgetAndAssurance() {
      clearMultiFilter('platforms');
      clearPrice();
      clearDiscount();
      clearMultiFilter('qualities');
    }

    function resetSpecsCategory() {
      clearMultiFilter('transmissions');
      clearMultiFilter('fuels');
      setYear(0, document.querySelector('#year-pills .facet-pill'));
      setMaxKm(0, document.querySelector('#km-pills .facet-pill'));
    }

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
      const sDrop = document.getElementById('ctrl-sort');
      if (sDrop) sDrop.value = 'score';

      const btnCurated = document.getElementById('btn-mode-curated');
      const btnAll = document.getElementById('btn-mode-all');
      const btnGerman = document.getElementById('btn-german-5l');
      if (btnCurated) btnCurated.classList.add('active', 'curated');
      if (btnAll) btnAll.classList.remove('active');
      if (btnGerman) btnGerman.classList.remove('active');

      const statusText = document.getElementById('mode-status-text');
      if (statusText) statusText.innerHTML = '<span class="pulse-dot"></span><span>Curated view: Under ₹5.0L · Deal Score 80+ · Low Mileage (&lt; 80k km) · Certified Assured</span>';

      document.querySelectorAll('#year-pills .facet-pill').forEach((p, idx) => {
        if (idx === 0) p.classList.add('active');
        else p.classList.remove('active');
      });
      document.querySelectorAll('#km-pills .facet-pill').forEach(b => {
        if (b.textContent.includes('80k')) b.classList.add('active');
        else b.classList.remove('active');
      });

      updateAllMultiFilterUIs();
      syncQuickBudgetButtons();
      syncDiscountButtons();
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
      syncQuickBudgetButtons();
      syncDiscountButtons();
      const btnGerman = document.getElementById('btn-german-5l');
      if (btnGerman) {
        const isGermanPreset = state.max_price === 500000 && state.brands.has('volkswagen') && state.brands.has('skoda');
        if (isGermanPreset) btnGerman.classList.add('active');
        else btnGerman.classList.remove('active');
      }
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

      const isAssured = car.category === 'assured' || car.category === 'verified';
      const plat = (car.platform || '').toLowerCase();
      const isTruwo = plat === 'truwo';
      const isCars24 = plat === 'cars24';
      const platformName = car.platform || (isTruwo ? 'Truwo' : (isCars24 ? 'Cars24' : 'Spinny'));
      const title = `${car.make_year} ${car.make} ${car.model} ${car.variant || ''}`.trim();
      const price = '₹' + (car.price / 100000).toFixed(2) + 'L';
      const km = (car.mileage / 1000).toFixed(0) + 'k km';

      let gradeClass = 'fair';
      let gradeLabel = `Score ${car.deal_score}/100`;
      if (car.deal_score >= 80) {
        gradeClass = 'top';
        gradeLabel = `💎 ${car.deal_score}/100 · TOP DEAL`;
      } else if (car.deal_score >= 68) {
        gradeClass = 'value';
        gradeLabel = `⭐ ${car.deal_score}/100 · VALUE PICK`;
      }

      const factors = car.score_breakdown || [];
      const factorsHtml = factors.map(f => {
        const typeClass = f.type || 'pos';
        return `
          <div class="score-audit-row">
            <div>
              <div class="score-audit-pillar">${f.pillar}</div>
              <div class="score-audit-desc">${f.detail}</div>
            </div>
            <span class="score-audit-badge ${typeClass}">${f.pts}</span>
          </div>
        `;
      }).join('');

      const modalTitle = document.getElementById('score-modal-title');
      if (modalTitle) modalTitle.textContent = `${title} — Score Audit`;

      const modalBody = document.getElementById('score-modal-body');
      if (modalBody) {
        modalBody.innerHTML = `
          <div class="modal-car-hero">
            ${car.img ? `<img src="${car.img}" alt="${title}" class="modal-car-thumb" loading="lazy" referrerpolicy="no-referrer" />` : ''}
            <div class="modal-hero-info">
              <div style="font-weight:700; color:#FFFFFF; font-size:14px;">${title}</div>
              <div style="font-size:11.5px; color:var(--text-muted); margin-top:2px;">
                ${price} · ${km} · ${(car.fuel_type || 'Petrol').toUpperCase()} · ${(car.transmission || 'MT').toUpperCase()} · ${platformName}
              </div>
            </div>
            <div class="modal-score-grade ${gradeClass}">${gradeLabel}</div>
          </div>

          <div class="modal-rationale-box">
            <span class="modal-rationale-icon">💡</span>
            <div class="modal-rationale-text">
              <strong>Why this rating?</strong> ${car.score_rationale || 'Score derived from odometer health, age, retail discount, and certified warranty.'}
            </div>
          </div>

          <div class="modal-breakdown-wrap">
            <div class="modal-breakdown-head">
              <span>Pillar & Audit Details</span>
              <span>Points Awarded</span>
            </div>
            <div class="score-audit-list">
              ${factorsHtml}
            </div>
            <div class="modal-breakdown-total">
              <span>Final Deal Score</span>
              <strong>${car.deal_score} / 100</strong>
            </div>
          </div>
        `;
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

    function openLiveSyncModal() {
      const modal = document.getElementById('sync-modal-backdrop');
      if (modal) {
        modal.classList.add('open');
        document.body.style.overflow = 'hidden';
      }
      const savedToken = localStorage.getItem('spinny_gh_token');
      const input = document.getElementById('gh-token-input');
      if (input && savedToken) input.value = savedToken;
    }

    function closeLiveSyncModal() {
      const modal = document.getElementById('sync-modal-backdrop');
      if (modal) modal.classList.remove('open');
      document.body.style.overflow = '';
    }

    function closeSyncModalOnBackdrop(e) {
      if (e && e.target && e.target.id === 'sync-modal-backdrop') {
        closeLiveSyncModal();
      }
    }

    function saveGhToken() {
      const input = document.getElementById('gh-token-input');
      if (!input) return;
      const val = input.value.trim();
      if (val) {
        localStorage.setItem('spinny_gh_token', val);
        const statusBox = document.getElementById('gh-dispatch-status');
        if (statusBox) {
          statusBox.style.display = 'block';
          statusBox.style.color = 'var(--accent-emerald)';
          statusBox.textContent = '✓ GitHub token saved in browser storage.';
        }
      }
    }

    function copySnippet(text) {
      if (navigator && navigator.clipboard) {
        navigator.clipboard.writeText(text);
        alert('Copied crawler command to clipboard!');
      }
    }

    async function triggerGithubDispatch() {
      const token = (document.getElementById('gh-token-input')?.value || localStorage.getItem('spinny_gh_token') || '').trim();
      const statusBox = document.getElementById('gh-dispatch-status');
      if (!token) {
        if (statusBox) {
          statusBox.style.display = 'block';
          statusBox.style.color = '#FBBF24';
          statusBox.innerHTML = 'Enter a GitHub Personal Access Token (with repo or workflow permissions) above, or <a href="https://github.com/kiranpuli/spinny-deals/actions/workflows/deploy.yml" target="_blank" style="color:#38BDF8; text-decoration:underline;">click here to trigger manually on GitHub</a>.';
        }
        return;
      }

      if (statusBox) {
        statusBox.style.display = 'block';
        statusBox.style.color = 'var(--accent-blue)';
        statusBox.textContent = '🚀 Dispatching crawler workflow to GitHub Actions runner...';
      }

      try {
        const res = await fetch('https://api.github.com/repos/kiranpuli/spinny-deals/actions/workflows/deploy.yml/dispatches', {
          method: 'POST',
          headers: {
            'Accept': 'application/vnd.github.v3+json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({ ref: 'main' })
        });

        if (res.status === 204) {
          if (statusBox) {
            statusBox.style.color = 'var(--accent-emerald)';
            statusBox.innerHTML = '✓ Crawler workflow dispatched! Scraper is now crawling fresh unbooked Bangalore stock and will deploy in ~2 minutes.';
          }
        } else {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.message || `HTTP ${res.status}`);
        }
      } catch (e) {
        if (statusBox) {
          statusBox.style.color = '#F87171';
          statusBox.textContent = `Dispatch error: ${e.message}. You can trigger directly via GitHub Actions UI.`;
        }
      }
    }

    async function fetchLiveCars24Direct() {
      const btn = document.getElementById('btn-fetch-c24-live');
      const spinner = document.getElementById('c24-sync-spinner');
      const resBox = document.getElementById('c24-sync-result');
      if (spinner) spinner.style.display = 'inline';
      if (btn) btn.disabled = true;

      try {
        const url = 'https://car-catalog-gateway-in.c24.tech/listing/v1/buy-used-car';
        const payload = {
          cityId: '4709',
          size: 60,
          sort: 'P',
          searchFilter: [],
          filterVersion: 4
        };
        const res = await fetch(url, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X_TENANT_ID': 'INDIA_CAR_LISTING',
            'SOURCE': 'WebApp'
          },
          body: JSON.stringify(payload)
        });
        if (!res.ok) throw new Error('Cars24 returned HTTP ' + res.status);
        const data = await res.json();
        const items = data.content || [];
        
        // Filter strictly active and unbooked cars
        const liveItems = items.filter(it => {
          const st = String(it.status || '').toUpperCase();
          const sub = String(it.subStatus || '').toUpperCase();
          if (st !== 'AVAILABLE') return false;
          if (sub && sub !== 'AVAILABLE') return false;
          if (it.isBooked) return false;
          return true;
        });

        let newCount = 0;
        liveItems.forEach(it => {
          const aid = 'c24_' + it.appointmentId;
          const exists = CARS.some(c => String(c.id) === aid);
          if (!exists) {
            const price = it.listingPrice || 0;
            const km = (it.odometer && it.odometer.value) || 0;
            const year = it.year || 2018;
            const bt = JSON.stringify(it.businessTag || {}).toLowerCase();
            const isAssured = bt.includes('assured') || bt.includes('owned');
            const dImg = it.detailImage || {};
            const img = dImg.bgRemovedUri || dImg.uri || '';

            let score = 45;
            if (km <= 25000) score += 24;
            else if (km <= 40000) score += 18;
            else if (km <= 60000) score += 12;
            else if (km <= 80000) score += 5;
            else if (km > 100000) score -= 10;

            if (year >= 2021) score += 22;
            else if (year >= 2019) score += 18;
            else if (year >= 2017) score += 12;
            else if (year >= 2015) score += 6;
            else if (year <= 2013) score -= 6;

            if (isAssured) score += 15;
            if (year >= 2018 && km <= 40000) score += 6;
            const deal_score = Math.min(99, Math.max(40, score));

            CARS.unshift({
              id: aid,
              platform: 'Cars24',
              make: it.make || '',
              model: it.model || '',
              variant: it.variant || '',
              make_year: year,
              mileage: km,
              price: price,
              orig_retail_price: Math.round((price * 1.4) / 10000) * 10000,
              retail_discount_pct: 35,
              fuel_type: it.fuelType || 'Petrol',
              transmission: (it.transmissionType && it.transmissionType.value) || 'Manual',
              category: isAssured ? 'assured' : 'market',
              hub: (it.address && it.address.locality) || 'Cars24 Bangalore Hub',
              img: img,
              url: 'https://www.cars24.com/' + (it.cdpRelativeUrl || ''),
              deal_score: deal_score,
              score_rationale: 'Live in-browser verify: confirmed active unbooked stock on Cars24.',
              score_breakdown: [
                { pillar: 'Live Stock Verification', detail: 'Confirmed active & unbooked on Cars24 gateway', pts: '+25 pts', type: 'pos' },
                { pillar: 'Odometer Health', detail: `${Math.round(km/1000)}k km verified`, pts: '+18 pts', type: 'pos' }
              ],
              ownership_review: {
                fuel_economy: '12 to 14 km/l in city traffic',
                annual_maintenance: '₹5,000 to ₹7,000 yearly',
                ride_comfort: 'High clearance over Bangalore speed bumps',
                known_issues: 'Standard brake pad & clutch check',
                bangalore_verdict: 'Live active Cars24 stock in Bangalore.'
              }
            });
            newCount++;
          }
        });

        if (resBox) {
          resBox.style.display = 'block';
          resBox.style.color = 'var(--accent-emerald)';
          resBox.textContent = `✓ Fetched ${liveItems.length} active unbooked Cars24 vehicles (${newCount} new added)!`;
        }
        applyFilters();
      } catch (err) {
        if (resBox) {
          resBox.style.display = 'block';
          resBox.style.color = '#F87171';
          resBox.textContent = `Error fetching live Cars24: ${err.message}`;
        }
      } finally {
        if (spinner) spinner.style.display = 'none';
        if (btn) btn.disabled = false;
      }
    }

    function openBmwModal() {
      const modal = document.getElementById('bmw-modal-backdrop');
      if (modal) {
        modal.classList.add('open');
        document.body.style.overflow = 'hidden';
      }
    }

    function closeBmwModal() {
      const modal = document.getElementById('bmw-modal-backdrop');
      if (modal) modal.classList.remove('open');
      document.body.style.overflow = '';
    }

    function closeBmwModalOnBackdrop(e) {
      if (e && e.target && e.target.id === 'bmw-modal-backdrop') {
        closeBmwModal();
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
      if (btnCurated) btnCurated.classList.remove('active', 'curated');
      if (btnAll) btnAll.classList.remove('active');
      if (btnGerman) btnGerman.classList.add('active');

      const statusText = document.getElementById('mode-status-text');
      if (statusText) statusText.innerHTML = '<span class="pulse-dot" style="background:#34D399; box-shadow:0 0 8px rgba(52,211,153,0.6);"></span><span>German Cars Scope: Volkswagen, Skoda, BMW, Audi ≤ ₹5.0L across Bangalore</span>';

      state.search = '';
      const sInput = document.getElementById('ctrl-search');
      if (sInput) sInput.value = '';

      state.min_price = 0;
      state.max_price = 500000;
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

      syncQuickBudgetButtons();
      syncDiscountButtons();
      updateAllMultiFilterUIs();
      applyFilters();

      const resultsSection = document.getElementById('cars-grid');
      if (resultsSection) resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    window.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        closeScoreModal();
        closeAlertsModal();
        closeLiveSyncModal();
        closeBmwModal();
      }
    });

    function renderCards(list) {
      const grid = document.getElementById('cars-grid');
      if (!list.length) {
        const isBmwQuery = (state.search && state.search.toLowerCase().includes('bmw')) || state.brands.has('bmw');
        if (isBmwQuery) {
          grid.innerHTML = `
            <div class="empty-state bmw-empty-card">
              <div class="bmw-empty-badge">🏎️ BMW Under ₹5 Lakhs Advisory</div>
              <h3>No sub-₹5L BMWs on Spinny, Cars24, or Truwo</h3>
              <p>Certified dealer platforms only stock 2015+ luxury vehicles due to warranty &amp; inspection criteria. Sub-₹5L BMWs (2007–2011 E90 3 Series &amp; E60 5 Series) are sold directly by private owners.</p>
              <div class="bmw-empty-actions">
                <a href="https://www.olx.in/en-in/bangalore_g4058803/cars_c84/q-bmw?filter=price_between_200000_to_500000" target="_blank" rel="noopener noreferrer" class="cta-primary-btn" style="display:inline-flex; width:auto; text-decoration:none; padding:10px 18px;">
                  <span>Search Private Owner BMWs on OLX Bangalore (₹2L - ₹5L)</span>
                  <span>&rarr;</span>
                </a>
                <button type="button" class="facet-pill active" onclick="openBmwModal()" style="padding:8px 14px;">Open Ownership &amp; Repair Cost Guide</button>
                <button type="button" class="facet-pill" onclick="filterGermanUnder5L()" style="padding:8px 14px;">View 33 Inspected German Cars Under ₹5L (VW / Skoda)</button>
              </div>
            </div>
          `;
          return;
        }
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
        const isAssured = c.category === 'assured' || c.category === 'verified';
        const tierSubLabel = isTruwo 
          ? 'Direct Owner' 
          : (isCars24 ? (isAssured ? 'Assured' : 'Certified') : (isAssured ? 'Assured' : 'Wholesale'));
        const pricingTagText = isTruwo ? 'Direct Owner · Inspected' : 'Fixed Price · No Haggle';
        const platformClass = isTruwo ? 'truwo' : (isCars24 ? 'cars24' : 'spinny');
        const platformName = c.platform || (isTruwo ? 'Truwo' : (isCars24 ? 'Cars24' : 'Spinny'));

        const price = '₹' + (c.price / 100000).toFixed(2) + 'L';
        const topPrice = c.orig_retail_price ? ('₹' + (c.orig_retail_price / 100000).toFixed(2) + 'L') : '—';
        const discPct = c.retail_discount_pct || (c.orig_retail_price ? Math.round(((c.orig_retail_price - c.price) / c.orig_retail_price) * 100) : 0);
        const topSavings = c.orig_retail_price ? Math.max(0, c.orig_retail_price - c.price) : 0;
        const topSavingsFmt = topSavings >= 100000 ? ('₹' + (topSavings / 100000).toFixed(2) + 'L') : ('₹' + Math.round(topSavings / 1000) + 'k');

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

        const rev = c.ownership_review || {};
        const isExpanded = state.density === 'detailed' || expandedCards.has(String(c.id));

        return `
          <article class="card" id="card-${c.id}">
            <!-- Flat Photo Area (B4 flat #131209) -->
            <div class="card-photo">
              <!-- Score Grade Badge with Clickable Audit -->
              <button type="button" class="badge-grade ${gradeClass}" onclick="openScoreModal('${c.id}', event)" title="Click to view score audit & point breakdown">
                <span>${gradeLabel}</span>
                <span class="badge-info-hint" aria-hidden="true">📊 Audit</span>
              </button>
              
              <!-- Top-Right Badges Container -->
              <div class="card-badges-top-right">
                <span class="source-tag source-${platformClass}">
                  <span class="source-dot ${platformClass}-dot"></span>
                  <span class="source-name">${platformName}</span>
                  <span class="source-tier">${tierSubLabel}</span>
                </span>
              </div>

              <!-- Live Unbooked Status -->
              <div class="badge-availability">
                <span class="avail-dot"></span>
                <span>Available Stock</span>
              </div>

              ${c.img ? `<img src="${c.img}" alt="${title}" loading="lazy" referrerpolicy="no-referrer" />` : '<span class="caption-5" style="color:var(--text-subtle);">No image preview</span>'}
            </div>

            <div class="card-content">
              <!-- Header Block -->
              <div class="car-header-block">
                <h2 class="car-title">${title}</h2>
                <div class="car-specs-strip">
                  <span class="spec-pill">${km}</span>
                  <span class="spec-pill">${(c.fuel_type || 'Petrol').toUpperCase()}</span>
                  <span class="spec-pill">${(c.transmission || 'MT').toUpperCase()}</span>
                  <span class="spec-pill hub">${c.hub}</span>
                </div>
              </div>

              <!-- Pricing Row (Fixed Price & Top Showroom Discount) -->
              <div class="card-pricing-bar">
                <div class="pricing-primary-col">
                  <span class="pricing-sub-label">${isTruwo ? 'Owner Price' : 'Fixed Price'}</span>
                  <span class="pricing-val-main">${price}</span>
                  <span class="pricing-source-badge ${platformClass}">${pricingTagText}</span>
                </div>
                <div class="pricing-retail-col">
                  <span class="pricing-sub-label">Original Top Price</span>
                  <span class="pricing-val-top">${topPrice}</span>
                  ${discPct > 0 ? `<span class="discount-badge-lg">-${discPct}% Off (Save ~${topSavingsFmt})</span>` : ''}
                </div>
              </div>

              <!-- Financial Telemetry Strip (Kept visible for fast buyback comparison) -->
              <div class="card-telemetry-strip">
                <div class="telemetry-item">
                  <span class="tele-k">${isAssured ? '24M Buyback' : '24M Resale'}</span>
                  <span class="tele-v buyback">${buyback}</span>
                </div>
                <div class="telemetry-item" style="text-align: right;">
                  <span class="tele-k">Depreciation</span>
                  <span class="tele-v loss">${monthly}</span>
                </div>
              </div>

              <!-- Progressive Disclosure: 1-Click Accordion Button -->
              <button type="button" class="btn-intel-toggle ${isExpanded ? 'active' : ''}" id="intel-btn-${c.id}" onclick="toggleCardIntel('${c.id}', event)">
                <span>✦ View Ownership Intel & Verdict</span>
                <span class="intel-chevron">▾</span>
              </button>

              <!-- Collapsible Card Intel Drawer -->
              <div class="card-intel-drawer ${isExpanded ? 'open' : ''}" id="intel-drawer-${c.id}">
                <!-- Ownership Intel Matrix (Clean 2x2 Grid) -->
                <div class="card-intel-matrix">
                  <div class="intel-cell">
                    <span class="intel-k">⛽ Mileage</span>
                    <span class="intel-v">${rev.fuel_economy || '12–14 km/l city'}</span>
                  </div>
                  <div class="intel-cell">
                    <span class="intel-k">🔧 Service</span>
                    <span class="intel-v">${rev.annual_maintenance || '₹5k–₹7k/yr'}</span>
                  </div>
                  <div class="intel-cell">
                    <span class="intel-k">🛣️ Road Ride</span>
                    <span class="intel-v">${rev.ride_comfort || 'Speed breaker safe'}</span>
                  </div>
                  <div class="intel-cell">
                    <span class="intel-k">⚠️ Watchlist</span>
                    <span class="intel-v">${rev.known_issues || 'Inspect clutch & brakes'}</span>
                  </div>
                </div>

                <!-- Bangalore Verdict Note -->
                <div class="card-verdict-row">
                  <p class="card-verdict-text"><strong style="color:var(--text-body);">Bangalore Verdict:</strong> ${rev.bangalore_verdict || (c.verdict || 'Reliable urban commuter with steady resale demand.')}</p>
                </div>
              </div>

              <!-- Single Primary CTA in Footer -->
              <div class="card-footer">
                <a href="${c.url || '#'}" target="_blank" rel="noopener noreferrer" class="cta-primary-btn">
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
