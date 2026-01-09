# Comprehensive Financial Model Analysis: NVIDIA Valuation (January 2025)

## Executive Summary

This is a sophisticated **Discounted Cash Flow (DCF) valuation model** for NVIDIA Corporation, structured as a sum-of-the-parts analysis with three distinct business segments. The model was created by Professor Aswath Damodaran (NYU Stern School of Business) and incorporates his signature "story-to-numbers" valuation framework.

**Key Finding:** The model estimates NVIDIA's intrinsic value at **$77.51 per share** versus a market price of **$123.00**, implying the stock is **58.7% overvalued** based on the input assumptions.

---

## Model Architecture & Data Flow

### Sheet Dependencies Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          REFERENCE DATA LAYER                                │
├─────────────────────────────────────────────────────────────────────────────┤
│  Country Equity Risk Premiums  │  Industry Averages (US)  │  Industry Beta  │
│  (190+ countries, Moody's      │  (93 industries, Beta,   │  (Global)       │
│   ratings, default spreads)    │   margins, ROIC, etc.)   │                 │
└────────────────┬───────────────┴────────────┬─────────────┴────────┬────────┘
                 │                            │                      │
                 ▼                            ▼                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SUPPORTING CALCULATORS                               │
├─────────────────────────────────────────────────────────────────────────────┤
│  Cost of Capital    │  Synthetic Rating  │  R&D Converter   │  Op Lease     │
│  Worksheet          │  (ICR→Rating→     │  (Capitalize     │  Converter    │
│  (4 approaches)     │   Default Spread)  │   R&D, 5yr)      │  (Debt adj)   │
│                     │                    │                  │               │
│  Failure Rate       │  Option Value      │                  │               │
│  Worksheet          │  (Black-Scholes)   │                  │               │
└────────────┬────────┴─────────┬──────────┴────────┬─────────┴───────┬───────┘
             │                  │                   │                 │
             ▼                  ▼                   ▼                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            INPUT SHEET                                       │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────┐  │
│  │ Company Data    │  │ Value Drivers   │  │ Override Assumptions        │  │
│  │ - Revenues      │  │ - Growth rates  │  │ - Stable cost of capital    │  │
│  │ - EBIT          │  │ - Op margin     │  │ - Stable ROIC               │  │
│  │ - Debt/Equity   │  │ - Sales/Capital │  │ - Failure probability       │  │
│  │ - Cash          │  │                 │  │ - Reinvestment lag          │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────────────────┘  │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                    SEGMENT-SPECIFIC INPUTS                            │   │
│  │  AI Chips: Market $80B→$300B, Share 80%→60%, Margin 65%→60%          │   │
│  │  Auto Chips: Market $20B→$200B, Share 6%→15%, Margin 65%→60%         │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          VALUATION OUTPUT                                    │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │               10-YEAR PROJECTIONS (3 SEGMENTS)                         │ │
│  │  For each segment: Revenue → Margin → EBIT → Tax → EBIT(1-t)          │ │
│  │                    → Reinvestment → FCFF → PV(FCFF)                   │ │
│  │  + Terminal Value calculation using Gordon Growth Model                │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                    ▼                                         │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                    VALUATION BRIDGE                                    │ │
│  │  Value of Operating Assets (sum of 3 segments)                        │ │
│  │  - Adjustment for Failure Probability                                  │ │
│  │  - Debt                                                                │ │
│  │  - Minority Interests                                                  │ │
│  │  + Cash                                                                │ │
│  │  + Non-operating Assets                                                │ │
│  │  - Employee Stock Options (Black-Scholes)                              │ │
│  │  = Equity Value → ÷ Shares → Value per Share                          │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  OUTPUT SHEETS: Stories to Numbers │ Valuation as Picture │ Diagnostics    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Detailed Component Analysis

### 1. INPUT SHEET (Cells A1:N86)

**Purpose:** Central control panel for all valuation assumptions

#### A. Company Fundamentals (Base Year Data)

