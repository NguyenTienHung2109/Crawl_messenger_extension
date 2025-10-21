#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FX Chat Room Extraction - GenAI Window Version
Truyền cả window chat cho GenAI để analyze sequence
"""

import pandas as pd
import re
import os
from datetime import datetime
from openai import OpenAI
import concurrent.futures
from tqdm import tqdm
import json

def load_data():
    """Load input data"""
    input_file = r'D:\Projects\03.FI_crawldata\03_Task_Extract_ChatRoom\input_expanded_banks.csv'
    df = pd.read_csv(input_file, encoding='utf-8-sig')
    print(f"Loaded {len(df)} messages from input")
    return df

def setup_openai_client():
    """Setup OpenRouter client"""
    key_file = r'D:\Projects\03.FI_crawldata\key.txt'
    with open(key_file, 'r') as f:
        api_key = f.read().strip()
    
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )
    return client

def find_start_messages(df):
    """Step 1: Find potential START messages using rules"""
    print("STEP 1: FIND START MESSAGES")
    print("-" * 30)
    
    start_messages = []
    
    for idx, row in df.iterrows():
        message = str(row['mess']).lower()
        
        # Basic START detection
        numbers = re.findall(r'\b\d+(?:\.\d+)?\b', message)
        time_keywords = ['on', 'spt', '1m', '1w', 'spot', '6m', '3m', '2m', '6w']
        has_time_exclusion = any(kw in message for kw in time_keywords)
        
        # Cách 1: Keywords + numbers
        bid_ask_keywords = ['bid', 'ask', 'offer', 'off', 'bán', 'mua', 'có', 'còn']
        has_bid_ask = any(kw in message for kw in bid_ask_keywords)
        
        is_start = False
        if len(numbers) > 0 and has_bid_ask and not has_time_exclusion:
            is_start = True
        # Cách 2: 2 numbers only
        elif len(numbers) == 2 and not has_time_exclusion:
            if re.search(r'\d+\s*[/-]?\s*\d+', message):
                is_start = True
        
        if is_start:
            start_messages.append({
                'index': idx,
                'time': row['time'],
                'date': row['Date'],
                'trader_name': row['trader_name'],
                'bank_name': row['bank_name'],
                'message': row['mess']
            })
    
    print(f"Potential START messages: {len(start_messages)}")
    return start_messages

def create_trader_windows(df, start_messages):
    """Step 2: Create windows between STARTs of same trader"""
    print("STEP 2: CREATE TRADER WINDOWS")
    print("-" * 30)
    
    windows = []
    
    # Group by trader and date
    trader_starts = {}
    for start in start_messages:
        key = f"{start['trader_name']}_{start['date']}"
        if key not in trader_starts:
            trader_starts[key] = []
        trader_starts[key].append(start)
    
    # Create windows between consecutive STARTs
    for key, starts in trader_starts.items():
        starts.sort(key=lambda x: x['index'])
        
        for i in range(len(starts)):
            start = starts[i]
            
            # Determine window end
            if i + 1 < len(starts):
                window_end_idx = starts[i + 1]['index']
            else:
                window_end_idx = len(df)
            
            # Get all messages in window
            window_messages = df[
                (df.index > start['index']) &
                (df.index < window_end_idx) &
                (df['Date'] == start['date'])
            ].copy()
            
            if len(window_messages) > 0:
                windows.append({
                    'start_idx': start['index'],
                    'start_trader': start['trader_name'],
                    'start_bank': start['bank_name'],
                    'start_message': start['message'],
                    'start_time': start['time'],
                    'start_date': start['date'],
                    'window_end_idx': window_end_idx,
                    'window_messages': window_messages
                })
    
    print(f"Trading windows created: {len(windows)}")
    return windows

def process_window_batch(batch_data):
    """Process batch of windows with GenAI"""
    client, windows_batch, batch_num = batch_data
    
    batch_results = []
    
    for window in windows_batch:
        # Prepare context for GenAI
        context = f"""START MESSAGE:
