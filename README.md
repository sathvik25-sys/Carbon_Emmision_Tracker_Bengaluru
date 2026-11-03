# Bengaluru Carbon Emission Tracker
### Machine Learning & Tier-1 Factor Estimator for Daily Commuting and Household Electricity

> **Academic Student Project Prototype — Bengaluru, Karnataka, India**  
> *Estimation of personal monthly carbon emissions from urban travel and household electricity, featuring an itemized "Carbon Receipt", interactive "What-If" transit mode comparison, and a non-linear Machine Learning regressor.*

---

## 🌟 Highlights & Key Features

1. **Clean, Responsive Web Application**
   - Modern, mobile-responsive single-page web UI built with Tailwind CSS, Chart.js, and Lucide icons.
   - Dual interface options: Full-stack **FastAPI** web application (`app.py`) and companion **Streamlit** dashboard (`streamlit_app.py`).

2. **Bengaluru Urban Mobility Context**
   - Tailored transit modes: **Walk/Cycle**, **Namma Metro (BMRCL)**, **BMTC Bus**, **Auto Rickshaw (3-Wheeler)**, **Two-Wheeler (Motorcycle/Scooter)**, **Personal Car**, and **Cab/Taxi (Uber/Ola)**.
   - **Bengaluru Rush-Hour Congestion Surcharge**: Accounts for heavy stop-and-go idling (e.g. Silk Board, Outer Ring Road, Tin Factory), adding up to +35% fuel penalty for ICE vehicles, while grade-separated Namma Metro remains congestion-free.
   - **Vehicle Ageing Degradation**: Models catalytic converter wear and older BS emission standards (+2.0%/year capped at +30%).

3. **Household Electricity & Per-Capita Scaling**
   - Evaluates monthly kWh from BESCOM electricity bills.
   - Factors per-capita division across household members (`Per-Capita kWh = Total kWh / Members`), strictly protecting against zero division.
   - Uses the **Central Electricity Authority (CEA)** Southern Regional Grid emission baseline (0.716 kg CO2e / kWh).

4. **Itemized "Carbon Receipt"**
   - Styled after retail receipts with itemized breakdown per activity: commute, other travel, and electricity.
   - Shows monthly kg CO2e, daily average, annualized projection, tree offset requirement (@ 21 kg CO2/tree/yr), and footprint status tier.
   - One-click print/save button formatted for clean printing.

5. **Interactive "What-If" Transit Scenario Simulator**
   - Compares your current commute against cleaner alternatives: Namma Metro, BMTC City Bus, Carpooling (2 people), Electric 2-Wheeler (EV), and Walking/Cycling.
   - Calculates monthly emissions saved, percentage reduction, and annual trees saved, visualized in an interactive bar chart.

6. **Machine Learning Non-Linear Model**
   - Trained Gradient Boosting Regressor (`carbon_regressor.joblib`) modeling complex non-linear interactions between distance, peak-hour congestion, vehicle age, and household electricity.
   - Evaluation metrics: **R² = 0.9874**, **MAE = 3.99 kg CO2e**.
   - Displays 95% confidence intervals, residual delta against the deterministic baseline, and top learned feature drivers.
   - **Methodological disclosure**: Clearly labeled as an academic demonstration trained on a simulated dataset of 5,000 Bengaluru commuter activity patterns.
   - **Reliable Fallback**: If the model artifact is missing or disabled, the application seamlessly falls back to the deterministic Tier-1 calculator.

7. **Instant Demonstration Presets**
   - 5 pre-configured Bengaluru commuter profiles for immediate 1-click evaluation:
     - 🚗 *Whitefield Techie* (Solo car driver in Silk Board congestion)
     - 🚇 *Indiranagar Metro Commuter* (Purple Line rapid transit user)
     - 🛵 *Electronic City Rider* (Daily 125cc petrol scooter commuter)
     - 🚌 *Koramangala Student* (BMTC bus + walking)
     - 💻 *HSR Layout Freelancer* (Remote work-from-home, high electricity share)

---

## 📁 Repository Structure

