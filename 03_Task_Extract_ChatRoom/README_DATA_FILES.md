# README - DATA FILES DESCRIPTION
## FX Chat Room Extraction Project

**Location:** `D:\Projects\03.FI_crawldata\03_Task_Extract_ChatRoom\`  
**Created:** September 2, 2025  
**Purpose:** Data file documentation for FX chat room extraction

---

## 📊 INPUT FILE: input_expanded_banks.csv

### File Overview
- **File:** `input_expanded_banks.csv`
- **Size:** 6,777 messages
- **Date Range:** October 22, 2024 - October 27, 2024 (6 days)
- **Bank Coverage:** 26/30 Ground Truth banks (86.7%)
- **Traders:** 96 unique traders
- **Language:** Mixed Vietnamese/English

### Column Structure
| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `time` | String | Message timestamp (HH:MM:SS) | `17:04:11` |
| `trader_name` | String | Full trader name | `Thanh Thai Nguyen` |
| `trader` | String | Trader email address | `thai.nth.vib@com.vn` |
| `mess` | String | Chat message content | `offer 44 4u` |
| `Date` | String | Message date | `October 22, 2024` |
| `bank_name` | String | Bank code (mapped from email) | `VIB` |

### Bank Distribution (Top 15)
| Bank | Messages | Percentage | Full Name |
|------|----------|------------|-----------|
| MB | 802 | 11.8% | MBBank |
| MSB | 760 | 11.2% | MSB |
| ABBK | 635 | 9.4% | Bac A Bank |
| ICBV | 557 | 8.2% | VietinBank |
| BIDV | 474 | 7.0% | BIDV |
| VIB | 297 | 4.4% | VIB |
| SABH | 290 | 4.3% | Nam A Bank |
| SEAV | 289 | 4.3% | SeABank |
| NCB | 258 | 3.8% | NCB |
| OCB | 241 | 3.6% | OCB |
| VPB | 237 | 3.5% | VPBank |
| VNTT | 234 | 3.5% | Viet Bank |
| TCB | 221 | 3.3% | Techcombank |
| Fubon | 210 | 3.1% | Fubon Bank |
| ACB | 200 | 3.0% | ACB |

### Sample Messages
```
17:04:11 | VIB  | offer 44 4u
17:04:32 | ABBK | offer 40 thoi anh Phung nhe  
17:05:16 | MB   | offer 410
17:05:17 | HDB  | buy Toan 7u nhe
17:05:49 | MB   | done anh
```

### Email to Bank Mapping Examples
```
thai.nth.vib@com.vn → VIB
hoaivtt@baca-bank.vn → ABBK  
toannd.mbbank@com.vn → MB
phunghk3.hdbank@com.vn → HDB
khanhlb.techcombank@com.vn → TCB
```

### Missing Banks (4/30)
- `EIBV` (Eximbank)
- `PVCB` (PVcomBank) 
- `SGTT` (Sacombank)
- `TPB` (TPBank)

---

## 🎯 OUTPUT FILE: ground_truth_2digit.csv

### File Overview
- **File:** `ground_truth_2digit.csv`
- **Size:** 138 deals
- **Purpose:** Target output format for extraction validation
- **Source:** Converted from Excel sheet "Output B1"
- **Format:** Structured FX trading deals với clean column names

### Column Structure
| Column | Type | Description | Example | Range |
|--------|------|-------------|---------|-------|
| `STT` | Integer | Sequential deal number | `1, 2, 3...` | 1-138 |
| `Buy_side` | String | Buying bank code | `TPB` | 30 unique banks |
| `Amount` | Float | Trading volume (millions USD) | `2.0` | 0.5-15.0u |
| `Price` | Integer | Chat room price (2 digits only) | `22` | 0-99 |
| `Sell_side` | String | Selling bank code | `ABBK` | 30 unique banks |
| `Actual_price` | Integer | Full market price | `25422` | 25,388-25,433 |
| `Actual_price_2digit` | Integer | 2 digits from actual price | `22` | 0-99 |

### Sample Ground Truth Deals
```
STT | Buy_side | Amount | Price | Sell_side | Actual_price | Actual_price_2digit
  1 | TPB      |   2.0  |   22  | ABBK      |     25422    |        22
  2 | Fubon    |   1.0  |   25  | ABBK      |     25425    |        25
  3 | ICBV     |   1.0  |   15  | LVBT      |     25415    |        15
  4 | NCB      |   3.0  |   20  | NABV      |     25420    |        20
  5 | ICBV     |   3.0  |   20  | ABBK      |     25420    |        20
