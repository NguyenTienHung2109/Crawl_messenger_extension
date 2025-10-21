# Business Requirements Document (BRD)
## FX Chat Room Data Extraction Project

### 1. Project Overview

**Project Name:** FX Chat Room Message Analysis and Data Extraction  
**Version:** 1.1  
**Date:** September 2, 2025  
**Prepared by:** System Analysis  
**Updated:** Final requirements với bank name mapping và price conversion  

### 2. Executive Summary

This project aims to develop an automated system to extract structured trading information from unstructured FX (Foreign Exchange) chat room conversations. The system will parse Vietnamese and English trading messages to identify trading commands, extract pricing information, and generate structured data outputs for further analysis.

### 3. Business Objectives

- **Primary Goal:** Convert unstructured chat room messages into structured trading data
- **Secondary Goals:**
  - Automate the identification of trading commands (Start, Reply, Confirm)
  - Extract key trading parameters (price, volume, side, bank)
  - Maintain data quality and accuracy in extraction process
  - Support real-time and batch processing of chat data

### 4. Scope

#### 4.1 In Scope
- Analysis of chat room messages containing FX trading communications
- Extraction of trading commands and parameters
- Processing of Vietnamese and English trading terminology
- Generation of structured output in time series format
- Implementation of business rules for message classification

#### 4.2 Out of Scope
- Real-time chat room integration
- Trading execution or settlement
- Financial risk management
- Regulatory compliance beyond data extraction

### 5. Business Requirements

#### 5.1 Functional Requirements

##### 5.1.1 Message Classification
- **REQ-001:** System must identify "Start" commands (initial trading quotes)
  - Detect numbers (integers)
  - Identify bid/ask keywords: "bid", "ask", "offer", "off", "bán", "mua", "có", "còn"
  - Exclude time indicators: "on", "spt", "1m", "1w", "spot", "6m", "3m", "2m", "6w"
  - Support volume indicators: "for", "u", "k", "mio"

##### 5.1.2 Reply Processing
- **REQ-002:** System must identify "Reply" commands from different traders
  - Detect "buy", "sell", "khớp" keywords
  - Associate replies with original Start commands
  - Convert replies into new Start commands

##### 5.1.3 Confirmation Processing
- **REQ-003:** System must process "Confirm" commands to finalize deals
  - Identify confirmation keywords: "done", "ok", "not suit"
  - Handle multiple confirmations (use latest)
  - Scan for additional confirmations ("tks") within 2 minutes

##### 5.1.4 Data Extraction
- **REQ-004:** Extract structured trading data including:
  - Date and Time
  - Bank identification (extracted từ trader email)
  - Trading side (Buy/Sell)
  - Price information (convert từ chat room ending digits)
  - Volume information
  
##### 5.1.5 Bank Name Requirements
- **REQ-016:** Convert trader emails thành bank names (vd: thai.nth.vib@com.vn → VIB)
- **REQ-017:** Chỉ sử dụng 30 banks có trong ground truth
- **REQ-018:** Filter input data để chỉ bao gồm banks từ ground truth

##### 5.1.6 Price Conversion Requirements  
- **REQ-019:** Price format - CHỈ SỬ DỤNG 2 SỐ CUỐI
  - Current market rate: 25,398
  - Chat room chỉ hiển thị 2 số cuối (98, 99, 00, 22, etc.)
  - Actual price giữ nguyên full number (25,398, 25,422, etc.)
  - **Important:** Chỉ quan tâm 2 số cuối, nếu 400 thì là số thứ 3

#### 5.2 Non-Functional Requirements

##### 5.2.1 Performance
- **REQ-005:** Process 7,000+ messages efficiently
- **REQ-006:** Support batch processing of historical data

##### 5.2.2 Data Quality
- **REQ-007:** Handle incomplete data gracefully (null values where appropriate)
- **REQ-008:** Maintain data integrity throughout processing pipeline
- **REQ-009:** Support price matching with UV real-time rates