| Input | Cell | Value | Description |
|-------|------|-------|-------------|
| Valuation Date | B3 | Jan 1, 2025 | Model reference date |
| Revenues (TTM) | B10 | $113,269M | Trailing 12-month revenues |
| Operating Income | B11 | $71,033M | EBIT |
| Interest Expense | B12 | $249M | Used for cost of debt |
| Book Value of Equity | B13 | $65,899M | For invested capital |
| Book Value of Debt | B14 | $10,225M | Total debt |
| Cash & Securities | B17 | $38,487M | Non-operating assets |
| Shares Outstanding | B20 | 24,490M | Fully diluted |
| Current Stock Price | B21 | $123 | Market price |
| Effective Tax Rate | B22 | 13.5% | Current tax rate |
| Marginal Tax Rate | B23 | 25% | Target tax rate |

#### B. Value Driver Inputs

| Driver | Cell | Value | Role |
|--------|------|-------|------|
| Revenue Growth (Yr 1) | B25 | 15% | First year growth |
| Operating Margin (Yr 1) | B26 | 65% | Next year margin |
| Target Margin | B28 | 60% | Convergence target |
| Convergence Year | B29 | 5 | Years to reach target margin |
| Sales/Capital (Yrs 1-5) | B30 | 2.5 | Reinvestment efficiency |
| Sales/Capital (Yrs 6-10) | B31 | 2.5 | Later years efficiency |
| Risk-free Rate | B33 | 4.7% | 10-yr Treasury proxy |

#### C. Segment-Specific Inputs

**AI Chip Business (Rows 42-46):**

| Metric | Current | Year 10 | Interpretation |
|--------|---------|---------|----------------|
| Total Market | $80,000M | $300,000M | 3.75x market growth |
| NVIDIA Share | 80% | 60% | Assumes competitive erosion |
| Operating Margin | 65% | 60% | Premium margins persist |

**Auto Chip Business (Rows 48-52):**

| Metric | Current | Year 10 | Interpretation |
|--------|---------|---------|----------------|
| Total Market | $20,000M | $200,000M | 10x market growth |
| NVIDIA Share | 6% | 15% | Major share gains |
| Operating Margin | 65% | 60% | Premium margins |

#### D. Override Assumptions (Rows 54-83)

Key overrides used in this model:

- **Stable Cost of Capital:** 8.5% (overridden from default RF + 4.5%)
- **Stable ROIC:** 20% (overridden from cost of capital assumption)
- **Reinvestment Lag:** 3 years (from default 1 year)
- **Failure Probability:** 0% (no distress adjustment)

---

### 2. COST OF CAPITAL WORKSHEET (Complex Multi-Method Calculator)

**Purpose:** Calculate WACC using one of four approaches

#### Four Available Approaches:

1. **Direct Input** - User specifies WACC directly
2. **Detailed Calculation** (Selected for this model) - Full bottom-up computation
3. **Industry Average** - Uses industry average adjusted for risk-free rate
4. **Histogram Method** - Uses percentile-based global WACC distribution

#### Detailed Calculation Components:

**Cost of Equity (CAPM):**

```
Cost of Equity = Rf + β_levered × ERP

Where:
- Rf = 4.70% (10-year Treasury)
- β_unlevered = 1.4602 (from Industry Averages for Semiconductor)
- β_levered = 1.4635 (adjusted for NVIDIA's debt ratio)
- ERP = 4.86% (revenue-weighted by operating countries)

Cost of Equity = 4.70% + 1.4635 × 4.86% = 11.82%
```

**Equity Risk Premium Calculation (Operating Countries Method):**

| Country | Revenue | ERP | Weight | Contribution |
|---------|---------|-----|--------|--------------|
| United States | $26,966M | 4.33% | 44.26% | 1.92% |
| China | $10,306M | 5.27% | 16.92% | 0.89% |
| Taiwan | $13,405M | 5.13% | 22.00% | 1.13% |
| Rest of World | $10,245M | 5.50% | 16.82% | 0.92% |
| **Total** | $60,922M | | 100% | **4.86%** |

**Cost of Debt:**

- Rating Approach: Actual rating (A2/A)
- Pre-tax Cost of Debt: 6.12% (RF 4.70% + Default Spread 1.42%)
- After-tax Cost of Debt: 4.59% (6.12% × (1 - 25%))