Time: {window['start_time']}
Trader: {window['start_trader']} ({window['start_bank']})
Message: {window['start_message']}

WINDOW MESSAGES:
"""
        
        # Limit window size to avoid long prompts
        window_msgs = window['window_messages'].head(20)  # Max 20 messages per window
        for idx, row in window_msgs.iterrows():
            context += f"{row['time']} {row['trader_name']} ({row['bank_name']}): {row['mess']}\\n"
        
        prompt = f"""
Analyze this FX trading window to extract a complete deal.

SEQUENCE REQUIRED:
1. START: Initial bid/ask offer (already identified)
2. REPLY: Response from different trader showing interest  
3. CONFIRM: Deal completion confirmation

EXTRACT:
- start_price: Last 2 digits (0-99) from START message
- start_volume: Volume from START (e.g., "2u" = 2.0)
- start_side: "BID" or "ASK" 
- reply_trader: Trader name who replied
- reply_bank: Bank of reply trader
- reply_volume: Volume from reply
- confirm_trader: Trader who confirmed
- deal_status: "confirmed", "rejected", or "none"

EXAMPLES:
START: "22 25, 3u" → price=25, volume=3.0, side=BID
REPLY: "buy 2u at 25" → volume=2.0
CONFIRM: "done" → status=confirmed

CONTEXT:
{context}

OUTPUT FORMAT (JSON):
{{
  "start_price": 25,
  "start_volume": 3.0,
  "start_side": "BID",
  "reply_trader": "trader_name",
  "reply_bank": "BANK_NAME", 
  "reply_volume": 2.0,
  "confirm_trader": "trader_name",
  "deal_status": "confirmed"
}}