##### 5.2.3 Usability
- **REQ-010:** Provide multiple extraction solution approaches
- **REQ-011:** Enable comparison and validation of different extraction methods

##### 5.2.4 Data Format Requirements  
- **REQ-012:** Convert ground truth data to CSV format for analysis
- **REQ-013:** Generate all solution results in CSV format for comparison
- **REQ-014:** Handle Vietnamese character encoding properly
- **REQ-015:** Support both Excel and CSV input/output formats

### 6. Business Rules

#### 6.1 Start Command Rules
1. **Number Detection:** Message must contain at least one integer
2. **Keyword Validation:** Must contain bid/ask related keywords
3. **Time Exclusion:** Must not contain time period indicators
4. **Volume Processing:** Handle various volume formats (u, k, mio)
5. **Price Matching:** Apply UV rate matching for prices 00-99

#### 6.2 Reply Command Rules
1. **Trader Validation:** Reply must come from different trader than Start
2. **Timing:** Must occur within reasonable timeframe of Start command
3. **Volume Extraction:** Extract volume from "u" keyword context
4. **Dual Nature:** Reply becomes new Start command for replying trader

#### 6.3 Confirmation Rules
1. **Keyword Detection:** Scan for confirmation-specific keywords
2. **Latest Priority:** Use most recent confirmation if multiple exist
3. **Volume Resolution:** Use lower volume between traders
4. **Deal Finalization:** Match sides and prices to complete deal structure

### 7. Data Requirements

#### 7.1 Input Data Structure
- **Source:** Chat room Excel export (sheet "Data" từ test(2).xlsx)
- **Format:** Time, Trader Name, Trader Email, Message  
- **Volume:** 7,659 messages total
- **Language:** Mixed Vietnamese/English
- **Bank Filter:** Chỉ sử dụng 30 banks từ ground truth (filtered từ 7,659 xuống 2,393 messages)

#### 7.2 Output Data Structure  
- **Target Format:** Exactly match ground truth format (sheet "Output B1")
- **Columns:** Buy side, Amount, Price, Sell side, Actual price
- **Buy/Sell sides:** Bank names (không phải trader names)
- **Price:** Full price numbers (không phải chat room endings)
- **Expected Deals:** 138 deals (theo ground truth)
- **Quality:** Complete records only (null for incomplete data)

### 8. Technical Approach

#### 8.1 Processing Pipeline
1. **Data Ingestion:** Load chat room Excel files
2. **Message Parsing:** Apply business rules for classification
3. **Information Extraction:** Extract trading parameters
4. **Data Validation:** Ensure data quality and completeness
5. **Output Generation:** Create structured time series data

#### 8.2 Implementation Strategy
- Develop 10 different extraction solution approaches
- Compare results across different methods
- Select optimal approach based on accuracy and performance
- Implement validation and quality checks

### 9. Success Criteria

#### 9.1 Functional Success
- Successfully classify 95%+ of trading-related messages
- Extract complete trading information for 80%+ of valid trades
- Maintain data accuracy and consistency

#### 9.2 Technical Success
- Process daily chat data (7,000+ messages) within acceptable timeframe
- Generate clean, structured output suitable for further analysis
- Provide reliable and repeatable extraction results

### 10. Risks and Mitigation

#### 10.1 Data Quality Risks
- **Risk:** Inconsistent message formats
- **Mitigation:** Implement robust parsing with fallback mechanisms

#### 10.2 Language Processing Risks
- **Risk:** Mixed Vietnamese/English terminology
- **Mitigation:** Comprehensive keyword mapping and context analysis

#### 10.3 Business Rule Complexity
- **Risk:** Complex interdependent rules may conflict
- **Mitigation:** Systematic testing with multiple solution approaches

### 11. Deliverables

