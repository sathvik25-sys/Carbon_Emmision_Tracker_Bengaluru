/**
 * Bengaluru Carbon Emission Tracker - Frontend Application
 * Handles reactive form inputs, Chart.js visualizations, API communication,
 * What-If scenario simulations, and Carbon Receipt generation.
 */

document.addEventListener("DOMContentLoaded", () => {
  // Initialize Lucide icons
  if (window.lucide) {
    window.lucide.createIcons();
  }

  // State
  let configData = null;
  let presetsData = null;
  let breakdownChart = null;
  let whatIfChart = null;

  // DOM Elements
  const form = document.getElementById("carbon-form");
  const mainModeSelect = document.getElementById("main_mode");
  const modeDescText = document.getElementById("mode-desc-text");
  const oneWayDistInput = document.getElementById("one_way_distance_km");
  const commuteDaysInput = document.getElementById("commute_days_per_month");
  const rushHourSlider = document.getElementById("rush_hour_pct");
  const rushHourValSpan = document.getElementById("rush_hour_val");
  const vehicleAgeContainer = document.getElementById("vehicle-age-container");
  const vehicleAgeInput = document.getElementById("vehicle_age");
  const otherModeSelect = document.getElementById("other_travel_mode");
  const otherDistInput = document.getElementById("other_travel_distance_km");
  const elecKwhInput = document.getElementById("monthly_electricity_kwh");
  const elecMembersInput = document.getElementById("household_members");

  // Previews
  const roundTripPreview = document.getElementById("round-trip-preview");
  const monthlyKmPreview = document.getElementById("monthly-km-preview");
  const otherMonthlyKmPreview = document.getElementById("other-monthly-km-preview");
  const perCapitaKwhPreview = document.getElementById("per-capita-kwh-preview");

  // Buttons
  const btnCalculate = document.getElementById("btn-calculate");
  const btnRunML = document.getElementById("btn-run-ml");
  const btnReset = document.getElementById("btn-reset-form");
  const btnPrintNav = document.getElementById("btn-print-receipt-nav");
  const btnPrintInner = document.getElementById("btn-print-receipt-inner");

  // Error Banner
  const errorBanner = document.getElementById("error-banner");
  const errorBannerText = document.getElementById("error-banner-text");

  // Fetch initial config and presets
  async function initializeApp() {
    try {
      const [cfgRes, presRes] = await Promise.all([
        fetch("/api/config"),
        fetch("/api/presets"),
      ]);

      if (cfgRes.ok) configData = await cfgRes.json();
      if (presRes.ok) presetsData = await presRes.json();

      updateModeDescriptions();
      updateInputPreviews();
      setupEventListeners();

      // Trigger initial calculation with default loaded values
      await performCalculation();
      await performMLPrediction();
    } catch (err) {
      console.error("Initialization error:", err);
      showError("Failed to initialize application configuration. Please reload.");
    }
  }

  // Update input previews reactively
  function updateInputPreviews() {
    const oneWay = parseFloat(oneWayDistInput.value) || 0;
    const days = parseInt(commuteDaysInput.value) || 0;
    const otherWeekly = parseFloat(otherDistInput.value) || 0;
    const elecKwh = parseFloat(elecKwhInput.value) || 0;
    const members = Math.max(1, parseInt(elecMembersInput.value) || 1);

    const roundTrip = oneWay * 2;
    const monthlyCommuteKm = roundTrip * days;
    const otherMonthlyKm = otherWeekly * (52 / 12);
    const perCapitaKwh = elecKwh / members;

    if (roundTripPreview) roundTripPreview.textContent = `${roundTrip.toFixed(1)} km/day`;
    if (monthlyKmPreview) monthlyKmPreview.textContent = `${monthlyCommuteKm.toFixed(0)} km`;
    if (otherMonthlyKmPreview) otherMonthlyKmPreview.textContent = `${otherMonthlyKm.toFixed(0)} km/mo`;
    if (perCapitaKwhPreview) perCapitaKwhPreview.textContent = `${perCapitaKwh.toFixed(1)} kWh/person`;
  }

  // Update mode description & toggle vehicle age
  function updateModeDescriptions() {
    const mode = mainModeSelect.value;
    if (configData && configData.modes && configData.modes[mode]) {
      const meta = configData.modes[mode];
      modeDescText.textContent = `${meta.description} (Base: ${meta.factor} ${meta.unit})`;

      if (meta.requires_vehicle_age) {
        vehicleAgeContainer.classList.remove("opacity-40", "pointer-events-none");
        vehicleAgeInput.disabled = false;
      } else {
        vehicleAgeContainer.classList.add("opacity-40", "pointer-events-none");
        vehicleAgeInput.disabled = true;
      }
    }
  }

  // Error handling
  function showError(msg) {
    errorBannerText.textContent = msg;
    errorBanner.classList.remove("hidden");
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function clearError() {
    errorBanner.classList.add("hidden");
    errorBannerText.textContent = "";
  }

  // Form Validation
  function getValidatedFormPayload() {
    clearError();

    const mainMode = mainModeSelect.value;
    const oneWayDist = parseFloat(oneWayDistInput.value);
    const days = parseInt(commuteDaysInput.value);
    const rushHour = parseFloat(rushHourSlider.value);
    const vehicleAge = parseFloat(vehicleAgeInput.value) || 0;
    const otherMode = otherModeSelect.value;
    const otherDist = parseFloat(otherDistInput.value) || 0;
    const elecKwh = parseFloat(elecKwhInput.value);
    const members = parseInt(elecMembersInput.value);

    // Validations
    if (isNaN(oneWayDist) || oneWayDist < 0) {
      showError("One-way distance cannot be negative or blank.");
      return null;
    }
    if (oneWayDist > 300) {
      showError("One-way distance exceeds realistic single-day Bengaluru commute threshold (max 300 km).");
      return null;
    }
    if (isNaN(days) || days < 0 || days > 31) {
      showError("Commute days per month must be between 0 and 31 days.");
      return null;
    }
    if (isNaN(rushHour) || rushHour < 0 || rushHour > 100) {
      showError("Rush hour share must be between 0% and 100%.");
      return null;
    }
    if (isNaN(vehicleAge) || vehicleAge < 0 || vehicleAge > 40) {
      showError("Vehicle age must be between 0 and 40 years.");
      return null;
    }
    if (isNaN(otherDist) || otherDist < 0 || otherDist > 1000) {
      showError("Other weekly travel distance must be between 0 and 1,000 km.");
      return null;
    }
    if (isNaN(elecKwh) || elecKwh < 0 || elecKwh > 10000) {
      showError("Household electricity must be between 0 and 10,000 kWh/month.");
      return null;
    }
    if (isNaN(members) || members < 1 || members > 50) {
      showError("Household members must be at least 1 person (prevents division by zero).");
      return null;
    }

    return {
      main_mode: mainMode,
      one_way_distance_km: oneWayDist,
      commute_days_per_month: days,
      rush_hour_pct: rushHour,
      vehicle_age: vehicleAge,
      other_travel_mode: otherMode,
      other_travel_distance_km: otherDist,
      monthly_electricity_kwh: elecKwh,
      household_members: members,
    };
  }

  // Perform Factor-based Calculation
  async function performCalculation() {
    const payload = getValidatedFormPayload();
    if (!payload) return;

    btnCalculate.disabled = true;
    btnCalculate.innerHTML = `<span class="inline-block animate-spin mr-2">⏳</span> Computing Footprint...`;

    try {
      const res = await fetch("/api/calculate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const errJson = await res.json();
        throw new Error(errJson.detail || "Calculation request failed.");
      }

      const data = await res.json();
      renderResults(data);
    } catch (err) {
      console.error(err);
      showError(err.message || "An error occurred during calculation.");
    } finally {
      btnCalculate.disabled = false;
      btnCalculate.innerHTML = `<i data-lucide="calculator" class="w-5 h-5"></i><span>Calculate & Generate Receipt</span>`;
      if (window.lucide) window.lucide.createIcons();
    }
  }

  // Perform ML Non-Linear Prediction
  async function performMLPrediction() {
    const payload = getValidatedFormPayload();
    if (!payload) return;

    btnRunML.disabled = true;
    btnRunML.innerHTML = `<span class="inline-block animate-spin mr-2">🧠</span> Inferencing ML Model...`;

    try {
      const res = await fetch("/api/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const errJson = await res.json();
        throw new Error(errJson.detail || "ML prediction failed.");
      }

      const data = await res.json();
      renderMLResults(data);
    } catch (err) {
      console.error(err);
    } finally {
      btnRunML.disabled = false;
      btnRunML.innerHTML = `<i data-lucide="brain-circuit" class="w-4 h-4 text-emerald-400"></i><span>Run Machine Learning Non-Linear Estimation</span>`;
      if (window.lucide) window.lucide.createIcons();
    }
  }

  // Render Core Calculation Results
  function renderResults(data) {
    const summary = data.summary;
    const breakdown = data.breakdown;

    // 1. Metric Cards
    document.getElementById("metric-monthly-total").textContent = summary.monthly_total_co2_kg.toFixed(1);
    document.getElementById("metric-daily-avg").textContent = summary.daily_average_co2_kg.toFixed(2);
    document.getElementById("metric-annual-total").textContent = summary.annual_total_co2_kg.toFixed(0);
    document.getElementById("metric-trees-offset").textContent = summary.trees_offset_needed;

    const tierBadge = document.getElementById("metric-tier-badge");
    tierBadge.textContent = summary.tier_label;
    tierBadge.className = `inline-block mt-1 text-[10px] font-semibold px-2 py-0.5 rounded ${getTierBadgeClass(summary.tier_code)}`;

    // 2. Benchmark Bar
    const userMonthly = summary.monthly_total_co2_kg;
    document.getElementById("bar-user-val").textContent = `${userMonthly.toFixed(1)} kg`;

    const maxBenchmark = 390.0; // Global avg
    const userPctWidth = Math.min(100, Math.max(5, (userMonthly / maxBenchmark) * 100));
    const progressBar = document.getElementById("bar-user-progress");
    progressBar.style.width = `${userPctWidth}%`;

    const benchBadge = document.getElementById("benchmark-status-badge");
    if (summary.bengaluru_delta_pct < 0) {
      benchBadge.textContent = `${Math.abs(summary.bengaluru_delta_pct)}% below Bengaluru avg`;
      benchBadge.className = "text-[11px] font-semibold text-emerald-700";
      progressBar.className = "bg-emerald-500 h-full rounded-full transition-all duration-500";
    } else {
      benchBadge.textContent = `${summary.bengaluru_delta_pct}% above Bengaluru avg`;
      benchBadge.className = "text-[11px] font-semibold text-amber-700";
      progressBar.className = "bg-amber-500 h-full rounded-full transition-all duration-500";
    }

    // 3. Breakdown Rows & Bars
    const commute = breakdown.commute;
    const other = breakdown.other_travel;
    const elec = breakdown.electricity;

    document.getElementById("breakdown-commute-kg").textContent = `${commute.monthly_commute_co2_kg.toFixed(1)} kg`;
    document.getElementById("breakdown-commute-pct").textContent = `(${commute.percentage}%)`;
    document.getElementById("bar-commute-pct").style.width = `${commute.percentage}%`;

    document.getElementById("breakdown-other-kg").textContent = `${other.monthly_other_co2_kg.toFixed(1)} kg`;
    document.getElementById("breakdown-other-pct").textContent = `(${other.percentage}%)`;
    document.getElementById("bar-other-pct").style.width = `${other.percentage}%`;

    document.getElementById("breakdown-elec-kg").textContent = `${elec.monthly_electricity_co2_kg.toFixed(1)} kg`;
    document.getElementById("breakdown-elec-pct").textContent = `(${elec.percentage}%)`;
    document.getElementById("bar-elec-pct").style.width = `${elec.percentage}%`;

    // 4. Update Doughnut Chart
    updateBreakdownChart(commute.monthly_commute_co2_kg, other.monthly_other_co2_kg, elec.monthly_electricity_co2_kg);

    // 5. Update What-If Scenarios
    renderWhatIfScenarios(data.what_if_scenarios, commute.monthly_commute_co2_kg, commute.mode_label);

    // 6. Update Printable Carbon Receipt
    renderReceipt(data);

    // 7. Update Actionable Tips
    renderRecommendations(data.recommendations);
  }

  function getTierBadgeClass(tier) {
    switch (tier) {
      case "LOW": return "bg-emerald-100 text-emerald-800 border border-emerald-200";
      case "MODERATE": return "bg-amber-100 text-amber-800 border border-amber-200";
      case "HIGH": return "bg-orange-100 text-orange-800 border border-orange-200";
      default: return "bg-rose-100 text-rose-800 border border-rose-200";
    }
  }

  // Update Chart.js Doughnut Breakdown
  function updateBreakdownChart(commuteKg, otherKg, elecKg) {
    const ctx = document.getElementById("breakdownDoughnutChart").getContext("2d");

    const dataVals = [commuteKg, otherKg, elecKg];
    const total = dataVals.reduce((a, b) => a + b, 0);

    if (breakdownChart) {
      breakdownChart.data.datasets[0].data = total > 0 ? dataVals : [1, 1, 1];
      breakdownChart.update();
      return;
    }

    breakdownChart = new Chart(ctx, {
      type: "doughnut",
      data: {
        labels: ["Commute", "Other Travel", "Household Power"],
        datasets: [{
          data: dataVals,
          backgroundColor: ["#10b981", "#14b8a6", "#f59e0b"],
          borderWidth: 2,
          borderColor: "#ffffff",
          hoverOffset: 4,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: (context) => {
                const val = context.raw || 0;
                const pct = total > 0 ? ((val / total) * 100).toFixed(1) : 0;
                return ` ${context.label}: ${val.toFixed(1)} kg (${pct}%)`;
              }
            }
          }
        },
        cutout: "70%",
      }
    });
  }

  // Render Machine Learning Card
  function renderMLResults(mlData) {
    const mlPred = mlData.ml_prediction;
    const comp = mlData.comparison;
    const baseline = mlData.factor_baseline;

    document.getElementById("ml-predicted-val").textContent = mlPred.predicted_monthly_co2_kg.toFixed(1);
    document.getElementById("ml-confidence-range").textContent = `95% CI: [${mlPred.confidence_interval_monthly[0]} - ${mlPred.confidence_interval_monthly[1]} kg]`;

    document.getElementById("ml-baseline-val").textContent = baseline.monthly_total_co2_kg.toFixed(1);

    const deltaSign = comp.delta_kg >= 0 ? "+" : "";
    document.getElementById("ml-delta-val").textContent = `${deltaSign}${comp.delta_kg.toFixed(1)}`;
    document.getElementById("ml-delta-pct").textContent = `${deltaSign}${comp.delta_pct}% vs factor model`;

    // Top feature drivers learned
    const featuresContainer = document.getElementById("ml-features-container");
    featuresContainer.innerHTML = "";

    const feats = mlPred.top_features || {};
    const friendlyNames = {
      "per_capita_kwh": "Per-Capita kWh",
      "main_mode_car": "Car Commute",
      "commute_monthly_km": "Commute Monthly km",
      "main_mode_cab": "Cab Commute",
      "vehicle_age": "Vehicle Age Wear",
      "congestion_distance_interaction": "Congestion Exposure",
      "one_way_distance_km": "Distance (km)",
      "main_mode_two_wheeler": "Two-Wheeler",
    };

    Object.entries(feats).slice(0, 4).forEach(([k, v]) => {
      const label = friendlyNames[k] || k;
      const el = document.createElement("div");
      el.className = "bg-slate-700/60 p-2 rounded border border-slate-600/60";
      el.innerHTML = `
        <span class="text-[10px] text-slate-400 block truncate" title="${label}">${label}</span>
        <span class="text-xs font-bold text-emerald-300">${v}%</span>
      `;
      featuresContainer.appendChild(el);
    });
  }

  // Render What-If Scenarios & Bar Chart
  function renderWhatIfScenarios(scenarios, currentCommuteKg, currentModeLabel) {
    const container = document.getElementById("whatif-cards-container");
    container.innerHTML = "";

    scenarios.forEach((sc) => {
      const isPositive = sc.monthly_saved_kg > 0;
      const card = document.createElement("div");
      card.className = `p-3.5 rounded-xl border transition ${
        sc.is_current_mode
          ? "bg-emerald-50/60 border-emerald-300"
          : "bg-slate-50 hover:bg-white border-slate-200"
      }`;

      card.innerHTML = `
        <div class="flex items-center justify-between mb-1.5">
          <span class="font-bold text-xs text-slate-800">${sc.label}</span>
          ${
            sc.is_current_mode
              ? '<span class="text-[10px] font-bold px-1.5 py-0.5 rounded bg-emerald-200 text-emerald-800">Current Mode</span>'
              : `<span class="text-[11px] font-bold ${isPositive ? 'text-emerald-600' : 'text-slate-400'}">${isPositive ? '-' : '+'}${Math.abs(sc.monthly_saved_kg).toFixed(1)} kg/mo</span>`
          }
        </div>
        <p class="text-[11px] text-slate-500 mb-2">${sc.description}</p>
        <div class="flex items-center justify-between text-[10px] pt-1.5 border-t border-slate-200/60 text-slate-600">
          <span>Monthly: <strong>${sc.alternative_monthly_co2_kg.toFixed(1)} kg</strong></span>
          ${
            isPositive
              ? `<span class="text-emerald-700 font-semibold">Saves ${sc.pct_saved}% (🌱 ${sc.annual_trees_saved} trees/yr)</span>`
              : `<span class="text-slate-400">Neutral</span>`
          }
        </div>
      `;
      container.appendChild(card);
    });

    // Update What-If Bar Chart
    updateWhatIfChart(scenarios, currentCommuteKg, currentModeLabel);
  }

  function updateWhatIfChart(scenarios, currentCommuteKg, currentModeLabel) {
    const ctx = document.getElementById("whatIfBarChart").getContext("2d");

    const labels = ["Current Mode", ...scenarios.map((s) => s.label.replace("Shift to ", "").replace("Carpool / ", ""))];
    const dataVals = [currentCommuteKg, ...scenarios.map((s) => s.alternative_monthly_co2_kg)];
    const bgColors = ["#ef4444", "#10b981", "#059669", "#3b82f6", "#06b6d4", "#22c55e"];

    if (whatIfChart) {
      whatIfChart.data.labels = labels;
      whatIfChart.data.datasets[0].data = dataVals;
      whatIfChart.update();
      return;
    }

    whatIfChart = new Chart(ctx, {
      type: "bar",
      data: {
        labels: labels,
        datasets: [{
          label: "Monthly Commute kg CO2e",
          data: dataVals,
          backgroundColor: bgColors,
          borderRadius: 6,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: (context) => ` ${context.raw.toFixed(1)} kg CO2e / month`
            }
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            title: { display: true, text: "kg CO2e / month", font: { size: 10 } }
          },
          x: {
            ticks: {
              maxRotation: 25,
              minRotation: 20,
              font: { size: 9 }
            }
          }
        }
      }
    });
  }

  // Render Printable Carbon Receipt
  function renderReceipt(data) {
    const now = new Date();
    document.getElementById("receipt-timestamp").textContent = now.toLocaleString("en-IN", {
      dateStyle: "medium",
      timeStyle: "short",
    });

    const randId = Math.floor(1000 + Math.random() * 9000);
    document.getElementById("receipt-id").textContent = `REF: BLR-CARB-2026-${randId}`;

    const commute = data.breakdown.commute;
    const other = data.breakdown.other_travel;
    const elec = data.breakdown.electricity;
    const summary = data.summary;

    document.getElementById("rcpt-commute-mode").textContent = commute.mode_label;
    document.getElementById("rcpt-commute-kg").textContent = `${commute.monthly_commute_co2_kg.toFixed(1)} kg`;
    document.getElementById("rcpt-commute-km").textContent = commute.monthly_distance_km;
    document.getElementById("rcpt-commute-rate").textContent = commute.effective_factor_kg_pkm.toFixed(3);
    document.getElementById("rcpt-rush-pct").textContent = `${data.inputs.rush_hour_pct}%`;

    document.getElementById("rcpt-other-mode").textContent = other.mode_label;
    document.getElementById("rcpt-other-kg").textContent = `${other.monthly_other_co2_kg.toFixed(1)} kg`;
    document.getElementById("rcpt-other-km").textContent = other.monthly_distance_km;
    document.getElementById("rcpt-other-weekly").textContent = other.weekly_distance_km;

    document.getElementById("rcpt-elec-kg").textContent = `${elec.monthly_electricity_co2_kg.toFixed(1)} kg`;
    document.getElementById("rcpt-elec-kwh").textContent = elec.per_capita_kwh.toFixed(0);
    document.getElementById("rcpt-elec-members").textContent = elec.household_members;

    document.getElementById("rcpt-total-monthly").textContent = `${summary.monthly_total_co2_kg.toFixed(1)} kg`;
    document.getElementById("rcpt-total-daily").textContent = `${summary.daily_average_co2_kg.toFixed(2)} kg/day`;
    document.getElementById("rcpt-total-annual").textContent = `${summary.annual_total_co2_kg.toFixed(0)} kg/yr`;
    document.getElementById("rcpt-trees").textContent = `${summary.trees_offset_needed} Trees/yr`;
    document.getElementById("rcpt-tier").textContent = summary.tier_label;
  }

  // Render Actionable Recommendations
  function renderRecommendations(tips) {
    const container = document.getElementById("recommendations-container");
    container.innerHTML = "";

    tips.forEach((tip) => {
      const card = document.createElement("div");
      card.className = "p-3 rounded-lg bg-slate-50 border border-slate-200/80 flex items-start space-x-2.5";
      card.innerHTML = `
        <div class="mt-0.5 text-emerald-600">
          <i data-lucide="check-circle-2" class="w-4 h-4"></i>
        </div>
        <div class="flex-1">
          <div class="flex items-center justify-between">
            <span class="text-xs font-bold text-slate-800">${tip.title}</span>
            <span class="text-[10px] font-semibold text-emerald-700 bg-emerald-50 px-1.5 py-0.5 rounded border border-emerald-200">${tip.impact}</span>
          </div>
          <p class="text-[11px] text-slate-600 mt-1 leading-relaxed">${tip.text}</p>
        </div>
      `;
      container.appendChild(card);
    });

    if (window.lucide) window.lucide.createIcons();
  }

  // Setup Event Listeners
  function setupEventListeners() {
    // Mode selection change
    mainModeSelect.addEventListener("change", () => {
      updateModeDescriptions();
      performCalculation();
      performMLPrediction();
    });

    // Distance & Days input
    [oneWayDistInput, commuteDaysInput, otherDistInput, elecKwhInput, elecMembersInput, vehicleAgeInput].forEach((input) => {
      input.addEventListener("input", () => {
        updateInputPreviews();
      });
      input.addEventListener("change", () => {
        performCalculation();
        performMLPrediction();
      });
    });

    // Rush hour slider
    rushHourSlider.addEventListener("input", (e) => {
      rushHourValSpan.textContent = `${e.target.value}%`;
      updateInputPreviews();
    });
    rushHourSlider.addEventListener("change", () => {
      performCalculation();
      performMLPrediction();
    });

    // Other mode select
    otherModeSelect.addEventListener("change", () => {
      performCalculation();
      performMLPrediction();
    });

    // Buttons
    btnCalculate.addEventListener("click", () => {
      performCalculation();
      performMLPrediction();
    });

    btnRunML.addEventListener("click", () => {
      performMLPrediction();
      const mlCard = document.getElementById("ml-card");
      mlCard.scrollIntoView({ behavior: "smooth", block: "center" });
    });

    // Preset buttons
    document.querySelectorAll(".preset-btn").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        const presetKey = btn.getAttribute("data-preset");
        loadPreset(presetKey);
      });
    });

    // Print Receipt
    const printReceiptHandler = () => {
      window.print();
    };
    if (btnPrintNav) btnPrintNav.addEventListener("click", printReceiptHandler);
    if (btnPrintInner) btnPrintInner.addEventListener("click", printReceiptHandler);

    // Reset Form
    btnReset.addEventListener("click", () => {
      loadPreset("twowheeler_rider");
    });
  }

  // Load a demo preset
  function loadPreset(key) {
    if (!presetsData || !presetsData[key]) return;
    const p = presetsData[key].data;

    mainModeSelect.value = p.main_mode;
    oneWayDistInput.value = p.one_way_distance_km;
    commuteDaysInput.value = p.commute_days_per_month;
    rushHourSlider.value = p.rush_hour_pct;
    rushHourValSpan.textContent = `${p.rush_hour_pct}%`;
    vehicleAgeInput.value = p.vehicle_age;
    otherModeSelect.value = p.other_travel_mode;
    otherDistInput.value = p.other_travel_distance_km;
    elecKwhInput.value = p.monthly_electricity_kwh;
    elecMembersInput.value = p.household_members;

    updateModeDescriptions();
    updateInputPreviews();
    performCalculation();
    performMLPrediction();
  }

  // Start app
  initializeApp();
});
