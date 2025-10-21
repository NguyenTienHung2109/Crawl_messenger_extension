"""
Solution V4 Universal - Universal Entity Extraction
Fix thiếu sót: Extract entities cho TẤT CẢ messages, không chỉ trong window matching

Key Improvements:
1. Universal entity extraction ngay từ Step 2 cho ALL message types
2. Volume extraction cho REPLY/CONFIRM không phụ thuộc vào window matching
3. Enhanced name matching và action detection
4. Robust number extraction với negative exclusion
"""

import pandas as pd
import re
from datetime import datetime, timedelta
import numpy as np

def extract_volume(message):
    """Universal volume extraction cho tất cả message types"""
    patterns = [
        (r'(\d+(?:\.\d+)?)\s*u\b', 1),           # 5u
        (r'(\d+(?:\.\d+)?)\s*mio\b', 1),         # 1.5mio 
        (r'(\d+)\s*k\b', 0.001),                 # 500k → 0.5
        (r'(\d+)\s*m\b', 1),                     # 10m → 10
        (r'for\s+(\d+(?:\.\d+)?)', 1),           # for 3
        (r'(\d+(?:\.\d+)?)\s+u\b', 1),           # "1 u" with space
        (r'(\d+(?:\.\d+)?)\s*mil\b', 1)          # 2mil
    ]
    
    for pattern, multiplier in patterns:
        match = re.search(pattern, message)
        if match:
            return float(match.group(1)) * multiplier
    return None

def extract_all_numbers(message):
    """Extract tất cả numbers (exclude negative)"""
    numbers = []
    for match in re.finditer(r'\b\d+(?:\.\d+)?\b', message):
        num = float(match.group())
        # Check context for negative
        start_pos = max(0, match.start() - 5)
        context = message[start_pos:match.start()]
        if '-' not in context:
            numbers.append(num)
    return numbers

def extract_action(message):
    """Extract action từ message"""
    message_lower = message.lower()
    if 'buy' in message_lower:
        return 'buy'
    elif 'sell' in message_lower:
        return 'sell'
    elif 'khớp' in message_lower:
        return 'match'
    return None

def extract_trader_names(message):
    """Extract tên trader được mention"""
    patterns = [
        r'buy\s+a(?:nh)?\s+(\w+)',
        r'sell\s+a(?:nh)?\s+(\w+)',
        r'khớp\s+(?:với\s+)?(\w+)',
        r'done\s+(\w+)',
        r'ok[i]?\s+(?:anh\s+)?(\w+)',
        r'not\s+suit\s+(\w+)',
        r'tks\s+(\w+)',
        r'thanks\s+(\w+)',
        r'(?:buy|sell)\s+(\w+)',
        r'(?:^|\s)([A-Z]\w{2,})'  # Capitalized names
    ]
    
    names = []
    for pattern in patterns:
        matches = re.findall(pattern, message)
        names.extend(matches)
    
    # Filter và dedupe
    names = list(set([name for name in names if len(name) >= 3]))
    return names

def check_single_number_case(row, df, idx):
    """Check case 1 số duy nhất + reply trong 30s"""
    message = str(row['mess']).lower()
    numbers = extract_all_numbers(message)
    
    if len(numbers) == 1:
        current_time = datetime.strptime(row['time'], '%H:%M:%S')
        
        # Find replies within 30s from other traders
        potential_replies = df[
            (df.index > idx) &
            (df['trader_name'] != row['trader_name']) &
            (df['Date'] == row['Date'])
        ].head(10)  # Limit check to next 10 messages for performance
        
        for _, reply in potential_replies.iterrows():
            try:
                reply_time = datetime.strptime(reply['time'], '%H:%M:%S')
                time_diff = (reply_time - current_time).total_seconds()
                if 0 < time_diff <= 30:
                    reply_message = str(reply['mess']).lower()
                    if any(kw in reply_message for kw in ['buy', 'sell', 'khớp']):
                        return True, "single_number_with_quick_reply"
                elif time_diff > 30:
                    break  # No need to check further
            except:
                continue
                
    return False, None