**WACC Calculation:**

```
WACC = (E/V × Cost of Equity) + (D/V × After-tax Cost of Debt)
WACC = (99.69% × 11.82%) + (0.31% × 4.59%)
WACC = 11.79%
```

---

### 3. R&D CONVERTER

**Purpose:** Capitalize R&D expenses to correctly reflect economic earnings

**Methodology:**

- Amortization Period: 5 years
- Current Year R&D: $11,665M
- Historical R&D expenses are amortized on a straight-line basis

**Calculations:**

| Year | R&D Expense | Unamortized | Amortization |
|------|-------------|-------------|--------------|
| Current | $11,665M | 100% | - |
| -1 | $8,675M | 80% | $1,735M |
| -2 | $7,339M | 60% | $1,468M |
| -3 | $5,268M | 40% | $1,054M |
| -4 | $3,924M | 20% | $785M |
| -5 | $2,829M | 0% | $566M |

**Results:**

- Capitalized R&D Asset: $25,900M (added to invested capital)
- Annual Amortization: $5,607M
- Operating Income Adjustment: +$6,058M (R&D - Amortization)

---

### 4. VALUATION OUTPUT (Core Engine)

**Purpose:** Project financials for 10 years and calculate present values

#### Three-Segment DCF Structure:

**Segment 1: REST (Gaming/Other) - Rows 2-10**

Revenue projection formula (Row 3):

```
Year N Revenue = Year N-1 Revenue × (1 + Growth Rate)
```

Growth rate evolution:

- Years 1-5: 15% (flat)
- Years 6-10: Linear decline from 15% to 4.7% (risk-free rate)

Margin convergence formula (Row 4):

```
If Year > Convergence Year:
    Margin = Target Margin
Else:
    Margin = Target - ((Target - Current) / Convergence Years) × (Convergence Year - Current Year)
```

**Segment 2: AI CHIPS - Rows 12-19**

Total market evolution:

```
Years 1-5: Linear interpolation from $80B to $212B
Years 6-10: Linear interpolation to $300B (60% of growth in first 5 years)
```

Market share erosion:

```
Market Share_Year N = 80% - (80% - 60%) × (N/10)
Linear decline over 10 years
```

**Segment 3: AUTO CHIPS - Rows 21-28**

Total market evolution:

```
Years 1-5: Linear to $140B (higher early growth)
Years 6-10: Linear to $200B
```

Market share gain:

```
Market Share_Year N = 6% + (15% - 6%) × (N/10)
Linear increase over 10 years
```

#### Reinvestment Calculation (Rows 8, 18, 27):

With 3-year lag override:

```
Reinvestment_Year N = (Revenue_Year N+3 - Revenue_Year N+2) / Sales-to-Capital Ratio
```

This means investments made today drive revenue growth 3 years later.

#### Terminal Value (Row 9, 19, 28 Column N):

Gordon Growth Model:

```
Terminal Value = FCFF_Terminal / (Cost of Capital_Stable - Growth Rate_Stable)
Terminal Value = FCFF × (1 + g) / (WACC - g)

Where:
- g = Risk-free rate = 4.7%
- WACC_stable = 8.5% (overridden)
```

#### Discount Factors (Rows 30-31):

Time-varying cost of capital:

- Years 1-5: 11.79% (current WACC)
- Years 6-10: Linear decline from 11.79% to 8.5%

Cumulated discount factor:

```
CDF_Year N = CDF_Year N-1 × (1 / (1 + WACC_Year N))
```

---

### 5. VALUATION BRIDGE (Rows 37-54)

**Equity Value Build-Up:**

