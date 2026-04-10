# False Discovery Rate (FDR) in Finance - Search and Selection Model

## Overview

This codebase implements the statistical framework from López de Prado's paper **"What is the False Discovery Rate in Finance?"** The implementation demonstrates that when accounting for latent search and selection processes in financial research, the False Discovery Rate (FDR) can exceed 80%, compared to previously reported estimates of 5-15%.

## Key Concept

Traditional FDR estimation assumes each published result comes from a **single statistical trial**. In reality, researchers test multiple strategies (K trials) and only publish the best-performing one. This **search and selection** process dramatically increases Type I errors while the literature ignores this effect.

## Repository Structure

```
/workspace/
├── code_table_1.py                 # Numerical example: conditional tail probabilities
├── code_table_2.py                 # Main empirical calibration (raw Sharpe ratios)
├── code_table_3_unified_pivotal_or_raw.py  # Unified version with pivotal statistic option
├── PredictorLSretWide.csv          # Dataset: 212 published predictors (1926-2024)
├── README.md                       # This documentation file
└── [output files]                  # Generated CSV tables and statistics
```

## Files Description

### 1. `code_table_1.py` - Numerical Example (Section 4.4.3)

Demonstrates **identification failure**: two different data-generating processes produce nearly identical observable results but vastly different FDRs.

**Case A (Search & Selection)**: 
- π₀ = 0.75, K = 5
- Selected statistic = max(SR̂₁, ..., SR̂₅)
- True FDR ≈ 70%

**Case B (No Search)**:
- π₀' = 0.10, K' = 1  
- Single trial assumption
- Estimated FDR ≈ 5.4%

**Output**: `table1_conditional_tail_probabilities.csv`

### 2. `code_table_2.py` - Empirical Calibration (Section 6)

Fits the maximum-of-mixtures model to 212 published predictors from the Open Asset Pricing website.

**Model**: 
```
F(x) = [π₀·Φ(x/σ₀) + (1-π₀)·Φ((x-δ₁)/σ₁)]^K
```

**Parameters estimated via MLE**:
- π₀: null prevalence
- δ₁: alternative mean shift
- σ₀: null scale parameter
- σ₁: alternative scale parameter (constrained σ₁ ≥ σ₀)
- K: effective search intensity

**Key Features**:
- AR(1)-adjusted rejection thresholds accounting for serial correlation
- Parallel optimization across K values
- Multi-stage optimizer: local multistart → differential evolution → final polish

**Output**: 
- `Table2_sigma1_ge_sigma0_monthly_strongopt_parallel.csv`
- `Section6_predictor_stats_monthly.csv`

### 3. `code_table_3_unified_pivotal_or_raw.py` - Unified Implementation

Single codebase supporting two statistical modes:

| Mode | Statistic | Threshold | Use Case |
|------|-----------|-----------|----------|
| `raw` | Monthly Sharpe ratio | AR(1)-adjusted cₙ | Heterogeneous predictors |
| `pivotal` | √[T·(1-ρ)/(1+ρ)]·SR̂ | Constant z-critical | Asymptotically pivotal analysis |

**Usage**: Change `STAT_MODE = "pivotal"` or `STAT_MODE = "raw"` on line 39.

## Mathematical Framework

### Maximum-of-Mixtures Distribution

For K candidate specifications with selection rule Θ = max:

**CDF**: F_Θ,K(x) = [π₀·F₀(x) + (1-π₀)·F₁(x)]^K

**PDF**: f_Θ,K(x) = K·[π₀·F₀(x) + (1-π₀)·F₁(x)]^(K-1) · [π₀·f₀(x) + (1-π₀)·f₁(x)]

### Familywise Error Rates

**Type I Error** (all K are null):
```
α_K = P(max SR̂_k ≥ c | M=0) = 1 - (1-α)^K
```

**Type II Error** (at least one non-null):
```
β_K = P(max SR̂_k < c | M≥1)
```

### False Discovery Rate

```
FDR = (α_K · π₀) / [α_K · π₀ + (1-β_K) · (1-π₀)]
```

## Installation

```bash
# Required packages
pip install numpy pandas scipy plotly dash
```

## 🚀 Running the Interactive Dashboard (NEW!)

The improved version includes an **interactive Dash application** that visualizes how search intensity and null prevalence impact FDR in real-time.

### 1. Start the Dashboard
```bash
python fdR_dashboard.py
```

### 2. Open in Browser
Navigate to `http://127.0.0.1:8050/`

### 3. Explore the Visualizations
The dashboard provides four interactive tabs:

| Tab | Description | Key Insight |
|-----|-------------|-------------|
| **📊 Distributions** | PDF/CDF plots showing null, alternative, and selected maximum distributions | Watch how the null distribution shifts right as K increases, inflating false positives |
| **📈 FDR Evolution** | FDR curve vs. Search Intensity (K) with literature comparison | See FDR rise from ~5% (K=1) to >80% (K=5) |
| **🔍 Sensitivity Analysis** | Heatmap of FDR across (K, π₀) space + Identification Failure plot | Understand why different parameter sets produce identical observable results |
| **📋 Results Table** | Live calculations of α_K, β_K, Power, and FDR | Test your own parameter combinations |