```
carbon_tracker/
├── app.py                      # FastAPI web server and REST API
├── calculator.py               # Deterministic Tier-1 calculator & What-If engine
├── config.py                   # Emission factors, constants, and demo presets
├── dataset_generator.py        # Synthetic Bengaluru commuter dataset generator
├── ml_engine.py                # Machine learning training, evaluation & inference
├── cli.py                      # Terminal CLI tool for instant testing
├── streamlit_app.py            # Optional companion Streamlit dashboard
├── requirements.txt            # Python dependencies
├── README.md                   # Complete documentation & demonstration guide
├── static/
│   ├── css/
│   │   └── style.css           # Thermal receipt styles, print media rules, and UI polish
│   └── js/
│       └── app.js              # Reactive UI, Chart.js charts, and preset handlers
├── templates/
│   └── index.html              # Single-page application HTML template
├── data/
│   └── bengaluru_commute_dataset.csv # 5,000 synthetic commuter activity records
├── models/
│   ├── carbon_regressor.joblib  # Trained scikit-learn Gradient Boosting model
│   └── model_metadata.json     # Model metrics, R², MAE, RMSE, and feature importances
└── tests/
    ├── __init__.py
    ├── test_calculator.py      # Core math, edge cases, zero division, and schema validation
    ├── test_ml_engine.py       # ML predictions, confidence intervals, and fallback handling
    └── test_api.py             # FastAPI REST endpoints and status codes
```

---

## 🚀 Quickstart & Setup

### 1. Prerequisites
- Python 3.10+ (Tested on Python 3.14.2)
- Modern web browser (Chrome, Edge, Firefox, Safari)

### 2. Install Dependencies
```bash
cd C:\Users\sathv\.gemini\antigravity\scratch\carbon_tracker
pip install -r requirements.txt
```