def enhanced_intent_detection(df):
    """Enhanced intent detection với priority rules"""
    print("STEP 1: ENHANCED INTENT DETECTION")
    print("-" * 35)
    
    results = []
    
    for idx, row in df.iterrows():
        message = str(row['mess']).lower()
        problems = []
        
        # Default
        intent_type = "NOISE"
        confidence = 0.0
        
        # Extract numbers và kiểm tra negative
        numbers = extract_all_numbers(message)
        has_negative = '-' in message and any(char.isdigit() for char in message)
        
        if has_negative:
            problems.append("negative_number_excluded")
            intent_type = "NOISE"
        else:
            has_numbers = len(numbers) > 0
            
            # Keywords
            bid_ask_keywords = ['bid', 'ask', 'offer', 'off', 'bán', 'mua', 'có', 'còn']
            has_bid_ask = any(kw in message for kw in bid_ask_keywords)
            
            time_keywords = ['on', 'spt', '1m', '1w', 'spot', '6m', '3m', '2m', '6w']
            has_time_exclusion = any(kw in message for kw in time_keywords)
            
            reply_keywords = ['buy', 'sell', 'khớp']
            confirm_keywords = ['done', 'ok', 'not suit', 'tks', 'thanks']
            
            # PRIORITY RULES
            
            # 1. CONFIRM có priority cao nhất
            if any(kw in message for kw in confirm_keywords):
                intent_type = "CONFIRM"
                confidence = 0.8
            
            # 2. REPLY có priority cao
            elif any(kw in message for kw in reply_keywords):
                intent_type = "REPLY"
                confidence = 0.7
            
            # 3. START cases
            elif has_numbers and not has_time_exclusion:
                # Case 1: Single number + quick reply
                is_single_case, case_type = check_single_number_case(row, df, idx)
                if is_single_case:
                    intent_type = "START"
                    confidence = 0.9
                    problems.append(case_type)
                
                # Case 2: Có keywords bid/ask + numbers
                elif has_bid_ask:
                    intent_type = "START"
                    confidence = 0.8
                
                # Case 3: 2 số only (bid/ask pattern)
                elif len(numbers) == 2:
                    if re.search(r'\d+\s*[/-]?\s*\d+', message):
                        intent_type = "START"
                        confidence = 0.7
                
                # Case 4: Volume patterns
                elif re.search(r'\d+(?:\.\d+)?\s*(?:u|mio|k|m)\b', message):
                    intent_type = "START"
                    confidence = 0.6
        
        # Problems tracking
        if not has_numbers and has_bid_ask:
            problems.append("no_numbers")
        if has_time_exclusion and has_bid_ask:
            problems.append("time_exclusion")
            
        result = {
            'index': idx,
            'time': row['time'],
            'date': row['Date'],
            'bank_name': row['bank_name'],
            'trader_name': row['trader_name'],
            'message': row['mess'],
            'intent_type': intent_type,
            'confidence_score': confidence,
            'problems': ';'.join(problems) if problems else '',
            'has_numbers': has_numbers,
            'has_bid_ask': has_bid_ask,
            'has_time_exclusion': has_time_exclusion,
            'numbers_found': str(numbers) if numbers else ''
        }
        results.append(result)
    
    step1_df = pd.DataFrame(results)
    
    print(f"Messages processed: {len(results)}")
    print(f"START intents: {(step1_df['intent_type'] == 'START').sum()}")
    print(f"REPLY intents: {(step1_df['intent_type'] == 'REPLY').sum()}")
    print(f"CONFIRM intents: {(step1_df['intent_type'] == 'CONFIRM').sum()}")
    print(f"NOISE: {(step1_df['intent_type'] == 'NOISE').sum()}")
    print(f"Avg confidence: {step1_df['confidence_score'].mean():.2f}")
    print()
    
    return step1_df