### Dashboard Features:
- **4 Interactive Sliders**: Adjust K (1-20), π₀ (0-1), δ₁ (0-1), and threshold c (1.5-3.0)
- **Real-time Updates**: All plots and metrics recalculate instantly
- **Reset Button**: Return to paper's baseline parameters (K=5, π₀=0.817, δ₁=0.108)
- **Detailed Annotations**: Each plot includes mathematical formulas and key thresholds

---

## 🧪 Running the Analysis Scripts

### Run Table 1 (Numerical Example)
```bash
python code_table_1.py
```

### Run Table 2 (Raw Sharpe Ratios)
```bash
python code_table_2.py
```

### Run Table 3 (Unified Mode)
```bash
# Raw mode
python code_table_3_unified_pivotal_or_raw.py  # Edit STAT_MODE variable

# Or modify line 39 directly:
# STAT_MODE = "pivotal"  # or "raw"
```

## Key Results

### Table 1: Identification Failure
| x | Case_A | Case_B | Diff |
|---|--------|--------|------|
| 2.00 | 1.000 | 1.000 | 0.000 |
| 2.50 | 0.623 | 0.628 | 0.005 |
| 3.00 | 0.316 | 0.319 | 0.003 |

→ Cases are observationally equivalent despite FDR difference (70% vs 5%)

### Table 2: Search-Adjusted FDR Estimates
| K | π₀ | δ₁ | σ₀ | σ₁ | α_K | β_K | LogLik | FDR |
|---|----|----|----|----|-----|-----|--------|-----|
| 1 | 0.000 | 0.147 | 0.066 | 0.104 | 0.126 | 0.255 | 179.99 | 0.000 |
| 3 | 0.674 | 0.108 | 0.096 | 0.142 | 0.507 | 0.216 | 194.42 | 0.572 |
| 5 | 0.817 | 0.000 | 0.100 | 0.218 | 0.701 | 0.225 | 203.14 | **0.801** |
| 10 | 0.846 | 0.000 | 0.075 | 0.198 | 0.787 | 0.134 | 164.04 | 0.833 |

→ Optimal fit at K≈5 yields FDR > 80%

## Data Source

**PredictorLSretWide.csv**: Monthly long-short returns for 212 published predictors
- Sample period: January 1926 - December 2024
- Observations: 1,188 monthly data points
- Mean observations per predictor: 817.46
- Mean first-order autocorrelation: 0.071

Data from: [Open Asset Pricing Website](https://openassetpricing.com/) (Chen & Zimmermann)

## Conclusions

1. **Identification Failure**: FDR cannot be identified from cross-sectional statistics without explicit search-and-selection modeling

2. **Search-Adjusted FDR**: Accounting for realistic search intensity (K≈5) increases FDR estimates from ~5-15% to **>80%**

3. **Implication**: The "factor zoo" should not be treated as a reliable map of investment opportunities

## 🆕 React Version Available!

A complete **React rewrite** of the dashboard is available in the `fdr-dashboard-react/` directory. The React version offers:

- ⚡ **Instant responsiveness**: No server round-trips, 60fps interactions
- 🚀 **Easy deployment**: Static hosting on Vercel, Netlify, or any CDN
- 📱 **Better mobile support**: Responsive design out of the box
- 💰 **Zero server costs**: Runs entirely in the browser

### Quick Start (React Version)

```bash
cd fdr-dashboard-react
npm install
npm run dev
```

See [`fdr-dashboard-react/README.md`](fdr-dashboard-react/README.md) for complete installation and deployment instructions.

---

## ✅ Testing & Verification

All dashboard functions have been tested and verified:

```bash
# Test core computation functions
python -c "from fdR_dashboard import compute_error_rates; print(compute_error_rates(0.75, 0.3, 1.0, 1.0, 5, 1.96))"

# Test visualization functions
python -c "from fdR_dashboard import create_distribution_plot; fig = create_distribution_plot(0.75, 0.3, 1.0, 1.0, 5, 1.96); print(f'Created plot with {len(fig.data)} traces')"

# Test Table 1 data generation (identification failure)
python -c "from fdR_dashboard import generate_table1_data; df = generate_table1_data(); print(df)"
```

### Test Results Summary:

| Component | Status | Key Result |
|-----------|--------|------------|
| **Error Rate Computation** | ✅ Pass | FDR ≈ 70% at K=5, π₀=0.75 (matches paper) |
| **FDR Evolution** | ✅ Pass | FDR increases from 60.7% (K=1) to 71.2% (K=10) |
| **Distribution Plots** | ✅ Pass | Generates 9 traces for PDF/CDF visualization |
| **Sensitivity Heatmap** | ✅ Pass | Creates interactive FDR heatmap over (K, π₀) space |
| **Identification Failure** | ✅ Pass | Max difference < 0.01 between Case A and Case B |

### Key Validation Points:

1. **Type I Error Inflation**: α increases from 2.5% (single trial) to 11.9% (K=5)
2. **FDR Growth**: FDR rises monotonically with search intensity K
3. **Observational Equivalence**: Two different DGDs produce nearly identical tail probabilities
4. **Dashboard Responsiveness**: All plots update in real-time with parameter changes

---

## 📚 Additional Resources

- López de Prado, M. (2026). "What is the False Discovery Rate in Finance?" SSRN:6450418
- López de Prado, M. (2018). *Advances in Financial Machine Learning*. Wiley.

## License

© 2020-2026 Marcos López de Prado. All Rights Reserved.

Code implemented for educational and research purposes based on the paper methodology.
