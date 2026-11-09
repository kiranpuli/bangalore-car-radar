<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>Bangalore Car Radar</title>
</head>
<body>
  <div align="center">
    <h1>🏎️ Bangalore Car Radar</h1>
    <p><strong>Autonomous multi-platform used car deal intelligence &amp; mechanical audit pipeline for Bangalore.</strong></p>
    <p>
      <a href="https://kiranpuli.github.io/spinny-deals/"><img src="https://img.shields.io/badge/Live_Dashboard-GitHub_Pages-amber?style=flat-square&color=F59E0B" alt="Live Dashboard" /></a>
      <a href="https://ntfy.sh/kiran-car-radar"><img src="https://img.shields.io/badge/Mobile_Push-ntfy.sh-blue?style=flat-square&color=3B82F6" alt="Mobile Alerts" /></a>
      <img src="https://img.shields.io/badge/Tracked_Cars-1%2C780%2B-emerald?style=flat-square&color=10B981" alt="Tracked Cars" />
      <img src="https://img.shields.io/badge/Audit-200--Point-purple?style=flat-square&color=8B5CF6" alt="Audit" />
    </p>
  </div>

  <hr />

  <h2>Table of Contents</h2>
  <ul>
    <li><a href="#1-system-overview">1. System Overview</a></li>
    <li><a href="#2-marketplace-integrations">2. Marketplace Integrations</a></li>
    <li><a href="#3-deal-scoring--mechanical-audit">3. Deal Scoring &amp; Mechanical Audit</a></li>
    <li><a href="#4-filter-deck--controls">4. Filter Deck &amp; Controls</a></li>
    <li><a href="#5-instant-mobile-push-pipeline">5. Instant Mobile Push Pipeline</a></li>
    <li><a href="#6-hourly-automation-architecture">6. Hourly Automation Architecture</a></li>
    <li><a href="#7-developer-cli-commands">7. Developer CLI Commands</a></li>
    <li><a href="#8-standalone-documentation">8. Standalone Documentation</a></li>
  </ul>

  <hr />

  <h2 id="1-system-overview">1. System Overview</h2>
  <p>Bangalore Car Radar monitors pre-owned vehicle inventories across Spinny, Cars24, Truwo, and OLX. It runs automated valuation algorithms, analyzes 200-point mechanical inspection sheets, scores deals on a 0 to 100 conviction index, and dispatches real-time alerts for top deals under ₹5L.</p>

  <h2 id="2-marketplace-integrations">2. Marketplace Integrations</h2>
  <table>
    <thead>
      <tr>
        <th>Source</th>
        <th>Coverage</th>
        <th>Type</th>
        <th>Inspection Standard</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td><strong>Spinny</strong></td>
        <td>Bangalore (Whitefield, Yelahanka, Electronic City, Mysore Road)</td>
        <td>Spinny Assured &amp; Max</td>
        <td>200-Point checklist &amp; 1-year warranty</td>
      </tr>
      <tr>
        <td><strong>Cars24</strong></td>
        <td>Bangalore Hubs</td>
        <td>Cars24 Assured</td>
        <td>140-Point mechanical inspection</td>
      </tr>
      <tr>
        <td><strong>Truwo</strong></td>
        <td>Bengaluru South/East</td>
        <td>Verified Inventory</td>
        <td>Direct hub telemetry</td>
      </tr>
      <tr>
        <td><strong>OLX</strong></td>
        <td>Bangalore City</td>
        <td>Verified Direct Listings</td>
        <td>Direct seller &amp; certified inventory</td>
      </tr>
    </tbody>
  </table>

  <h2 id="3-deal-scoring--mechanical-audit">3. Deal Scoring &amp; Mechanical Audit</h2>
  <p>Every vehicle is scored from 0 to 100 based on:</p>
  <ul>
    <li><strong>Depreciation Curve (40 pts):</strong> Price vs. year &amp; brand resale retention in Bangalore.</li>
    <li><strong>Mechanical Inspection (30 pts):</strong> Tyre tread depth (&ge; 4mm), suspension condition, engine leaks, and battery/AC health.</li>
    <li><strong>Odometer Verification (15 pts):</strong> Mileage verified against service history (&le; 80,000 km target).</li>
    <li><strong>Ownership &amp; Bodywork (15 pts):</strong> Single-owner preference, original paint verification.</li>
  </ul>
  <p><strong>Curated Threshold:</strong> Cars with Score &ge; 80, Price &le; ₹5.00L, and Mileage &le; 80k km are highlighted in <em>🔥 Top Deals</em>.</p>

  <h2 id="4-filter-deck--controls">4. Filter Deck &amp; Controls</h2>
  <ul>
    <li><strong>Budget:</strong> Exact Min/Max inputs in ₹ Lakhs with continuous range slider (₹1L to ₹15L+).</li>
    <li><strong>Model Year:</strong> Quick segmented pill buttons (<code>All</code>, <code>2016+</code>, <code>2018+</code>, <code>2020+</code>, <code>2022+</code>) and continuous slider.</li>
    <li><strong>Showroom Savings:</strong> Discount percentage pills (<code>Any</code>, <code>20%+</code>, <code>35%+</code>, <code>50%+</code>) with 0% to 60%+ slider.</li>
    <li><strong>Max Mileage:</strong> Ceiling pills (<code>Any</code>, <code>&le; 40k</code>, <code>&le; 60k</code>, <code>&le; 80k</code>, <code>&le; 100k</code>) and 20k to 120k km slider.</li>
    <li><strong>Source Platforms:</strong> Multi-select buttons with live inventory counters.</li>
    <li><strong>Transmission:</strong> Dedicated gearbox facet panel with live count badges for <code>All (1,780+)</code>, <code>⚡ Automatic (830+)</code>, and <code>🕹️ Manual (940+)</code>.</li>
    <li><strong>Fuel Type:</strong> Dedicated fuel facet panel with live count badges for <code>All</code>, <code>⛽ Petrol (1,280+)</code>, <code>🛢️ Diesel (450+)</code>, and <code>🍃 CNG (40+)</code>.</li>
    <li><strong>Automakers:</strong> Live brand chip selectors with inventory counts.</li>
    <li><strong>Model Exclusion:</strong> <em>⊘ Hide Model</em> buttons save unwanted models to browser <code>localStorage</code>.</li>
  </ul>

  <h2 id="5-instant-mobile-push-pipeline">5. Instant Mobile Push Pipeline</h2>
  <p>Push alerts are delivered directly to smartphones (e.g., Samsung S25 Ultra) using <code>ntfy.sh/kiran-car-radar</code> with zero registration:</p>
  <pre><code>curl -d "🔥 2018 Honda Jazz Petrol dropped to ₹4.20L at Spinny Whitefield!" \
     -H "Title: Car Deal Radar Alert" \
     -H "Click: https://kiranpuli.github.io/spinny-deals/" \
     https://ntfy.sh/kiran-car-radar</code></pre>

  <h2 id="6-hourly-automation-architecture">6. Hourly Automation Architecture</h2>
  <p>Inventory is updated hourly via two synchronized pipelines:</p>
  <ol>
    <li><strong>GitHub Actions:</strong> Scheduled hourly workflow scraping live feeds, rebuilding HTML, and committing to <code>main</code>.</li>
    <li><strong>Local Sync:</strong> <code>hourly_update.sh</code> with git rebase resilience and error logging.</li>
  </ol>

  <h2 id="7-developer-cli-commands">7. Developer CLI Commands</h2>
  <h3>Rebuild Static UI</h3>
  <pre><code>python3 build_ui.py</code></pre>

  <h3>Run Scrapers Headless</h3>
  <pre><code>python3 spinny_checker.py --headless</code></pre>

  <h3>Run Local Development Server</h3>
  <pre><code>python3 server.py 8000</code></pre>

  <h2 id="8-standalone-documentation">8. Standalone Documentation</h2>
  <p>Complete styled documentation is available as standalone HTML at <a href="documentation.html">documentation.html</a> or online at <a href="https://kiranpuli.github.io/spinny-deals/documentation.html">https://kiranpuli.github.io/spinny-deals/documentation.html</a>.</p>
</body>
</html>
