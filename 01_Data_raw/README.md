# FX Chat Room Data Analysis - Raw Data

## Overview
This directory contains raw data files for the FX (Foreign Exchange) chat room message analysis project. The project aims to extract structured trading information from unstructured chat room conversations.

## Files Description

### Input Files
- **`test(2).xlsx`** - Input specification file containing requirements for data transformation
  - Contains Vietnamese instructions for converting chat room data to time series format
  - Defines expected output structure: Date, Time, Bank, Side, Price, Volume

### Rule Files  
- **`Rule-FX-Message.docx`** - Business rules document for FX message processing
  - Defines parsing rules for chat room messages
  - Contains logic for identifying "Start", "Reply", and "Confirm" commands
  - Specifies price and volume extraction patterns

### Output Sample Files
- **`Copy of Chat room FX text 1 ngay.xlsx`** - Sample output showing chat room data structure
  - **Shape:** 7,598 rows × 4 columns
  - **Columns:** 
    - `time` - Message timestamp (HH:MM:SS format)
    - `trader_name` - Full name of the trader
    - `trader` - Email address of the trader
    - `mess` - Chat message content
  - **Note:** In the output file, results show full numbers, but in chat room only end words are typically used

### Generated Analysis Files
- **`output_sample_analysis.md`** - Detailed analysis of the output sample file
- **`input_analysis.md`** - Analysis of the input specification file  
- **`rules_analysis.md`** - Parsed content from the rules document

## Key Business Logic

### Message Types
1. **Start Commands** - Initial trading quotes from traders
   - Must contain: numbers, bid/ask keywords, no time indicators
   - Format variations: single numbers, bid/ask pairs, price/volume combinations

2. **Reply Commands** - Responses to trading quotes
   - Contains: buy/sell keywords from different traders
   - Automatically becomes new Start command for replying trader

3. **Confirm Commands** - Deal confirmations
   - Keywords: "done", "ok", "not suit"
   - Final step to close trading deals

### Data Processing Notes
- Chat messages contain mixed Vietnamese and English trading terms
- Numbers may be abbreviated (u = million USD, k = thousand, mio = million)
- Price matching rules apply based on UV rates updated every 5 minutes
- Volume calculations use the lower value between traders when available

## Project Structure
```
01_Data_raw/
├── Copy of Chat room FX text 1 ngay.xlsx  # Output sample (7,598 chat messages)
├── test(2).xlsx                           # Input specification
├── Rule-FX-Message.docx                   # Business rules
├── README.md                              # This file
├── output_sample_analysis.md              # Generated analysis
├── input_analysis.md                      # Generated analysis
└── rules_analysis.md                      # Generated analysis
```

## Usage
Use the generated analysis files to understand the data structure and business rules before implementing extraction solutions in the `03_Task_Extract_ChatRoom` directory.