### 3. Run the Web Application (Recommended)
Launch the primary FastAPI full-stack web application:
```bash
python app.py
```
Open your browser at **[http://127.0.0.1:8000](http://127.0.0.1:8000)**.

### 4. Run the Streamlit Dashboard (Alternative)
If your evaluators prefer Streamlit:
```bash
streamlit run streamlit_app.py
```

### 5. Run via Command Line Interface (CLI)
You can test any profile directly in your terminal:
```bash
# Run with a preset profile
python cli.py --preset whitefield_techie

# Run with custom parameters
python cli.py --mode car --distance 16.5 --days 22 --rush-hour 75 --vehicle-age 5 --kwh 220 --members 2
```

---

## 🧪 Running Automated Tests

Run the full test suite using Python's built-in `unittest` runner:
```bash
python -m unittest discover tests -v
```
All 25 tests verify:
- Deterministic calculation formulas against manual hand calculations.
- Active mobility (walk/cycle) producing 0 tailpipe emissions.
- Namma Metro grade-separation having zero road congestion penalty.
- Traffic congestion penalties and vehicle age degradation caps (+30% max).
- Division-by-zero protection (e.g. household members <= 0).
- Negative input prevention and realistic upper bounds (distance <= 300 km, days <= 31).
- What-If savings calculations and tree sequestration math.
- ML inference output structure, confidence intervals, and reliable fallback handling.
- FastAPI REST endpoints (`/`, `/api/config`, `/api/presets`, `/api/calculate`, `/api/predict`, `/api/health`).

---

## 📊 Emission Factors & Calculation Methodology

| Mode / Source | Base Factor | Unit | Source & Bengaluru Context | Congestion Sensitive? |
| :--- | :---: | :---: | :--- | :---: |
| **Walk / Cycle** | 0.000 | kg CO2e / km | Zero tailpipe operational emissions | No |
| **Namma Metro (BMRCL)** | 0.018 | kg CO2e / pkm | Electric rapid transit on Southern Grid; 60% avg load factor; regenerative braking | No (Grade-separated) |
| **BMTC Bus** | 0.028 | kg CO2e / pkm | BMTC urban fleet average across Diesel, EV, and Vajra buses (~40 passenger occupancy) | Yes (up to +15%) |
| **Two-Wheeler** | 0.048 | kg CO2e / pkm | 100-150cc 4-stroke petrol commuter scooter/motorcycle, solo rider (ARAI standard) | Yes (up to +20%) |
| **Auto Rickshaw** | 0.065 | kg CO2e / pkm | LPG/CNG 4-stroke 3-wheeler in Bengaluru city traffic; avg 1.3 passenger load | Yes (up to +25%) |
| **Personal Car** | 0.155 | kg CO2e / pkm | ICE petrol/diesel passenger car in urban stop-and-go driving (1.2 passenger occupancy) | Yes (up to +35%) |
| **Cab / Taxi (Uber/Ola)** | 0.185 | kg CO2e / pkm | Ride-hailing sedan/hatchback including 20% deadhead/empty cruising mileage | Yes (up to +35%) |
| **Household Electricity** | 0.716 | kg CO2e / kWh | Central Electricity Authority (CEA) Baseline Database for Southern Regional Grid / BESCOM | N/A |

### Calculation Formulas
1. **Commute Monthly Emissions**:
   $$\text{Monthly Commute CO}_2 = (\text{One-Way Distance} \times 2 \times \text{Days}) \times \text{Base Factor} \times (1 + \text{Congestion Penalty}) \times (1 + \text{Age Penalty})$$
2. **Household Electricity (Per-Capita)**:
   $$\text{Personal Monthly Electricity CO}_2 = \frac{\text{Household Monthly kWh}}{\max(1, \text{Members})} \times 0.716 \text{ kg CO}_2\text{e/kWh}$$
3. **Other Travel Monthly Emissions**:
   $$\text{Other Travel CO}_2 = \left(\text{Weekly Distance} \times \frac{52}{12}\right) \times \text{Base Factor}$$
4. **Tree Offset Requirement**:
   $$\text{Trees Needed} = \left\lceil \frac{\text{Monthly Total CO}_2 \times 12}{21.0 \text{ kg CO}_2/\text{tree/year}} \right\rceil$$

---

## 🤖 Machine Learning Model Details

- **Model Architecture**: Scikit-Learn `Pipeline` with `ColumnTransformer` (StandardScaler for numerical features, OneHotEncoder for transit modes) and `GradientBoostingRegressor` (150 estimators, learning rate = 0.08, max depth = 4).
- **Dataset**: 5,000 synthetic Bengaluru commuter activity patterns generated via `dataset_generator.py` reflecting realistic distributions of travel distances, mode splits, rush-hour exposure, and BESCOM power consumption.
- **Evaluation Metrics**:
  - Test Set $R^2$: **0.9874**
  - Test MAE: **3.99 kg CO2e**
  - Test RMSE: **5.12 kg CO2e**
- **Top Learned Feature Drivers**:
  1. Per-Capita Electricity Consumption (43.97%)
  2. Mode: Personal Car (16.51%)
  3. Commute Monthly Distance in km (15.44%)
  4. Mode: Cab/Taxi (13.85%)
  5. Vehicle Age Engine Wear (4.61%)
  6. Congestion Exposure Interaction (1.82%)
- **Academic Disclosure**: In accordance with project requirements, the ML model is clearly identified in the UI and documentation as an academic demonstration of multi-variable non-linear regression using simulated data. The factor-based calculator serves as the verified production standard.

---

## 🎓 Student Demonstration Walkthrough Script

When demonstrating this project to professors, evaluators, or project reviewers, follow this 4-step sequence:

1. **Step 1: Baseline Demonstration with a Preset (30 seconds)**
   - Click the top demo preset button: **`🚗 Whitefield Techie (Car)`**.
   - Point out that the form auto-populates with realistic Bengaluru parameters (18 km commute across Outer Ring Road, 85% rush hour, 6-year-old car, 260 kWh BESCOM power).
   - Show the resulting **299.5 kg CO2e/month** total (marked as *Intensive Footprint*), requiring **172 trees/year** to offset.

2. **Step 2: Inspecting the "Carbon Receipt" & Breakdown (30 seconds)**
   - Scroll to the itemized thermal **Carbon Receipt**.
   - Show how each line item separates commute fuel, other travel, and per-capita BESCOM electricity.
   - Click the **"Print / Save"** button to show the print-ready receipt view.

3. **Step 3: Evaluating "What-If" Alternatives (45 seconds)**
   - Show the **"What-If" Commute Scenario Simulator**.
   - Point out that shifting the Whitefield commute from solo car to **Namma Metro** reduces commute emissions from **178.4 kg to 14.3 kg** (**92.0% reduction**), saving **164 kg CO2e/month** and equivalent to planting **94 trees/year**.
   - Point out intermediate alternatives like carpooling (2 pax) saving 65.6% emissions.

4. **Step 4: Machine Learning Non-Linear Model Analysis (45 seconds)**
   - Highlight the **Machine Learning Model card**.
   - Point out the side-by-side comparison between the deterministic factor baseline and the ML regressor.
   - Explain the feature importance ranking (why per-capita power and car mileage dominate urban footprint).
   - Point out the academic disclosure banner, explaining that the ML pipeline models non-linear congestion interactions, with a zero-downtime fallback to the Tier-1 factor engine.

---

## 📌 Assumptions & Limitations

1. **Synthetic Commuter Data**: Due to the absence of public micro-level commuter travel diaries for Bengaluru, the ML model is trained on a simulated dataset reflecting Bengaluru urban mobility statistics. For production city deployment, the dataset generator can be replaced with real DULT (Directorate of Urban Land Transport) or BMTC survey data.
2. **Vehicle Fleets**: Personal car emissions assume an average petrol/diesel hatchback/sedan with 1.2 passenger occupancy. Heavy SUVs or dedicated electric cars (EVs) can be added as separate subcategories.
3. **Electricity Time-of-Day**: The grid emission factor of 0.716 kg CO2e/kWh represents the annual average grid emission baseline from the Central Electricity Authority. It does not account for hourly time-of-day solar peak variations.