| Component | Value | Calculation |
|-----------|-------|-------------|
| **PV of FCFFs (Years 1-10)** | | |
| - Rest Segment | $249,284M | Sum of discounted FCFFs |
| - AI Segment | $371,215M | Sum of discounted FCFFs |
| - Auto Segment | $32,055M | Sum of discounted FCFFs |
| **PV of Terminal Values** | | |
| - Rest Segment | $500,944M | TV × Year 10 DF |
| - AI Segment | $612,270M | TV × Year 10 DF |
| - Auto Segment | $102,045M | TV × Year 10 DF |
| **Total Segment Values** | | |
| - Rest (Gaming/Other) | $750,229M | 40.2% |
| - AI Chips | $983,484M | 52.7% |
| - Auto Chips | $134,100M | 7.2% |
| **Going Concern Value** | **$1,867,813M** | |
| × (1 - Prob of Failure) | × 100% | 0% failure assumed |
| + Distress Proceeds | $0M | |
| **Operating Assets** | $1,867,813M | |
| - Total Debt | ($10,225M) | |
| - Minority Interests | $0M | |
| + Cash | $38,487M | |
| + Non-operating Assets | $2,237M | |
| **Equity Value** | $1,898,312M | |
| - Employee Options | $0M | Disabled in this run |
| **Equity in Common Stock** | $1,898,312M | |
| ÷ Shares Outstanding | 24,490M | |
| **Value per Share** | **$77.51** | |
| Market Price | $123.00 | |
| **Price/Value** | **158.7%** | **Overvalued by 58.7%** |

---

### 6. SUPPORTING WORKSHEETS

#### A. Synthetic Rating (Credit Analysis)

Estimates bond rating from Interest Coverage Ratio (ICR):

```
ICR = EBIT / Interest Expense = $71,033M / $249M = 285×

For large manufacturing firms:
ICR > 8.5 → AAA rating → Default spread = 0.69%
```

NVIDIA qualifies for AAA, but the model uses actual A2/A rating.

#### B. Option Value (Black-Scholes)

When enabled, values employee stock options:

```
Inputs:
- Stock Price: $123
- Strike Price: $1.29
- Maturity: 7 years
- Volatility: 45%
- Options Outstanding: 7.72M

Option Value = Black-Scholes adjusted for dilution
```

(Currently disabled in this model run)

#### C. Failure Rate Worksheet

Two approaches:

1. **Bond Rating Based:** 10-year default probability by rating
2. **Age-Based:** Industry-specific failure rates for young companies

#### D. Operating Lease Converter

Converts operating leases to debt equivalent:

```
Lease Commitments → PV at cost of debt → Add to debt
Depreciation → Adjust operating income
```

(Not used - Operating leases = "No")

---

### 7. DIAGNOSTICS SHEET

**Purpose:** Sanity check assumptions against industry benchmarks

| Metric | Company | Industry | Status |
|--------|---------|----------|--------|
| Revenue Growth (Recent) | 128.62% | 5.13% | Far above average |
| Revenue Growth (Forecast Y1) | 24.75% | 5.13% | Above average |
| Operating Margin | 72.21% | 29.71% | Exceptional |
| ROIC (Current) | 104.95% | 21.14% | Exceptional |
| ROIC (Year 10) | 114.32% | - | Still very high |
| Sales/Capital | 2.50 | 1.10 | More efficient |

**Key Diagnostic:** Value/Price = 63%, suggesting model estimates stock is overvalued.

---

## 10-Year Financial Projections

### REST (Gaming/Other) Segment

| Year | Rev Growth | Revenues | Op Margin | EBIT | EBIT(1-t) | Reinvest | FCFF |
|------|------------|----------|-----------|------|-----------|----------|------|
| Base | - | $48,069M | 72.21% | $34,711M | $30,025M | - | - |
| 1 | 15.00% | $55,279M | 65.00% | $35,932M | $31,081M | $4,386M | $26,694M |
| 2 | 15.00% | $63,571M | 63.00% | $40,050M | $34,643M | $5,044M | $29,599M |
| 3 | 15.00% | $73,107M | 62.00% | $45,326M | $39,207M | $5,004M | $34,203M |
| 4 | 15.00% | $84,073M | 61.00% | $51,285M | $44,361M | $4,752M | $39,609M |
| 5 | 15.00% | $96,684M | 60.00% | $58,010M | $50,179M | $4,272M | $45,907M |
| 6 | 12.94% | $109,195M | 60.00% | $65,517M | $55,165M | $3,563M | $51,603M |
| 7 | 10.88% | $121,075M | 60.00% | $72,645M | $59,496M | $2,644M | $56,852M |
| 8 | 8.82% | $131,754M | 60.00% | $79,052M | $62,926M | $2,769M | $60,157M |
| 9 | 6.76% | $140,661M | 60.00% | $84,396M | $65,238M | $2,899M | $62,340M |
| 10 | 4.70% | $147,272M | 60.00% | $88,363M | $66,272M | $3,035M | $63,237M |
| Term | 4.70% | $154,193M | 60.00% | $92,516M | $69,387M | $16,306M | $53,081M |