1. **Analysis Documentation** - README and analysis files for raw data
2. **Python Conversion Tool** - Markdown converter for input/rule/output files  
3. **10 Extraction Solutions** - Multiple approaches in 03_Task_Extract_ChatRoom directory
4. **Results Comparison** - Comparative analysis of solution effectiveness
5. **BRD Documentation** - This business requirements document
6. **CSV Conversion** - Ground truth and all results converted to CSV format
7. **Validation Reports** - Accuracy validation against real chat room data

### 11.1 Final Solution Performance Results
Based on validation với filtered bank data và ground truth format:

#### 11.1.1 Bank Filtering Results
- **Ground Truth Banks:** 30 unique banks từ Buy side và Sell side
- **Input Data:** Filtered từ 7,659 xuống 2,393 messages (chỉ valid banks)
- **Bank Coverage:** 8/30 banks có trong input data (MSB, BIDV, VIB, OCB, TCB, ACB, VCB, SHB)

#### 11.1.2 Solution Comparison Results
| Solution | Deals | GT Ratio | Buy Banks | Sell Banks | With Amount | Avg Chat Price | Avg Actual Price |
|----------|-------|----------|-----------|------------|-------------|----------------|------------------|
| Sol 01   | 1555  | 11.3x    | 770       | 785        | 345         | 120.1          | 24216           |
| Sol 02   | 1555  | 11.3x    | 770       | 785        | 345         | 87.2           | 24232           |
| Sol 03   | 1388  | 10.1x    | 650       | 738        | 356         | 114.6          | 24175           |
| Sol 04   | 354   | 2.6x     | 170       | 184        | 354         | 201.5          | 24572           |
| Sol 05   | 12    | 0.1x     | 8         | 4          | 1           | 128.7          | 19104           |

### 11.2 Key Technical Implementation
- **Email to Bank Mapping:** thai.nth.vib@com.vn → VIB, tcb@techcombank.com → TCB
- **Price Conversion:** Chat room 90 → Full price 25390 (base + ending)
- **Target Output:** Exact match với ground truth format (Buy side, Amount, Price, Sell side, Actual price)
- **Expected Results:** 138 deals (ground truth baseline)

### 12. Timeline and Milestones

- **Phase 1:** Analysis and Documentation (Completed)
- **Phase 2:** Solution Development (Completed)  
- **Phase 3:** Testing and Comparison (Completed)
- **Phase 4:** Bank Integration và Price Conversion (Completed)
- **Phase 5:** Final BRD Update (Completed)

### 13. File Structure and Important Files

```
D:\Projects\03.FI_crawldata\
├── 01_Data_raw\
│   ├── Copy of Chat room FX text 1 ngay.xlsx    # Ground truth data (7,598 messages)
│   ├── test(2).xlsx                             # Input specification
│   ├── Rule-FX-Message.docx                     # Business rules document
│   ├── README.md                                # Data documentation
│   ├── rules_analysis.md                        # Converted rules for AI processing
│   ├── input_analysis.md                        # Input specification analysis
│   └── output_sample_analysis.md                # Output sample analysis
├── 03_Task_Extract_ChatRoom\
│   ├── solution_01_regex_basic.py               # Basic regex approach
│   ├── solution_03_rule_engine.py               # Best performing solution
│   ├── solution_05_ml_classification.py         # ML approach
│   ├── solution_08_pattern_matching.py          # Pattern matching
│   ├── ground_truth.csv                         # Converted ground truth
│   ├── solution_*_bank_results.csv              # Results với bank names
│   ├── bank_solutions_comparison.csv            # Performance comparison với banks
│   ├── input_filtered_banks.csv                 # Input đã filter chỉ ground truth banks
│   ├── extract_banks_from_ground_truth.py       # Tool extract và map bank names
│   └── comparison_report.md                     # Analysis report
├── BRD_FX_ChatRoom_Extraction.md                # This document
├── convert_to_markdown.py                       # File converter tool
└── analyze_files.py                            # Data analysis tool
```

---

**Document Status:** Active  
**Last Updated:** September 2, 2025 (Version 1.1)  
**Next Review:** Upon final solution selection and implementation