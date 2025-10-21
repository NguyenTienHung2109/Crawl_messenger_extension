#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FX Chat Room Extraction - GenAI Version
Using OpenRouter API with GPT-4o for intelligent extraction
"""

import pandas as pd
import re
import os
from datetime import datetime
from openai import OpenAI
import concurrent.futures
from tqdm import tqdm
import threading

def load_data():
    """Load input data and bank mapping"""
    input_file = r'D:\Projects\03.FI_crawldata\03_Task_Extract_ChatRoom\input_expanded_banks.csv'
    df = pd.read_csv(input_file, encoding='utf-8-sig')
    
    print(f"Loaded {len(df)} messages from input")
    return df

def setup_openai_client():
    """Setup OpenRouter client with API key"""
    key_file = r'D:\Projects\03.FI_crawldata\key.txt'
    with open(key_file, 'r') as f:
        api_key = f.read().strip()
    
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )
    return client

def process_intent_batch(batch_data):
    """Process one batch of messages for intent detection"""
    client, batch_df, batch_start = batch_data
    
    messages_text = ""
    for idx, row in batch_df.iterrows():
        messages_text += f"{idx}: {row['mess']}\n"
    
    prompt = f"""
Classify these Vietnamese FX chat messages into intents:

INTENT TYPES:
- START: Bid/ask offers (e.g., "22 25", "bid 20 ask 22")  
- REPLY: Interest responses (e.g., "buy 2u", "sell 3u")
- CONFIRM: Deal completion (e.g., "done", "ok", "tks")
- NOISE: Other messages

RULES:
- START: Must have numbers, avoid time keywords (1m, 6m, spot, on, spt)
- Price range: 0-99 only (2 digits)
- Return confidence 0.0-1.0

MESSAGES:
{messages_text}

OUTPUT FORMAT (one line per message):
INDEX:INTENT:CONFIDENCE
Example: 0:START:0.8
"""

    try:
        completion = client.chat.completions.create(
            model="qwen/qwen-2.5-7b-instruct",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )
        
        response = completion.choices[0].message.content
        batch_results = []
        
        # Parse response
        for line in response.strip().split('\n'):
            if ':' in line:
                try:
                    parts = line.split(':')
                    if len(parts) >= 3:
                        idx = int(parts[0])
                        intent = parts[1].upper()
                        confidence = float(parts[2])
                        
                        if idx in batch_df.index:
                            row = batch_df.loc[idx]
                            batch_results.append({
                                'index': idx,
                                'time': row['time'],
                                'date': row['Date'],
                                'bank_name': row['bank_name'],
                                'trader_name': row['trader_name'],
                                'message': row['mess'],
                                'intent_type': intent,
                                'confidence_score': confidence,
                                'genai_source': True
                            })
                except:
                    continue
        
        return batch_results
        
    except Exception as e:
        # Fallback to NOISE for failed batch
        batch_results = []
        for idx, row in batch_df.iterrows():
            batch_results.append({
                'index': idx,
                'time': row['time'],
                'date': row['Date'],
                'bank_name': row['bank_name'],
                'trader_name': row['trader_name'],
                'message': row['mess'],
                'intent_type': 'NOISE',
                'confidence_score': 0.1,
                'genai_source': False
            })
        return batch_results

def step1_genai_intent_detection(df, client):
    """Step 1: GenAI Intent Detection with threading"""
    print("STEP 1: GENAI INTENT DETECTION")
    print("-" * 30)
    
    results = []
    batch_size = 50
    max_workers = 5  # Concurrent API calls
    
    # Prepare batches
    batches = []
    for i in range(0, len(df), batch_size):
        batch_df = df.iloc[i:i+batch_size]
        batches.append((client, batch_df, i))
    
    # Process batches with threading
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        with tqdm(total=len(batches), desc="Intent Detection") as pbar:
            future_to_batch = {executor.submit(process_intent_batch, batch): batch for batch in batches}
            
            for future in concurrent.futures.as_completed(future_to_batch):
                try:
                    batch_results = future.result()
                    results.extend(batch_results)
                    pbar.update(1)
                except Exception as e:
                    pbar.update(1)
                    print(f"Batch failed: {str(e)}")
    
    step1_df = pd.DataFrame(results)
    print(f"Messages processed: {len(results)}")
    print(f"START intents: {(step1_df['intent_type'] == 'START').sum()}")
    print(f"REPLY intents: {(step1_df['intent_type'] == 'REPLY').sum()}")
    print(f"CONFIRM intents: {(step1_df['intent_type'] == 'CONFIRM').sum()}")
    print(f"NOISE: {(step1_df['intent_type'] == 'NOISE').sum()}")
    print()
    
    return step1_df

def process_entity_batch(batch_data):
    """Process one batch for entity extraction"""
    client, batch, batch_start = batch_data
    
    messages_text = ""
    for idx, row in batch.iterrows():
        messages_text += f"{idx}: {row['message']}\n"
    
    prompt = f"""
Extract entities from these FX START messages:

EXTRACT:
- bid: Number 0-99
- ask: Number 0-99  
- volume: Volume in millions (e.g., "2u" = 2.0)
- side: "BID" or "ASK" (trading direction)

EXAMPLES:
"22 25" → bid=22, ask=25, side=BID
"bid 20 ask 22, 3u" → bid=20, ask=22, volume=3.0, side=BID
"07 12" → bid=7, ask=12, side=BID
"sell 15 20, 5u" → bid=15, ask=20, volume=5.0, side=ASK

MESSAGES:
{messages_text}