### AI Chip Segment

| Year | Total Mkt | Mkt Share | Revenues | Op Margin | EBIT(1-t) | FCFF |
|------|-----------|-----------|----------|-----------|-----------|------|
| Base | $80,000M | 80.00% | $64,000M | 65.00% | $35,984M | - |
| 1 | $106,400M | 78.00% | $82,992M | 65.00% | $46,662M | $40,333M |
| 2 | $132,800M | 76.00% | $100,928M | 63.00% | $55,001M | $49,094M |
| 3 | $159,200M | 74.00% | $117,808M | 62.00% | $63,180M | $60,089M |
| 4 | $185,600M | 72.00% | $133,632M | 61.00% | $70,511M | $67,701M |
| 5 | $212,000M | 70.00% | $148,400M | 60.00% | $77,020M | $74,492M |
| 6 | $229,600M | 68.00% | $156,128M | 60.00% | $78,876M | $76,629M |
| 7 | $247,200M | 66.00% | $163,152M | 60.00% | $80,173M | $78,208M |
| 8 | $264,800M | 64.00% | $169,472M | 60.00% | $80,940M | $77,556M |
| 9 | $282,400M | 62.00% | $175,088M | 60.00% | $81,206M | $77,663M |
| 10 | $300,000M | 60.00% | $180,000M | 60.00% | $81,000M | $77,290M |

### Auto Chip Segment

| Year | Total Mkt | Mkt Share | Revenues | Op Margin | EBIT(1-t) | FCFF |
|------|-----------|-----------|----------|-----------|-----------|------|
| Base | $20,000M | 6.00% | $1,200M | 65.00% | $675M | - |
| 1 | $44,000M | 6.90% | $3,036M | 65.00% | $1,707M | $454M |
| 2 | $68,000M | 7.80% | $5,304M | 63.00% | $2,890M | $1,465M |
| 3 | $92,000M | 8.70% | $8,004M | 62.00% | $4,293M | $3,241M |
| 4 | $116,000M | 9.60% | $11,136M | 61.00% | $5,876M | $4,738M |
| 5 | $140,000M | 10.50% | $14,700M | 60.00% | $7,629M | $6,405M |
| 6 | $152,000M | 11.40% | $17,328M | 60.00% | $8,754M | $7,444M |
| 7 | $164,000M | 12.30% | $20,172M | 60.00% | $9,913M | $8,516M |
| 8 | $176,000M | 13.20% | $23,232M | 60.00% | $11,096M | $10,532M |
| 9 | $188,000M | 14.10% | $26,508M | 60.00% | $12,294M | $11,704M |
| 10 | $200,000M | 15.00% | $30,000M | 60.00% | $13,500M | $12,882M |

### Discount Rates & Present Values

| Year | Cost of Capital | Cumulated DF | PV(Rest) | PV(AI) | PV(Auto) |
|------|-----------------|--------------|----------|--------|----------|
| 1 | 11.79% | 0.8945 | $23,878M | $36,078M | $406M |
| 2 | 11.79% | 0.8001 | $23,683M | $39,282M | $1,172M |
| 3 | 11.79% | 0.7157 | $24,480M | $43,008M | $2,320M |
| 4 | 11.79% | 0.6402 | $25,358M | $43,344M | $3,034M |
| 5 | 11.79% | 0.5727 | $26,290M | $42,660M | $3,668M |
| 6 | 11.13% | 0.5153 | $26,591M | $39,487M | $3,836M |
| 7 | 10.48% | 0.4664 | $26,518M | $36,479M | $3,972M |
| 8 | 9.82% | 0.4247 | $25,551M | $32,941M | $4,473M |
| 9 | 9.16% | 0.3891 | $24,256M | $30,219M | $4,554M |
| 10 | 8.50% | 0.3586 | $22,678M | $27,718M | $4,620M |