def universal_entity_extraction(step1_df):
    """Universal entity extraction cho TẤT CẢ message types"""
    print("STEP 2: UNIVERSAL ENTITY EXTRACTION")
    print("-" * 36)
    
    step2_df = step1_df.copy()
    
    # Initialize universal entity columns
    step2_df['entity_volume'] = None
    step2_df['entity_numbers'] = None
    step2_df['entity_action'] = None
    step2_df['entity_target_trader'] = None
    step2_df['entity_counterparty'] = None
    step2_df['entity_key_calling'] = None
    
    # START-specific columns
    step2_df['entity_price'] = None
    step2_df['entity_side'] = None
    step2_df['entity_bid'] = None
    step2_df['entity_ask'] = None
    step2_df['entity_problems'] = ''
    
    for idx, row in step2_df.iterrows():
        message = str(row['message']).lower()
        intent = row['intent_type']
        problems = []
        
        # UNIVERSAL EXTRACTION for ALL messages
        volume = extract_volume(message)
        numbers = extract_all_numbers(message)
        action = extract_action(message)
        trader_names = extract_trader_names(message)
        
        step2_df.at[idx, 'entity_volume'] = volume
        step2_df.at[idx, 'entity_numbers'] = str(numbers) if numbers else ''
        step2_df.at[idx, 'entity_action'] = action
        
        # Intent-specific extraction
        if intent == "START":
            # START entity extraction
            price = None
            side = None
            bid_price = None
            ask_price = None
            
            # Enhanced price extraction
            if 'for' in message:
                for_match = re.search(r'(\d+(?:\.\d+)?)\s*for', message)
                if for_match:
                    candidate_price = float(for_match.group(1))
                    if 0 <= candidate_price <= 99:
                        price = candidate_price
                    else:
                        problems.append(f"price_out_of_range_{candidate_price}")
            
            elif volume and numbers:
                for num in numbers:
                    if abs(num - volume) > 0.1 and 0 <= num <= 99:
                        price = num
                        break
                if price is None:
                    problems.append("no_valid_price_with_volume")
            
            elif numbers:
                for num in numbers:
                    if 0 <= num <= 99:
                        price = num
                        break
                if price is None and numbers:
                    problems.append("all_prices_out_of_range")
            
            # Side detection
            bid_keywords = ['bid', 'mua']
            ask_keywords = ['ask', 'offer', 'off', 'có', 'còn', 'bán']
            
            if any(kw in message for kw in bid_keywords):
                side = 'bid'
            elif any(kw in message for kw in ask_keywords):
                side = 'offer'
            
            # Handle 2-number cases
            if len(numbers) == 2 and not volume:
                sorted_nums = sorted([n for n in numbers if 0 <= n <= 99])
                if len(sorted_nums) == 2:
                    bid_price = sorted_nums[0]
                    ask_price = sorted_nums[1]
                    
                    if side == 'bid':
                        price = bid_price
                    elif side == 'offer':
                        price = ask_price
                    else:
                        price = sorted_nums[0]
            
            step2_df.at[idx, 'entity_price'] = price
            step2_df.at[idx, 'entity_side'] = side
            step2_df.at[idx, 'entity_bid'] = bid_price
            step2_df.at[idx, 'entity_ask'] = ask_price
            
            if price is None:
                problems.append("no_price_extracted")
            if side is None and (bid_price or ask_price):
                problems.append("unclear_side_with_spread")
        
        elif intent == "REPLY":
            # REPLY entity extraction
            target_trader = None
            if trader_names:
                target_trader = trader_names[0]  # Take first mentioned name
            
            step2_df.at[idx, 'entity_target_trader'] = target_trader
        
        elif intent == "CONFIRM":
            # CONFIRM entity extraction
            counterparty = None
            key_calling = trader_names
            
            # Priority patterns for counterparty
            patterns = [
                r'done\s+(\w+)',
                r'ok[i]?\s+(?:anh\s+)?(\w+)',
                r'not\s+suit\s+(\w+)',
                r'tks\s+(\w+)',
                r'thanks\s+(\w+)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, message)
                if match:
                    counterparty = match.group(1)
                    break
            
            step2_df.at[idx, 'entity_counterparty'] = counterparty
            step2_df.at[idx, 'entity_key_calling'] = ','.join(key_calling) if key_calling else None
        
        # Store problems
        step2_df.at[idx, 'entity_problems'] = ';'.join(problems)
    
    # Statistics
    print("UNIVERSAL ENTITY STATS:")
    total_with_volume = step2_df['entity_volume'].notna().sum()
    total_with_action = step2_df['entity_action'].notna().sum()
    
    print(f"Messages with volume: {total_with_volume}")
    print(f"Messages with action: {total_with_action}")
    
    # Intent-specific stats
    start_messages = step2_df[step2_df['intent_type'] == 'START']
    start_with_price = start_messages['entity_price'].notna().sum()
    start_with_volume = start_messages['entity_volume'].notna().sum()
    start_with_side = start_messages['entity_side'].notna().sum()
    
    print(f"START with price: {start_with_price}")
    print(f"START with volume: {start_with_volume}")
    print(f"START with side: {start_with_side}")
    
    reply_messages = step2_df[step2_df['intent_type'] == 'REPLY']
    reply_with_volume = reply_messages['entity_volume'].notna().sum()
    reply_with_action = reply_messages['entity_action'].notna().sum()
    reply_with_target = reply_messages['entity_target_trader'].notna().sum()
    
    print(f"REPLY with volume: {reply_with_volume}")
    print(f"REPLY with action: {reply_with_action}")
    print(f"REPLY with target: {reply_with_target}")
    
    confirm_messages = step2_df[step2_df['intent_type'] == 'CONFIRM']
    confirm_with_volume = confirm_messages['entity_volume'].notna().sum()
    confirm_with_counterparty = confirm_messages['entity_counterparty'].notna().sum()
    
    print(f"CONFIRM with volume: {confirm_with_volume}")
    print(f"CONFIRM with counterparty: {confirm_with_counterparty}")
    
    if step2_df['entity_price'].notna().any():
        print(f"Price range: {step2_df['entity_price'].min():.0f} - {step2_df['entity_price'].max():.0f}")
    print()
    
    return step2_df

def enhanced_reply_matching_v4(step2_df):
    """Enhanced reply matching sử dụng pre-extracted entities"""
    print("STEP 3: ENHANCED REPLY MATCHING V4")
    print("-" * 35)
    
    step3_df = step2_df.copy()
    
    # Initialize reply matching columns
    step3_df['reply_found'] = False
    step3_df['reply_bank'] = None
    step3_df['reply_trader'] = None
    step3_df['time_gap_minutes'] = None
    step3_df['reply_problems'] = ''
    
    # Copy entity data to reply columns for easier access
    step3_df['reply_volume'] = step2_df['entity_volume']
    step3_df['reply_action'] = step2_df['entity_action']
    step3_df['reply_target_trader'] = step2_df['entity_target_trader']
    
    start_messages = step3_df[step3_df['intent_type'] == 'START'].copy()
    
    for start_idx, start_row in start_messages.iterrows():
        start_time = datetime.strptime(start_row['time'], '%H:%M:%S')
        start_trader = start_row['trader_name']
        start_date = start_row['date']
        
        # WINDOW LOGIC
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
            
            if time_gap <= 5 and time_gap < min_time_gap:
                # Use pre-extracted entities
                best_reply = {
                    'bank': reply_row['bank_name'],
                    'trader': reply_row['trader_name'],
                    'time_gap': time_gap
                }
                min_time_gap = time_gap
        
        # Update START message with reply info
        if best_reply:
            step3_df.at[start_idx, 'reply_found'] = True
            step3_df.at[start_idx, 'reply_bank'] = best_reply['bank']
            step3_df.at[start_idx, 'reply_trader'] = best_reply['trader']
            step3_df.at[start_idx, 'time_gap_minutes'] = best_reply['time_gap']
        else:
            step3_df.at[start_idx, 'reply_problems'] = 'no_reply_found'
    
    # Statistics
    starts_with_reply = step3_df[(step3_df['intent_type'] == 'START') & (step3_df['reply_found'])].shape[0]
    total_starts = (step3_df['intent_type'] == 'START').sum()
    
    if starts_with_reply > 0:
        avg_time_gap = step3_df[step3_df['reply_found']]['time_gap_minutes'].mean()
        print(f"START messages with reply: {starts_with_reply}/{total_starts}")
        print(f"Reply success rate: {starts_with_reply/total_starts*100:.1f}%")
        print(f"Avg reply time gap: {avg_time_gap:.1f} minutes")
    else:
        print(f"START messages with reply: 0/{total_starts}")
        print("Reply success rate: 0.0%")
    print()
    
    return step3_df

def enhanced_confirmation_processing_v4(step3_df):
    """Enhanced confirmation processing sử dụng pre-extracted entities"""
    print("STEP 4: ENHANCED CONFIRMATION PROCESSING V4")
    print("-" * 43)
    
    step4_df = step3_df.copy()
    
    # Initialize confirm columns
    step4_df['confirm_found'] = False
    step4_df['confirm_status'] = None
    step4_df['confirm_trader'] = None
    step4_df['confirm_problems'] = ''
    
    # Copy entity data to confirm columns
    step4_df['confirm_volume'] = step4_df['entity_volume']
    step4_df['confirm_counterparty'] = step4_df['entity_counterparty']
    step4_df['confirm_key_calling'] = step4_df['entity_key_calling']
    
    # Process START messages with replies
    start_with_reply = step4_df[
        (step4_df['intent_type'] == 'START') & 
        (step4_df['reply_found'])
    ].copy()
    
    for start_idx, start_row in start_with_reply.iterrows():
        start_time = datetime.strptime(start_row['time'], '%H:%M:%S')
        start_trader = start_row['trader_name']
        reply_trader = start_row['reply_trader']
        start_date = start_row['date']
        
        # WINDOW LOGIC for CONFIRM
        next_start_same_trader = step4_df[
            (step4_df['intent_type'] == 'START') &
            (step4_df['trader_name'] == start_trader) &
            (step4_df['date'] == start_date) &
            (step4_df.index > start_idx)
        ]
        
        confirm_window_end_idx = len(step4_df)
        if not next_start_same_trader.empty:
            confirm_window_end_idx = next_start_same_trader.index[0]
        
        # Find confirmations trong window
        potential_confirms = step4_df[
            (step4_df['intent_type'] == 'CONFIRM') &
            (step4_df['date'] == start_date) &
            (step4_df.index > start_idx) &
            (step4_df.index < confirm_window_end_idx) &
            (step4_df['trader_name'].isin([start_trader, reply_trader]))
        ]
        
        best_confirm = None
        
        for confirm_idx, confirm_row in potential_confirms.iterrows():
            confirm_time = datetime.strptime(confirm_row['time'], '%H:%M:%S')
            time_gap = (confirm_time - start_time).total_seconds() / 60
            
            if time_gap <= 5:
                confirm_message = str(confirm_row['message']).lower()
                
                # Determine status
                status = "unknown"
                if any(kw in confirm_message for kw in ['done', 'ok']):
                    status = "confirmed"
                elif 'not suit' in confirm_message:
                    status = "rejected"
                elif any(kw in confirm_message for kw in ['tks', 'thanks']):
                    status = "acknowledged"
                
                # Use pre-extracted entities
                best_confirm = {
                    'status': status,
                    'trader': confirm_row['trader_name']
                }
                break
        
        # Update START message with confirm info
        if best_confirm:
            step4_df.at[start_idx, 'confirm_found'] = True
            step4_df.at[start_idx, 'confirm_status'] = best_confirm['status']
            step4_df.at[start_idx, 'confirm_trader'] = best_confirm['trader']
        else:
            step4_df.at[start_idx, 'confirm_problems'] = 'no_confirm_found'
    
    # Statistics
    starts_with_confirm = step4_df[
        (step4_df['intent_type'] == 'START') & 
        (step4_df['confirm_found'])
    ].shape[0]
    
    confirmed_deals = step4_df[
        (step4_df['intent_type'] == 'START') & 
        (step4_df['confirm_status'] == 'confirmed')
    ].shape[0]
    
    if len(start_with_reply) > 0:
        print(f"START messages with confirmation: {starts_with_confirm}")
        print(f"Actually confirmed deals: {confirmed_deals}")
        print(f"Confirmation rate: {starts_with_confirm/len(start_with_reply)*100:.1f}%")
    else:
        print("No START messages with replies to process")
    print()
    
    return step4_df

def enhanced_deal_assembly_v4(step4_df):
    """Enhanced deal assembly với universal entity usage"""
    print("STEP 5: ENHANCED DEAL ASSEMBLY V4")
    print("-" * 33)
    
    step5_df = step4_df.copy()
    
    # Initialize deal columns
    step5_df['deal_valid'] = False
    step5_df['final_buy_side'] = None
    step5_df['final_sell_side'] = None
    step5_df['final_amount'] = None
    step5_df['final_price'] = None
    step5_df['final_actual_price'] = None
    step5_df['deal_problems'] = ''
    
    # Process confirmed deals
    confirmed_deals = step5_df[
        (step5_df['intent_type'] == 'START') &
        (step5_df['reply_found']) &
        (step5_df['confirm_found']) &
        (step5_df['confirm_status'] == 'confirmed')
    ].copy()
    
    valid_deals = 0
    
    for idx, row in confirmed_deals.iterrows():
        problems = []
        
        # Determine buy/sell sides
        start_side = row['entity_side']
        start_bank = row['bank_name']
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
        
        # Universal volume resolution - use ALL available volumes
        volumes = []
        
        # Get volume from START
        if pd.notna(row['entity_volume']):
            volumes.append(row['entity_volume'])
        
        # Get volume from REPLY (pre-extracted)
        reply_idx = None
        reply_volume = None
        potential_replies = step5_df[
            (step5_df['intent_type'] == 'REPLY') &
            (step5_df['date'] == row['date']) &
            (step5_df.index > idx) &
            (step5_df['trader_name'] == row['reply_trader'])
        ]
        if not potential_replies.empty:
            reply_row = potential_replies.iloc[0]
            if pd.notna(reply_row['entity_volume']):
                volumes.append(reply_row['entity_volume'])
        
        # Get volume from CONFIRM (pre-extracted)
        confirm_volume = None
        potential_confirms = step5_df[
            (step5_df['intent_type'] == 'CONFIRM') &
            (step5_df['date'] == row['date']) &
            (step5_df.index > idx) &
            (step5_df['trader_name'] == row['confirm_trader'])
        ]
        if not potential_confirms.empty:
            confirm_row = potential_confirms.iloc[0]
            if pd.notna(confirm_row['entity_volume']):
                volumes.append(confirm_row['entity_volume'])
        
        if volumes:
            final_amount = min(volumes)
        else:
            problems.append("no_volume")
            continue
            
        # Enhanced price handling
        chat_price = row['entity_price']
        if pd.notna(chat_price):
            if chat_price >= 400:
                final_price = int(chat_price % 100)
                actual_price = 25000 + int(chat_price)
            elif chat_price <= 99:
                final_price = int(chat_price)
                actual_price = 25300 + int(chat_price)
            else:
                final_price = int(chat_price % 100)
                actual_price = 25000 + int(chat_price)
        else:
            problems.append("no_price")
            continue
        
        # Enhanced validation
        if buy_side == sell_side:
            problems.append("same_bank_sides")
            continue
        if not (0.1 <= final_amount <= 100):
            problems.append("volume_out_of_range")
        if not (0 <= final_price <= 99):
            problems.append("price_out_of_range")
        if buy_side is None or sell_side is None:
            problems.append("missing_banks")
            continue
            
        # Mark as valid deal
        if not problems:
            step5_df.at[idx, 'deal_valid'] = True
            step5_df.at[idx, 'final_buy_side'] = buy_side
            step5_df.at[idx, 'final_sell_side'] = sell_side
            step5_df.at[idx, 'final_amount'] = final_amount
            step5_df.at[idx, 'final_price'] = final_price
            step5_df.at[idx, 'final_actual_price'] = actual_price
            valid_deals += 1
        else:
            step5_df.at[idx, 'deal_problems'] = ';'.join(problems)
    
    print(f"Confirmed candidates: {len(confirmed_deals)}")
    print(f"Valid deals assembled: {valid_deals}")
    if len(confirmed_deals) > 0:
        print(f"Deal success rate: {valid_deals/len(confirmed_deals)*100:.1f}%")
    print()
    
    return step5_df

def create_final_output(step5_df):
    """Create final output trong GT format"""
    
    valid_deals = step5_df[step5_df['deal_valid']].copy()
    
    if len(valid_deals) == 0:
        print("No valid deals found!")
        return pd.DataFrame()
    
    # Create final output format
    final_output = []
    
    for idx, row in valid_deals.iterrows():
        deal = {
            'STT': len(final_output) + 1,
            'Buy_side': row['final_buy_side'],
            'Amount': row['final_amount'],
            'Price': row['final_price'],
            'Sell_side': row['final_sell_side'], 
            'Actual_price': row['final_actual_price'],
            'Actual_price_2digit': row['final_price']
        }
        final_output.append(deal)
    
    final_df = pd.DataFrame(final_output)
    return final_df

def main():
    """Main execution với universal entity extraction"""
    
    print("SOLUTION V4 UNIVERSAL - UNIVERSAL ENTITY EXTRACTION")
    print("=" * 55)
    print()
    
    # Load input
    input_file = r'D:\Projects\03.FI_crawldata\03_Task_Extract_ChatRoom\input_expanded_banks.csv'
    df = pd.read_csv(input_file, encoding='utf-8-sig')
    
    print(f"Loaded {len(df)} messages from input")
    print()
    
    # Step 1: Enhanced Intent Detection
    step1_df = enhanced_intent_detection(df)
    
    # Step 2: Universal Entity Extraction
    step2_df = universal_entity_extraction(step1_df)
    
    # Step 3: Enhanced Reply Matching V4
    step3_df = enhanced_reply_matching_v4(step2_df)
    
    # Step 4: Enhanced Confirmation Processing V4
    step4_df = enhanced_confirmation_processing_v4(step3_df)
    
    # Step 5: Enhanced Deal Assembly V4
    step5_df = enhanced_deal_assembly_v4(step4_df)
    
    # Save intermediate results
    intermediate_file = r'D:\Projects\03.FI_crawldata\03_Task_Extract_ChatRoom\intermediate_v4_universal_results.csv'
    step5_df.to_csv(intermediate_file, index=False, encoding='utf-8-sig')
    print(f"Intermediate results saved: {intermediate_file}")
    
    # Create final output
    final_df = create_final_output(step5_df)
    
    if len(final_df) > 0:
        # Save final results
        output_file = r'D:\Projects\03.FI_crawldata\03_Task_Extract_ChatRoom\solution_v4_universal_results.csv'
        final_df.to_csv(output_file, index=False, encoding='utf-8-sig')
        
        print("FINAL RESULTS:")
        print(f"Valid deals extracted: {len(final_df)}")
        print(f"Target: 138 deals")
        print(f"Ratio: {len(final_df)/138:.1f}x")
        print(f"File saved: {output_file}")
        print()
        print("SAMPLE DEALS:")
        print(final_df.head().to_string(index=False))
        
        return final_df
    else:
        print("No valid deals created!")
        return pd.DataFrame()

if __name__ == "__main__":
    main()