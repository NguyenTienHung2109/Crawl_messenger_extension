#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug version with name matching logic for REPLY/CONFIRM
"""

import pandas as pd
import re
import os
from datetime import datetime
import unicodedata

def remove_accents(input_str):
    """Remove Vietnamese accents using character mapping"""
    if pd.isna(input_str):
        return ""
    
    s1 = u'ÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚÝàáâãèéêìíòóôõùúýĂăĐđĨĩŨũƠơƯưẠạẢảẤấẦầẨẩẪẫẬậẮắẰằẲẳẴẵẶặẸẹẺẻẼẽẾếỀềỂểỄễỆệỈỉỊịỌọỎỏỐốỒồỔổỖỗỘộỚớỜờỞởỠỡỢợỤụỦủỨứỪừỬửỮữỰựỲỳỴỵỶỷỸỹ'
    s0 = u'AAAAEEEIIOOOOUUYaaaaeeeiioooouuyAaDdIiUuOoUuAaAaAaAaAaAaAaAaAaAaAaAaEeEeEeEeEeEeEeEeIiIiOoOoOoOoOoOoOoOoOoOoOoOoUuUuUuUuUuUuUuYyYyYyYy'
    
    s = ''
    for c in str(input_str):
        if c in s1:
            s += s0[s1.index(c)]
        else:
            s += c
    return s

def normalize_name(name):
    """Normalize Vietnamese name - remove accents, keep case"""
    if pd.isna(name):
        return ""
    
    # Remove accents
    name = remove_accents(str(name))
    
    # Keep only alphanumeric và space
    name = re.sub(r'[^a-zA-Z0-9\s]', '', name)
    
    # Extract first name (usually last word) và convert to lowercase
    words = name.strip().split()
    if words:
        first_name = words[-1].lower()
        return first_name
    return ""

def extract_name_from_message(message, trader_names):
    """Extract trader name mentioned in REPLY/CONFIRM messages"""
    if pd.isna(message):
        return None
    
    message_lower = str(message).lower()
    
    # Common patterns for name calling
    patterns = [
        r'buy\s+(\w+)',
        r'sell\s+(\w+)', 
        r'done\s+(?:a|anh|em|chi|c)\s+(\w+)',
        r'ok\s+(\w+)',
        r'tks\s+(\w+)',
        r'(\w+)\s+\d+\s*u',  # "Toan 7u"
        r'(?:done|ok|tks)\s+(\w+)(?:\s|$|nhé|ơi)',
    ]
    
    extracted_names = []
    for pattern in patterns:
        matches = re.findall(pattern, message_lower, re.IGNORECASE)
        extracted_names.extend(matches)
    
    # Match với trader names
    for extracted in extracted_names:
        extracted_norm = normalize_name(extracted)
        for trader_name in trader_names:
            trader_norm = normalize_name(trader_name)
            if extracted_norm in trader_norm or trader_norm in extracted_norm:
                return trader_name
    
    return None

def load_data():
    """Load input data"""
    input_file = r'D:\Projects\03.FI_crawldata\03_Task_Extract_ChatRoom\input_expanded_banks.csv'
    df = pd.read_csv(input_file, encoding='utf-8-sig')
    print(f"Loaded {len(df)} messages from input")
    return df

def step1_intent_detection(df):
    """Step 1: Intent Detection with name extraction"""
    print("STEP 1: INTENT DETECTION + NAME EXTRACTION")
    print("-" * 40)
    
    results = []
    trader_names = df['trader_name'].unique().tolist()
    
    for idx, row in df.iterrows():
        message = str(row['mess']).lower()
        problems = []
        
        # Intent detection
        intent_type = "NOISE"
        confidence = 0.0
        
        # START detection
        numbers = re.findall(r'\b\d+(?:\.\d+)?\b', message)
        has_numbers = len(numbers) > 0
        
        bid_ask_keywords = ['bid', 'ask', 'offer', 'off', 'bán', 'mua', 'có', 'còn']
        has_bid_ask = any(kw in message for kw in bid_ask_keywords)
        
        time_keywords = ['on', 'spt', '1m', '1w', 'spot', '6m', '3m', '2m', '6w']
        has_time_exclusion = any(kw in message for kw in time_keywords)
        
        # Cách 1: Keywords + numbers
        if has_numbers and has_bid_ask and not has_time_exclusion:
            intent_type = "START"
            confidence = 0.8
        # Cách 2: 2 numbers only
        elif len(numbers) == 2 and not has_time_exclusion:
            if re.search(r'\d+\s*[/-]?\s*\d+', message):
                intent_type = "START"
                confidence = 0.7
        
        # REPLY detection với name matching
        reply_keywords = ['buy', 'sell', 'khớp']
        mentioned_trader = extract_name_from_message(row['mess'], trader_names)
        
        if any(kw in message for kw in reply_keywords):
            if intent_type == "NOISE":
                intent_type = "REPLY"
                confidence = 0.7
                if mentioned_trader:
                    confidence = 0.9  # Higher confidence nếu có tên
        
        # CONFIRM detection
        confirm_keywords = ['done', 'ok', 'not suit', 'tks', 'thanks']
        if any(kw in message for kw in confirm_keywords):
            if intent_type == "NOISE":
                intent_type = "CONFIRM"
                confidence = 0.6
                if mentioned_trader:
                    confidence = 0.8  # Higher confidence nếu có tên
        
        result = {
            'index': idx,
            'time': row['time'],
            'date': row['Date'],
            'bank_name': row['bank_name'],
            'trader_name': row['trader_name'],
            'message': row['mess'],
            'intent_type': intent_type,
            'confidence_score': confidence,
            'mentioned_trader': mentioned_trader,
            'has_numbers': has_numbers,
            'has_bid_ask': has_bid_ask,
            'has_time_exclusion': has_time_exclusion
        }
        results.append(result)
    
    step1_df = pd.DataFrame(results)
    
    print(f"Messages processed: {len(results)}")
    print(f"START intents: {(step1_df['intent_type'] == 'START').sum()}")
    print(f"REPLY intents: {(step1_df['intent_type'] == 'REPLY').sum()}")
    print(f"CONFIRM intents: {(step1_df['intent_type'] == 'CONFIRM').sum()}")
    print(f"REPLY with names: {step1_df[(step1_df['intent_type'] == 'REPLY') & (step1_df['mentioned_trader'].notna())].shape[0]}")
    print(f"CONFIRM with names: {step1_df[(step1_df['intent_type'] == 'CONFIRM') & (step1_df['mentioned_trader'].notna())].shape[0]}")
    print()
    
    return step1_df

def step2_entity_extraction(step1_df):
    """Step 2: Entity Extraction for START messages"""
    print("STEP 2: ENTITY EXTRACTION")
    print("-" * 30)
    
    step2_df = step1_df.copy()
    
    # Initialize entity columns
    step2_df['entity_price'] = None
    step2_df['entity_volume'] = None  
    step2_df['entity_side'] = None
    step2_df['entity_bid'] = None
    step2_df['entity_ask'] = None
    step2_df['entity_problems'] = ''
    
    start_messages = step2_df[step2_df['intent_type'] == 'START']
    
    for idx, row in start_messages.iterrows():
        message = str(row['message']).lower()
        problems = []
        
        # Extract numbers
        numbers = [float(n) for n in re.findall(r'\b\d+(?:\.\d+)?\b', message)]
        
        # Extract volume
        volume = None
        volume_patterns = [
            r'(\d+(?:\.\d+)?)\s*u\b',
            r'(\d+(?:\.\d+)?)\s*mil',
            r'(\d+(?:\.\d+)?)\s*m\b'
        ]
        
        for pattern in volume_patterns:
            match = re.search(pattern, message)
            if match:
                volume = float(match.group(1))
                break
        
        # Extract side
        side = None
        if any(kw in message for kw in ['bid', 'mua', 'buy']):
            side = 'bid'
        elif any(kw in message for kw in ['ask', 'offer', 'bán', 'sell']):
            side = 'offer'
        elif len(numbers) >= 2:
            side = 'bid'  # Default cho pattern "22 25"
        
        # Extract bid/ask prices
        bid_price = None
        ask_price = None
        
        if len(numbers) >= 2:
            # Giả định format: bid ask
            bid_price = int(numbers[0]) % 100  # Chỉ lấy 2 số cuối
            ask_price = int(numbers[1]) % 100
        elif len(numbers) == 1:
            price = int(numbers[0]) % 100
            if side == 'bid':
                bid_price = price
            else:
                ask_price = price
        
        # Set main price (use ask nếu có, otherwise bid)
        main_price = ask_price if ask_price is not None else bid_price
        
        # Validation
        if main_price is not None and not (0 <= main_price <= 99):
            problems.append("price_out_of_range")
            main_price = None
        
        # Update DataFrame
        step2_df.at[idx, 'entity_price'] = main_price
        step2_df.at[idx, 'entity_volume'] = volume
        step2_df.at[idx, 'entity_side'] = side
        step2_df.at[idx, 'entity_bid'] = bid_price
        step2_df.at[idx, 'entity_ask'] = ask_price
        step2_df.at[idx, 'entity_problems'] = ';'.join(problems) if problems else ''
    
    print(f"START messages with price: {step2_df['entity_price'].notna().sum()}")
    print(f"START messages with volume: {step2_df['entity_volume'].notna().sum()}")
    print(f"START messages with side: {step2_df['entity_side'].notna().sum()}")
    print()
    
    return step2_df

def step3_reply_matching_with_names(step2_df):
    """Step 3: Enhanced REPLY matching với name extraction"""
    print("STEP 3: REPLY MATCHING WITH NAME EXTRACTION")
    print("-" * 45)
    
    step3_df = step2_df.copy()
    
    # Initialize reply columns
    step3_df['reply_found'] = False
    step3_df['reply_bank'] = None
    step3_df['reply_volume'] = None
    step3_df['reply_trader'] = None
    step3_df['reply_mentioned_name'] = None
    step3_df['time_gap_minutes'] = None
    step3_df['debug_start_reply'] = ''
    
    start_messages = step3_df[step3_df['intent_type'] == 'START'].copy()
    
    for start_idx, start_row in start_messages.iterrows():
        start_time = datetime.strptime(start_row['time'], '%H:%M:%S')
        start_trader = start_row['trader_name']
        start_date = start_row['date']
        
        # Extract START trader's first name for matching
        start_first_name = normalize_name(start_trader)
        
        # WINDOW LOGIC: Find next START from same trader
        next_start_same_trader = step3_df[
            (step3_df['intent_type'] == 'START') &
            (step3_df['trader_name'] == start_trader) &
            (step3_df['date'] == start_date) &
            (step3_df.index > start_idx)
        ]
        
        window_end_idx = len(step3_df)
        if not next_start_same_trader.empty:
            window_end_idx = next_start_same_trader.index[0]
        
        # Find replies trong window
        potential_replies = step3_df[
            (step3_df['intent_type'] == 'REPLY') &
            (step3_df['date'] == start_date) &
            (step3_df.index > start_idx) &
            (step3_df.index < window_end_idx) &
            (step3_df['trader_name'] != start_trader)
        ]
        
        best_reply = None
        min_time_gap = float('inf')
        
        for reply_idx, reply_row in potential_replies.iterrows():
            reply_time = datetime.strptime(reply_row['time'], '%H:%M:%S')
            time_gap = (reply_time - start_time).total_seconds() / 60
            
            if time_gap <= 5:
                reply_message = str(reply_row['message']).lower()
                
                # Check if REPLY mentions START trader's name
                mentioned_name = reply_row['mentioned_trader']
                name_match = False
                
                if mentioned_name:
                    mentioned_first = normalize_name(mentioned_name)
                    if mentioned_first == start_first_name:
                        name_match = True
                
                # Extract volume from reply
                reply_volume = None
                volume_match = re.search(r'(\d+(?:\.\d+)?)\s*u\b', reply_message)
                if volume_match:
                    reply_volume = float(volume_match.group(1))
                
                # Prioritize replies with name match
                score = 0
                if name_match:
                    score += 10  # High priority cho name match
                if reply_volume:
                    score += 5   # Medium priority cho volume
                if time_gap < min_time_gap:
                    score += 1   # Low priority cho time
                
                if score > 0 and (not best_reply or score > best_reply.get('score', 0)):
                    best_reply = {
                        'idx': reply_idx,
                        'bank': reply_row['bank_name'],
                        'trader': reply_row['trader_name'],
                        'volume': reply_volume,
                        'time_gap': time_gap,
                        'mentioned_name': mentioned_name,
                        'name_match': name_match,
                        'score': score
                    }
                    if name_match:
                        min_time_gap = time_gap  # Update min time only for name matches
        
        # DEBUG: Log START-REPLY matching
        debug_info = f"START[{start_idx}] {start_row['time']} {start_trader} ({start_row['bank_name']}): {start_row['message'][:50]}"
        
        if best_reply:
            step3_df.at[start_idx, 'reply_found'] = True
            step3_df.at[start_idx, 'reply_bank'] = best_reply['bank']
            step3_df.at[start_idx, 'reply_volume'] = best_reply['volume']
            step3_df.at[start_idx, 'reply_trader'] = best_reply['trader']
            step3_df.at[start_idx, 'reply_mentioned_name'] = best_reply['mentioned_name']
            step3_df.at[start_idx, 'time_gap_minutes'] = best_reply['time_gap']
            step3_df.at[start_idx, 'debug_start_reply'] = f"{debug_info} → REPLY[{best_reply['idx']}]: {best_reply['trader']} ({best_reply['bank']}) mentions='{best_reply['mentioned_name']}' vol={best_reply['volume']} gap={best_reply['time_gap']:.1f}min match={best_reply['name_match']}"
        else:
            step3_df.at[start_idx, 'debug_start_reply'] = f"{debug_info} → NO REPLY (no name match or volume)"
    
    # Statistics
    starts_with_reply = step3_df[(step3_df['intent_type'] == 'START') & (step3_df['reply_found'])].shape[0]
    total_starts = (step3_df['intent_type'] == 'START').sum()
    name_matched_replies = step3_df[(step3_df['intent_type'] == 'START') & (step3_df['reply_found']) & (step3_df['reply_mentioned_name'].notna())].shape[0]
    
    print(f"START messages with reply: {starts_with_reply}/{total_starts}")
    print(f"Reply success rate: {starts_with_reply/total_starts*100:.1f}%")
    print(f"Name-matched replies: {name_matched_replies}/{starts_with_reply} ({name_matched_replies/starts_with_reply*100:.1f}%)")
    print()
    
    return step3_df

def step4_confirmation_with_names(step3_df):
    """Step 4: Enhanced CONFIRM processing với name matching"""
    print("STEP 4: CONFIRMATION WITH NAME MATCHING")
    print("-" * 40)
    
    step4_df = step3_df.copy()
    
    # Initialize confirm columns
    step4_df['confirm_found'] = False
    step4_df['confirm_status'] = None
    step4_df['confirm_trader'] = None
    step4_df['confirm_mentioned_name'] = None
    step4_df['debug_full_sequence'] = ''
    
    start_with_reply = step4_df[
        (step4_df['intent_type'] == 'START') & 
        (step4_df['reply_found'])
    ].copy()
    
    for start_idx, start_row in start_with_reply.iterrows():
        start_time = datetime.strptime(start_row['time'], '%H:%M:%S')
        start_trader = start_row['trader_name']
        reply_trader = start_row['reply_trader']
        start_date = start_row['date']
        
        # Extract names for matching
        start_first_name = normalize_name(start_trader)
        reply_first_name = normalize_name(reply_trader)
        
        # WINDOW LOGIC for CONFIRM
        next_start_same_trader = step4_df[
            (step4_df['intent_type'] == 'START') &
            (step4_df['trader_name'] == start_trader) &
            (step4_df['date'] == start_date) &
            (step4_df.index > start_idx)
        ]
        
        window_end_idx = len(step4_df)
        if not next_start_same_trader.empty:
            window_end_idx = next_start_same_trader.index[0]
        
        potential_confirms = step4_df[
            (step4_df['intent_type'] == 'CONFIRM') &
            (step4_df['date'] == start_date) &
            (step4_df.index > start_idx) &
            (step4_df.index < window_end_idx) &
            (step4_df['trader_name'].isin([start_trader, reply_trader]))
        ]
        
        best_confirm = None
        
        for confirm_idx, confirm_row in potential_confirms.iterrows():
            confirm_time = datetime.strptime(confirm_row['time'], '%H:%M:%S')
            time_gap = (confirm_time - start_time).total_seconds() / 60
            
            if time_gap <= 5:
                confirm_message = str(confirm_row['message']).lower()
                
                # Status detection
                status = "unknown"
                if any(kw in confirm_message for kw in ['done', 'ok']):
                    status = "confirmed"
                elif 'not suit' in confirm_message:
                    status = "rejected"
                elif any(kw in confirm_message for kw in ['tks', 'thanks']):
                    status = "acknowledged"
                
                # Check name mention in CONFIRM
                mentioned_name = confirm_row['mentioned_trader']
                name_match = False
                
                if mentioned_name:
                    mentioned_first = normalize_name(mentioned_name)
                    # CONFIRM có thể mention START trader hoặc REPLY trader
                    if mentioned_first in [start_first_name, reply_first_name]:
                        name_match = True
                
                best_confirm = {
                    'idx': confirm_idx,
                    'status': status,
                    'trader': confirm_row['trader_name'],
                    'mentioned_name': mentioned_name,
                    'name_match': name_match
                }
                break
        
        # DEBUG: Log START-CONFIRM sequence
        start_debug = step4_df.at[start_idx, 'debug_start_reply']
        
        if best_confirm:
            step4_df.at[start_idx, 'confirm_found'] = True
            step4_df.at[start_idx, 'linked_confirm_idx'] = best_confirm['idx']
            
            # Update CONFIRM row với sequence info
            confirm_idx = best_confirm['idx']
            step4_df.at[confirm_idx, 'confirm_status'] = best_confirm['status']
            step4_df.at[confirm_idx, 'confirm_trader'] = best_confirm['trader']
            step4_df.at[confirm_idx, 'confirm_mentioned_name'] = best_confirm['mentioned_name']
            step4_df.at[confirm_idx, 'linked_start_idx'] = start_idx
            step4_df.at[confirm_idx, 'debug_full_sequence'] = f"{start_debug} → CONFIRM[{confirm_idx}]: {best_confirm['trader']} mentions='{best_confirm['mentioned_name']}' status={best_confirm['status']} match={best_confirm['name_match']}"
            
            # Copy START data to CONFIRM row
            step4_df.at[confirm_idx, 'start_trader_name'] = start_trader
            step4_df.at[confirm_idx, 'start_bank_name'] = start_row['bank_name']
            step4_df.at[confirm_idx, 'start_entity_price'] = start_row['entity_price']
            step4_df.at[confirm_idx, 'start_entity_volume'] = start_row['entity_volume']
            step4_df.at[confirm_idx, 'start_entity_side'] = start_row['entity_side']
            step4_df.at[confirm_idx, 'reply_bank'] = start_row['reply_bank']
            step4_df.at[confirm_idx, 'reply_volume'] = start_row['reply_volume']
            step4_df.at[confirm_idx, 'reply_mentioned_name'] = start_row['reply_mentioned_name']
        else:
            step4_df.at[start_idx, 'debug_full_sequence'] = f"{start_debug} → NO CONFIRM"
    
    # Statistics
    starts_with_confirm = step4_df[(step4_df['intent_type'] == 'START') & (step4_df['confirm_found'])].shape[0]
    confirmed_deals = step4_df[(step4_df['intent_type'] == 'CONFIRM') & (step4_df['confirm_status'] == 'confirmed')].shape[0]
    
    print(f"START messages with confirmation: {starts_with_confirm}")
    print(f"Actually confirmed deals: {confirmed_deals}")
    print(f"Confirmation rate: {confirmed_deals/starts_with_confirm*100:.1f}%")
    print()
    
    return step4_df

def step5_deal_assembly(step4_df):
    """Step 5: Deal assembly từ CONFIRM rows"""
    print("STEP 5: DEAL ASSEMBLY FROM CONFIRM ROWS")
    print("-" * 40)
    
    step5_df = step4_df.copy()
    
    # Initialize deal columns
    step5_df['deal_valid'] = False
    step5_df['buy_side'] = None
    step5_df['sell_side'] = None
    step5_df['final_volume'] = None
    step5_df['debug_final_deal'] = ''
    
    # Process CONFIRM messages with confirmed status
    confirmed_deals = step5_df[
        (step5_df['intent_type'] == 'CONFIRM') &
        (step5_df['confirm_status'] == 'confirmed') &
        (step5_df['linked_start_idx'].notna())
    ].copy()
    
    valid_deals = 0
    
    for idx, row in confirmed_deals.iterrows():
        problems = []
        
        # Get data from linked START
        start_side = row['start_entity_side']
        start_bank = row['start_bank_name']
        reply_bank = row['reply_bank']
        
        if start_side == 'bid':
            buy_side = start_bank
            sell_side = reply_bank
        elif start_side == 'offer':
            buy_side = reply_bank
            sell_side = start_bank
        else:
            problems.append("unclear_side")
            continue
        
        # Get volume
        volumes = [v for v in [row['start_entity_volume'], row['reply_volume']] if pd.notna(v)]
        if volumes:
            final_amount = min(volumes)
        else:
            problems.append("no_volume")
            continue
            
        # Get price
        chat_price = row['start_entity_price']
        if pd.notna(chat_price):
            final_price = int(chat_price)
        else:
            problems.append("no_price")
            continue
        
        # Validation
        if buy_side == sell_side:
            problems.append("same_bank_sides")
            continue
        if not (0.5 <= final_amount <= 50):
            problems.append("volume_out_of_range")
        if not (0 <= final_price <= 99):
            problems.append("price_out_of_range")
        
        # DEBUG: Log final deal on CONFIRM row
        full_sequence = row.get('debug_full_sequence', 'No sequence')
        
        if not problems:
            step5_df.at[idx, 'deal_valid'] = True
            step5_df.at[idx, 'buy_side'] = buy_side
            step5_df.at[idx, 'sell_side'] = sell_side
            step5_df.at[idx, 'final_volume'] = final_amount
            step5_df.at[idx, 'entity_price'] = chat_price
            step5_df.at[idx, 'debug_final_deal'] = f"CONFIRM[{idx}]: {full_sequence} → DEAL: {buy_side}→{sell_side} {final_amount}u@{final_price}"
            valid_deals += 1
        else:
            step5_df.at[idx, 'deal_problems'] = ';'.join(problems)
            step5_df.at[idx, 'debug_final_deal'] = f"CONFIRM[{idx}]: {full_sequence} → FAILED: {';'.join(problems)}"
    
    print(f"Confirmed candidates: {len(confirmed_deals)}")
    print(f"Valid deals assembled: {valid_deals}")
    print(f"Deal success rate: {valid_deals/len(confirmed_deals)*100:.1f}%")
    print()
    
    return step5_df

def create_final_output(step5_df):
    """Create final CSV output từ CONFIRM rows"""
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
    print("SOLUTION DEBUG WITH NAME MATCHING")
    print("=" * 40)
    
    # Load data
    df = load_data()
    
    # Step 1: Intent Detection with name extraction
    step1_df = step1_intent_detection(df)
    
    # Step 2: Entity Extraction
    step2_df = step2_entity_extraction(step1_df)
    
    # Step 3: Reply Matching with names
    step3_df = step3_reply_matching_with_names(step2_df)
    
    # Step 4: Confirmation with names
    step4_df = step4_confirmation_with_names(step3_df)
    
    # Step 5: Deal Assembly
    step5_df = step5_deal_assembly(step4_df)
    
    # Save debug results
    debug_file = r'D:\Projects\03.FI_crawldata\03_Task_Extract_ChatRoom\debug_name_matching_results.csv'
    step5_df.to_csv(debug_file, index=False, encoding='utf-8-sig')
    print(f"Debug results saved: {debug_file}")
    
    # Create final output
    final_df = create_final_output(step5_df)
    
    if len(final_df) > 0:
        output_file = r'D:\Projects\03.FI_crawldata\03_Task_Extract_ChatRoom\solution_debug_name_results.csv'
        final_df.to_csv(output_file, index=False, encoding='utf-8-sig')
        
        print("FINAL RESULTS:")
        print(f"Valid deals extracted: {len(final_df)}")
        print(f"Target: 138 deals")
        print(f"Ratio: {len(final_df)/138:.1f}x")
        print(f"File saved: {output_file}")
        
        print(f"\nSAMPLE DEALS:")
        if len(final_df) > 0:
            print(final_df.head().to_string(index=False))
    else:
        print("No deals extracted!")

if __name__ == "__main__":
    main()