```

### Bank Distribution in Ground Truth
**Buy Side (Top 10):**
- SEAV: 20 deals (14.5%)
- LVBT: 18 deals (13.0%)  
- TPB: 16 deals (11.6%)
- MSB: 15 deals (10.9%)
- VIB: 9 deals (6.5%)
- NCB: 8 deals (5.8%)
- ICBV: 7 deals (5.1%)
- MB: 6 deals (4.3%)
- ABBK: 6 deals (4.3%)
- VNTT: 6 deals (4.3%)

**Sell Side (Top 10):**
- ABBK: 23 deals (16.7%)
- LVBT: 14 deals (10.1%)
- VIB: 13 deals (9.4%)
- MSB: 13 deals (9.4%)
- BIDV: 12 deals (8.7%)
- SEAV: 11 deals (8.0%)
- VCB: 9 deals (6.5%)
- SABH: 7 deals (5.1%)
- OCB: 7 deals (5.1%)
- NCB: 6 deals (4.3%)

### Price Analysis
- **Chat Prices:** 0-99 (chỉ 2 số cuối)
- **Actual Prices:** 25,388-25,433 (full market prices)
- **Current Market Rate:** 25,398 (giá hiện tại)
- **Conversion Logic:** 
  - Chỉ quan tâm 2 số cuối của giá hiện tại (98)
  - Nếu chat price = 98 → actual = 25,398
  - Nếu chat price = 99 → actual = 25,399  
  - Nếu chat price = 00 → actual = 25,400
  - **Đặc biệt:** Nếu số cuối là 400 → tức là số thứ 3 (không phải 2 số cuối)

### Volume Analysis
- **Range:** 0.5-15.0 million USD
- **Average:** 3.1 million USD
- **Common Volumes:** 2.0u, 3.0u, 5.0u
- **Large Deals:** 15.0u (ODA deals)

---

## 🔄 DATA RELATIONSHIP

### Input → Output Mapping
```
Chat Message: "offer 44 4u"
↓
Trader Email: thai.nth.vib@com.vn → Bank: VIB
Chat Price: 44 → Actual Price: 25,344 (base 25,300 + 44)
Volume: 4u → Amount: 4.0
Side: offer → VIB as Sell side
```

### Enhanced Price Conversion Examples
```
Current Market Rate: 25,398
Logic: Chỉ quan tâm 2 số cuối

Column Relationships:
- Actual_price: 25,422 → Actual_price_2digit: 22
- Actual_price: 25,398 → Actual_price_2digit: 98 (current rate)
- Actual_price: 25,400 → Actual_price_2digit: 00 (round number)
- Actual_price: 25,395 → Actual_price_2digit: 95

Price Column Logic:
- Price = Actual_price_2digit (same values)
- Both columns contain 2 digits only (0-99)
- Used for algorithm validation and comparison
```

### Extraction Challenge
- **Input:** Unstructured chat messages (6,777)
- **Output:** Structured deals (138 target)
- **Ratio:** ~49:1 message-to-deal ratio
- **Complexity:** Multi-step conversation parsing (Start → Reply → Confirm)

---

## 📈 DATA QUALITY METRICS

### Input Data Quality
- ✅ **Complete Coverage:** All required columns present
- ✅ **Bank Mapping:** 26/30 GT banks covered (86.7%)
- ✅ **Time Series:** Chronological message ordering
- ✅ **Encoding:** UTF-8 with Vietnamese characters

### Ground Truth Quality
- ✅ **Complete Deals:** All deals have required fields
- ✅ **Bank Consistency:** 30 unique banks used
- ✅ **Price Consistency:** Chat prices 0-99, Actual prices in tight range
- ✅ **Volume Reasonableness:** Realistic trading volumes

---

## 🛠️ USAGE INSTRUCTIONS

### For Algorithm Development
1. **Load Input:** `pd.read_csv('input_expanded_banks.csv', encoding='utf-8-sig')`
2. **Parse Messages:** Extract Start/Reply/Confirm commands
3. **Map Banks:** Use `bank_name` column (already mapped)
4. **Extract Prices:** Chat room chỉ cần 2 số cuối (0-99)
5. **Create Output:** Format với columns: STT, Buy_side, Amount, Price, Sell_side, Actual_price, Actual_price_2digit
6. **Validate:** Compare against `ground_truth_2digit.csv`

### For Performance Evaluation
1. **Load Both Files:** `input_expanded_banks.csv` và `ground_truth_2digit.csv`
2. **Run Extraction Algorithm:** Process 6,777 input messages
3. **Compare Results:** Match extracted deals với 138 GT deals
4. **Calculate Metrics:** Exact matches (Buy_side + Sell_side + Amount + Price)
5. **Validate Columns:** Ensure output có đúng 7 columns không có spaces

---

## 🎯 EXTRACTION TARGET

### Success Metrics
- **Target Deals:** 138 deals (exact GT count)
- **Exact Matches:** 50+ deals (>36% accuracy)
- **Bank Coverage:** 25+ banks used
- **Price Accuracy:** 95%+ correct price conversions
- **Format Compliance:** 100% GT format match

### Current Best Performance
- **Deals Extracted:** 321 (2.3x ratio)
- **Exact GT Matches:** 18/138 (13.0%)
- **Bank Coverage:** 25/30 banks (83.3%)
- **Room for Improvement:** 3x better exact matching needed

---

**Files Ready for Algorithm Development:**
- ✅ `input_expanded_banks.csv` - 6,777 processed chat messages với 26 bank mapping
- ✅ `ground_truth_2digit.csv` - Target output format với 138 deals, clean column names
- ✅ 7 columns: STT, Buy_side, Amount, Price, Sell_side, Actual_price, Actual_price_2digit
- ✅ Complete documentation và examples for development guidance