**Stable Cost of Capital (Terminal):** 8.50%

---

## Formula Logic Flow Summary

### Revenue Projection Chain:

```
Input!B25 (Growth Yr1)
    ↓
Valuation!C2 = Input!B25
    ↓
Valuation!C3 = B3 × (1 + C2) → Revenue Year 1
    ↓
Valuation!D3 = C3 × (1 + D2) → Revenue Year 2
    ... continues to Year 10 and Terminal
```

### Operating Income Chain:

```
Input!B26 (Op Margin Yr1) → Valuation!C4
    ↓
Valuation!C5 = C4 × C3 → EBIT Year 1
    ↓
Valuation!C7 = C5 × (1 - C6) → EBIT(1-t) with NOL logic
```

### Reinvestment Chain (with 3-year lag):

```
Valuation!C8 = (F3 - E3) / C57
    [Where C57 = Input!B30 (Sales/Capital)]

Meaning: Year 1 reinvestment drives Year 4 growth
```

### FCFF Chain:

```
Valuation!C9 = C7 - C8 → FCFF Year 1
```

### Discount Factor Chain:

```
Cost of Capital!B13 → Input!B34 → Valuation!C30
Valuation!C31 = 1 / (1 + C30)
Valuation!D31 = C31 × (1 / (1 + D30))
```

### Present Value Chain:

```
Valuation!C32 = C9 × C31 → PV(FCFF) Year 1
Sum(C32:L32) + N9 × L31 = B37 → Value of Rest Segment
```

---

## Key Model Assumptions & Their Impact

| Assumption | Value | Impact on Valuation |
|------------|-------|---------------------|
| AI Market grows to $300B | +3.75× | High - drives AI segment value |
| NVIDIA AI share drops to 60% | -20pp | Moderate - partially offsets market growth |
| Auto market grows to $200B | +10× | Moderate - small current base |
| NVIDIA Auto share grows to 15% | +9pp | Moderate - significant share gain |
| Target Operating Margin 60% | -5-12pp | Moderate - margin compression |
| Sales/Capital = 2.5× | Above industry | Positive - reduces reinvestment |
| 3-year reinvestment lag | Extended | Negative - delays growth benefits |
| Stable ROIC = 20% | Below current | Significant - affects terminal value |
| Stable WACC = 8.5% | Below current | Positive - higher terminal value |
| Failure probability = 0% | No distress | Positive - no value haircut |

---

## Sensitivity Considerations

The model's valuation is most sensitive to:

1. **Terminal Value Assumptions** - The stable growth rate (4.7%) and stable cost of capital (8.5%) drive ~65% of total value
2. **AI Market Size & Share** - AI segment represents 52.7% of total value
3. **Operating Margin Trajectory** - Movement from 72% to 60% materially impacts cash flows
4. **Reinvestment Efficiency** - Sales/Capital ratio of 2.5× vs industry average of 1.1× significantly reduces capital requirements

---

## Conclusion

This is a well-constructed, academically rigorous DCF model that implements:

1. **Sum-of-the-parts valuation** with three distinct business segments
2. **Comprehensive cost of capital framework** with multiple calculation methods
3. **Accounting adjustments** for R&D capitalization and operating leases
4. **Industry benchmarking** against 93 US industries
5. **Country risk integration** with 190+ country equity risk premiums
6. **Stress testing** through diagnostics and override capabilities

The model's conclusion that NVIDIA is ~59% overvalued at $123 reflects relatively conservative long-term assumptions about market share erosion, margin compression, and ROIC mean reversion, despite building in substantial market growth in both AI and Auto segments.

---

*Model Source: Professor Aswath Damodaran, NYU Stern School of Business*
*Analysis Date: January 2025*