Return null for missing values.
"""

        try:
            completion = client.chat.completions.create(
                model="qwen/qwen-2.5-7b-instruct",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            response = completion.choices[0].message.content
            
            # Parse JSON response
            try:
                # Extract JSON from response
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = response[json_start:json_end]
                    deal_data = json.loads(json_str)
                    
                    # Add window info
                    deal_data['start_idx'] = window['start_idx']
                    deal_data['start_trader'] = window['start_trader']
                    deal_data['start_bank'] = window['start_bank']
                    deal_data['start_time'] = window['start_time']
                    deal_data['start_date'] = window['start_date']
                    deal_data['genai_success'] = True
                    
                    batch_results.append(deal_data)
                else:
                    # No valid JSON found
                    batch_results.append({
                        'start_idx': window['start_idx'],
                        'start_trader': window['start_trader'],
                        'start_bank': window['start_bank'],
                        'start_time': window['start_time'],
                        'start_date': window['start_date'],
                        'genai_success': False,
                        'error': 'no_json'
                    })
                    
            except json.JSONDecodeError:
                batch_results.append({
                    'start_idx': window['start_idx'],
                    'start_trader': window['start_trader'],
                    'start_bank': window['start_bank'],
                    'start_time': window['start_time'],
                    'start_date': window['start_date'],
                    'genai_success': False,
                    'error': 'json_parse_error'
                })
                
        except Exception as e:
            batch_results.append({
                'start_idx': window['start_idx'],
                'start_trader': window['start_trader'],
                'start_bank': window['start_bank'],
                'start_time': window['start_time'],
                'start_date': window['start_date'],
                'genai_success': False,
                'error': str(e)
            })
    
    return batch_results

def extract_deals_with_genai_windows(windows, client):
    """Step 3: Extract deals using GenAI with full window context"""
    print("STEP 3: GENAI WINDOW EXTRACTION")
    print("-" * 35)
    
    results = []
    batch_size = 5   # Smaller batch for stability
    max_workers = 4   # Reduce concurrent calls
    
    # Prepare batches
    batches = []
    for i in range(0, len(windows), batch_size):  # Chạy full dataset
        batch_windows = windows[i:i+batch_size]
        batches.append((client, batch_windows, i))
    
    # Process with threading
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        with tqdm(total=len(batches), desc="Window Analysis") as pbar:
            future_to_batch = {executor.submit(process_window_batch, batch): batch for batch in batches}
            
            for future in concurrent.futures.as_completed(future_to_batch):
                try:
                    batch_results = future.result()
                    results.extend(batch_results)
                    pbar.update(1)
                except Exception as e:
                    pbar.update(1)
                    print(f"Batch failed: {str(e)}")
    
    # Statistics
    successful = len([r for r in results if r.get('genai_success', False)])
    confirmed_deals = len([r for r in results if r.get('deal_status') == 'confirmed'])
    
    print(f"Windows processed: {len(results)}")
    print(f"GenAI success: {successful}/{len(results)} ({successful/len(results)*100:.1f}%)")
    print(f"Confirmed deals: {confirmed_deals}")
    print()
    
    return results

def create_final_output(genai_results):
    """Convert GenAI results to final format"""
    final_deals = []
    
    for result in genai_results:
        if (result.get('genai_success', False) and 
            result.get('deal_status') == 'confirmed' and
            result.get('start_price') is not None):
            
            # Determine buy/sell sides
            start_side = result.get('start_side', '').upper()
            start_bank = result.get('start_bank')
            reply_bank = result.get('reply_bank')
            
            if start_side == 'BID':
                buy_side = start_bank
                sell_side = reply_bank
            elif start_side == 'ASK':
                buy_side = reply_bank  
                sell_side = start_bank
            else:
                continue
            
            # Get volume
            volumes = [v for v in [result.get('start_volume'), result.get('reply_volume')] if v is not None]
            if not volumes:
                continue
            final_volume = min(volumes)
            
            # Validate
            price = result.get('start_price', 0)
            if (buy_side and sell_side and buy_side != sell_side and
                0.5 <= final_volume <= 50 and 0 <= price <= 99):
                
                deal = {
                    'STT': len(final_deals) + 1,
                    'Buy_side': buy_side,
                    'Amount': final_volume,
                    'Price': int(price),
                    'Sell_side': sell_side,
                    'Actual_price': 25300 + int(price),
                    'Actual_price_2digit': int(price)
                }
                final_deals.append(deal)
    
    return pd.DataFrame(final_deals)

def main():
    print("FX CHAT ROOM EXTRACTION - GENAI WINDOW VERSION")
    print("=" * 55)
    
    # Load data
    df = load_data()
    
    # Setup GenAI client
    client = setup_openai_client()
    
    # Step 1: Find START messages (rule-based)
    start_messages = find_start_messages(df)
    
    # Step 2: Create trader windows
    windows = create_trader_windows(df, start_messages)
    
    # Step 3: GenAI analysis of windows
    genai_results = extract_deals_with_genai_windows(windows, client)
    
    # Step 4: Create final output
    final_df = create_final_output(genai_results)
    
    if len(final_df) > 0:
        # Save results
        output_file = r'D:\Projects\03.FI_crawldata\03_Task_Extract_ChatRoom\solution_v4_genai_window_results.csv'
        final_df.to_csv(output_file, index=False, encoding='utf-8-sig')
        
        print("FINAL RESULTS:")
        print(f"Valid deals extracted: {len(final_df)}")
        print(f"Target: 138 deals")
        print(f"Ratio: {len(final_df)/138:.1f}x")
        print(f"File saved: {output_file}")
        
        # Show sample
        print(f"\nSAMPLE DEALS:")
        if len(final_df) > 0:
            print(final_df.head().to_string(index=False))
    else:
        print("No deals extracted!")
    
    # Save GenAI raw results for debugging
    genai_df = pd.DataFrame(genai_results)
    genai_file = r'D:\Projects\03.FI_crawldata\03_Task_Extract_ChatRoom\genai_window_debug.csv'
    genai_df.to_csv(genai_file, index=False, encoding='utf-8-sig')
    print(f"\nGenAI debug results: {genai_file}")

if __name__ == "__main__":
    main()