OUTPUT FORMAT (one line per message):
INDEX:BID:ASK:VOLUME:SIDE
Example: 0:22:25:2.0:BID
Use NULL for missing values.
"""

    try:
        completion = client.chat.completions.create(
            model="qwen/qwen-2.5-7b-instruct", 
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )
        
        response = completion.choices[0].message.content
        batch_results = []
        
        # Parse response
        for line in response.strip().split('\n'):
            if ':' in line:
                try:
                    parts = line.split(':')
                    if len(parts) >= 5:
                        idx = int(parts[0])
                        bid = float(parts[1]) if parts[1] != 'NULL' else None
                        ask = float(parts[2]) if parts[2] != 'NULL' else None
                        volume = float(parts[3]) if parts[3] != 'NULL' else None
                        side = parts[4] if parts[4] != 'NULL' else None
                        
                        batch_results.append({
                            'idx': idx,
                            'bid': bid,
                            'ask': ask, 
                            'volume': volume,
                            'side': side
                        })
                except:
                    continue
        
        return batch_results
        
    except Exception as e:
        return []

def step2_genai_entity_extraction(step1_df, client):
    """Step 2: GenAI Entity Extraction with threading"""
    print("STEP 2: GENAI ENTITY EXTRACTION")
    print("-" * 30)
    
    step2_df = step1_df.copy()
    
    # Initialize entity columns
    step2_df['entity_price'] = None
    step2_df['entity_volume'] = None
    step2_df['entity_side'] = None
    step2_df['entity_bid'] = None
    step2_df['entity_ask'] = None
    
    start_messages = step2_df[step2_df['intent_type'] == 'START']
    batch_size = 20
    max_workers = 3
    
    # Prepare batches
    batches = []
    for i in range(0, len(start_messages), batch_size):
        batch = start_messages.iloc[i:i+batch_size]
        batches.append((client, batch, i))
    
    # Process entity batches with threading
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        with tqdm(total=len(batches), desc="Entity Extraction") as pbar:
            future_to_batch = {executor.submit(process_entity_batch, batch): batch for batch in batches}
            
            for future in concurrent.futures.as_completed(future_to_batch):
                try:
                    batch_results = future.result()
                    # Update step2_df with results
                    for result in batch_results:
                        idx = result['idx']
                        if idx in step2_df.index:
                            step2_df.at[idx, 'entity_bid'] = result['bid']
                            step2_df.at[idx, 'entity_ask'] = result['ask']
                            step2_df.at[idx, 'entity_volume'] = result['volume']
                            step2_df.at[idx, 'entity_side'] = result['side']
                            
                            # Set price (use ask)
                            if result['ask'] is not None:
                                step2_df.at[idx, 'entity_price'] = result['ask']
                    
                    pbar.update(1)
                except Exception as e:
                    pbar.update(1)
                    print(f"Entity batch failed: {str(e)}")
    
    print(f"START messages with price: {step2_df['entity_price'].notna().sum()}")
    print(f"START messages with volume: {step2_df['entity_volume'].notna().sum()}")
    print()
    
    return step2_df

def create_final_output(step5_df):
    """Convert to final CSV format"""
    valid_deals = step5_df[step5_df['deal_valid']].copy()
    final_deals = []
    
    for idx, row in valid_deals.iterrows():
        deal = {
            'STT': len(final_deals) + 1,
            'Buy_side': row['buy_side'],
            'Amount': row['final_volume'],
            'Price': int(row['entity_price']) if pd.notna(row['entity_price']) else 0,
            'Sell_side': row['sell_side'],
            'Actual_price': 25300 + (int(row['entity_price']) if pd.notna(row['entity_price']) else 0),
            'Actual_price_2digit': int(row['entity_price']) if pd.notna(row['entity_price']) else 0
        }
        final_deals.append(deal)
    
    return pd.DataFrame(final_deals)

def main():
    print("FX CHAT ROOM EXTRACTION - GENAI VERSION")
    print("=" * 50)
    
    # Load data
    df = load_data()
    
    # Setup GenAI client
    client = setup_openai_client()
    
    # Step 1: GenAI Intent Detection
    step1_df = step1_genai_intent_detection(df, client)
    
    # Step 2: GenAI Entity Extraction
    step2_df = step2_genai_entity_extraction(step1_df, client)
    
    # Step 3: Reply Matching
    step3_df = step3_reply_matching(step2_df)
    
    # Step 4: Confirmation Processing
    step4_df = step4_confirmation_processing(step3_df)
    
    # Step 5: Deal Assembly
    step5_df = step5_deal_assembly(step4_df)
    
    # Save intermediate results
    intermediate_file = r'D:\Projects\03.FI_crawldata\03_Task_Extract_ChatRoom\intermediate_v3_genai_results.csv'
    step5_df.to_csv(intermediate_file, index=False, encoding='utf-8-sig')
    print(f"Intermediate results saved: {intermediate_file}")
    
    # Create final output
    final_df = create_final_output(step5_df)
    
    if len(final_df) > 0:
        # Save results
        output_file = r'D:\Projects\03.FI_crawldata\03_Task_Extract_ChatRoom\solution_v3_genai_results.csv'
        final_df.to_csv(output_file, index=False, encoding='utf-8-sig')
        
        print("\nFINAL RESULTS:")
        print(f"Valid deals extracted: {len(final_df)}")
        print(f"Target: 138 deals")
        print(f"Ratio: {len(final_df)/138:.1f}x")
        print(f"File saved: {output_file}")
        
        # Show sample
        print(f"\nSAMPLE DEALS:")
        print(final_df.head().to_string(index=False))
    else:
        print("No deals extracted!")

if __name__ == "__main__":
    main()