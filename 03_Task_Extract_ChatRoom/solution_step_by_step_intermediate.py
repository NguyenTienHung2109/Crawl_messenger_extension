"""
Solution Step-by-Step with Intermediate Columns
Based on rules analysis and create intermediate columns for debug and validate

Intermediate Steps:
1. Intent Detection -> intent_type, confidence_score
2. Entity Extraction -> entity_price, entity_volume, entity_side  
3. Reply Matching -> reply_found, reply_bank, reply_volume
4. Confirmation -> confirm_found, confirm_status, final_volume
5. Deal Assembly -> deal_valid, buy_side, sell_side
"""

import pandas as pd
import re
from datetime import datetime, timedelta
import numpy as np

def step1_intent_detection(df):
    """
    Step 1: Detect Intent for each message
    Output columns: intent_type, confidence_score, problems
    """
    print("STEP 1: INTENT DETECTION")
    print("-" * 30)
    
    results = []
    
    for idx, row in df.iterrows():
        message = str(row['mess']).lower()
        problems = []
        
        # Check for START intent
        intent_type = "NOISE"
        confidence = 0.0
        
        # START detection theo rules
        numbers = re.findall(r'\b\d+(?:\.\d+)?\b', message)
        has_numbers = len(numbers) > 0
        
        bid_ask_keywords = ['bid', 'ask', 'offer', 'off', 'bán', 'mua', 'có', 'còn']
        has_bid_ask = any(kw in message for kw in bid_ask_keywords)
        
        time_keywords = ['on', 'spt', '1m', '1w', 'spot', '6m', '3m', '2m', '6w']
        has_time_exclusion = any(kw in message for kw in time_keywords)
        
        # Cách 1: Có keywords bid/ask + numbers
        if has_numbers and has_bid_ask and not has_time_exclusion:
            intent_type = "START"
            confidence = 0.8
        
        # Cách 2: 2 số only (bid/ask pattern)
        elif len(numbers) == 2 and not has_time_exclusion:
            # Check pattern: No1/No2, No1-No2, No1 No2
            if re.search(r'\d+\s*[/-]?\s*\d+', message):
                intent_type = "START"
                confidence = 0.7
        
        # REPLY detection
        reply_keywords = ['buy', 'sell', 'khớp']
        if any(kw in message for kw in reply_keywords):
            if intent_type == "NOISE":
                intent_type = "REPLY"
                confidence = 0.7
        
        # CONFIRM detection
        confirm_keywords = ['done', 'ok', 'not suit', 'tks', 'thanks']
        if any(kw in message for kw in confirm_keywords):
            if intent_type == "NOISE":
                intent_type = "CONFIRM"
                confidence = 0.6
        
        # Problems tracking
        if not has_numbers and has_bid_ask:
            problems.append("no_numbers")
        if has_time_exclusion and has_bid_ask:
            problems.append("time_exclusion")
        if has_numbers and not has_bid_ask and intent_type == "NOISE":
            problems.append("numbers_no_intent")
            
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
            'has_time_exclusion': has_time_exclusion
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

def step2_entity_extraction(step1_df):
    """
    Step 2: Extract entities from START messages
    Output columns: entity_price, entity_volume, entity_side, entity_bid, entity_ask
    """
    print("STEP 2: ENTITY EXTRACTION")
    print("-" * 30)
    
    # Copy step1 results
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
            r'(\d+(?:\.\d+)?)\s*mio\b',
            r'(\d+(?:\.\d+)?)\s*k\b',
            r'for\s+(\d+(?:\.\d+)?)'
        ]
        
        for pattern in volume_patterns:
            match = re.search(pattern, message)
            if match:
                volume = float(match.group(1))
                if 'k' in pattern:
                    volume = volume / 1000
                break
        
        # Extract price
        price = None
        if 'for' in message:
            for_match = re.search(r'(\d+(?:\.\d+)?)\s*for', message)
            if for_match:
                candidate_price = float(for_match.group(1))
                # Validate price range 0-99 (2 digits only)
                if 0 <= candidate_price <= 99:
                    price = candidate_price
                else:
                    problems.append(f"price_out_of_range_{candidate_price}")
        elif volume and numbers:
            # Find number that is not volume
            for num in numbers:
                if abs(num - volume) > 0.1 and 0 <= num <= 99:
                    price = num
                    break
            if price is None and numbers:
                problems.append(f"no_valid_price_found_with_volume")
        elif numbers:
            # Only accept prices in range 0-99
            candidate_price = numbers[0]
            if 0 <= candidate_price <= 99:
                price = candidate_price
            else:
                problems.append(f"price_out_of_range_{candidate_price}")
        
        # Determine side
        side = None
        bid_keywords = ['bid', 'mua']
        ask_keywords = ['ask', 'offer', 'off', 'có', 'còn', 'bán']
        
        if any(kw in message for kw in bid_keywords):
            side = 'bid'
        elif any(kw in message for kw in ask_keywords):
            side = 'offer'
        
        # Handle 2-number cases (bid/ask spread)
        bid_price = None
        ask_price = None
        if len(numbers) == 2 and not volume:
            bid_price = numbers[0]
            ask_price = numbers[1]
            if side == 'bid':
                price = bid_price
            elif side == 'offer':
                price = ask_price
        
        # Validation
        if price is None:
            problems.append("no_price_extracted")
        if side is None:
            problems.append("no_side_detected")
        if volume is None and len(numbers) > 1:
            problems.append("volume_ambiguous")
            
        # Update DataFrame
        step2_df.at[idx, 'entity_price'] = price
        step2_df.at[idx, 'entity_volume'] = volume
        step2_df.at[idx, 'entity_side'] = side
        step2_df.at[idx, 'entity_bid'] = bid_price
        step2_df.at[idx, 'entity_ask'] = ask_price
        step2_df.at[idx, 'entity_problems'] = ';'.join(problems)
    
    # Statistics
    start_with_price = step2_df[(step2_df['intent_type'] == 'START') & (step2_df['entity_price'].notna())].shape[0]
    start_with_volume = step2_df[(step2_df['intent_type'] == 'START') & (step2_df['entity_volume'].notna())].shape[0]
    start_with_side = step2_df[(step2_df['intent_type'] == 'START') & (step2_df['entity_side'].notna())].shape[0]
    
    print(f"START messages with price: {start_with_price}")
    print(f"START messages with volume: {start_with_volume}")
    print(f"START messages with side: {start_with_side}")
    print(f"Price range: {step2_df['entity_price'].min():.0f} - {step2_df['entity_price'].max():.0f}")
    print()
    
    return step2_df

def step3_reply_matching(step2_df):
    """
    Step 3: Match REPLY messages with START messages
    Output columns: reply_found, reply_bank, reply_volume, reply_trader, time_gap
    """
    print("STEP 3: REPLY MATCHING")
    print("-" * 25)
    
    step3_df = step2_df.copy()
    
    # Initialize reply columns
    step3_df['reply_found'] = False
    step3_df['reply_bank'] = None
    step3_df['reply_volume'] = None
    step3_df['reply_trader'] = None
    step3_df['time_gap_minutes'] = None
    step3_df['reply_problems'] = ''
    
    start_messages = step3_df[step3_df['intent_type'] == 'START'].copy()
    
    for start_idx, start_row in start_messages.iterrows():
        start_time = datetime.strptime(start_row['time'], '%H:%M:%S')
        start_trader = start_row['trader_name']
        start_date = start_row['date']
        
        # Find replies trong 5-minute window
        potential_replies = step3_df[
            (step3_df['intent_type'] == 'REPLY') &
            (step3_df['date'] == start_date) &
            (step3_df.index > start_idx) &
            (step3_df['trader_name'] != start_trader)
        ]
        
        best_reply = None
        min_time_gap = float('inf')
        
        for reply_idx, reply_row in potential_replies.iterrows():
            reply_time = datetime.strptime(reply_row['time'], '%H:%M:%S')
            time_gap = (reply_time - start_time).total_seconds() / 60
            
            if time_gap <= 5 and time_gap < min_time_gap:  # Within 5 minutes
                # Extract volume from reply message
                reply_message = str(reply_row['message']).lower()
                reply_volume = None
                
                volume_match = re.search(r'(\d+(?:\.\d+)?)\s*u\b', reply_message)
                if volume_match:
                    reply_volume = float(volume_match.group(1))
                
                best_reply = {
                    'bank': reply_row['bank_name'],
                    'trader': reply_row['trader_name'],
                    'volume': reply_volume,
                    'time_gap': time_gap
                }
                min_time_gap = time_gap
        
        # Update START message with reply info
        if best_reply:
            step3_df.at[start_idx, 'reply_found'] = True
            step3_df.at[start_idx, 'reply_bank'] = best_reply['bank']
            step3_df.at[start_idx, 'reply_volume'] = best_reply['volume']
            step3_df.at[start_idx, 'reply_trader'] = best_reply['trader']
            step3_df.at[start_idx, 'time_gap_minutes'] = best_reply['time_gap']
        else:
            problems = ["no_reply_found"]
            step3_df.at[start_idx, 'reply_problems'] = ';'.join(problems)
    
    # Statistics
    starts_with_reply = step3_df[(step3_df['intent_type'] == 'START') & (step3_df['reply_found'])].shape[0]
    total_starts = (step3_df['intent_type'] == 'START').sum()
    avg_time_gap = step3_df[step3_df['reply_found']]['time_gap_minutes'].mean()
    
    print(f"START messages with reply: {starts_with_reply}/{total_starts}")
    print(f"Reply success rate: {starts_with_reply/total_starts*100:.1f}%")
    print(f"Avg reply time gap: {avg_time_gap:.1f} minutes")
    print()
    
    return step3_df

def step4_confirmation_processing(step3_df):
    """
    Step 4: Process CONFIRM messages
    Output columns: confirm_found, confirm_status, confirm_volume, confirm_trader
    """
    print("STEP 4: CONFIRMATION PROCESSING") 
    print("-" * 33)
    
    step4_df = step3_df.copy()
    
    # Initialize confirm columns
    step4_df['confirm_found'] = False
    step4_df['confirm_status'] = None
    step4_df['confirm_volume'] = None  
    step4_df['confirm_trader'] = None
    step4_df['confirm_problems'] = ''
    
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
        
        # Find confirmations trong 5-minute window
        potential_confirms = step4_df[
            (step4_df['intent_type'] == 'CONFIRM') &
            (step4_df['date'] == start_date) &
            (step4_df.index > start_idx) &
            (step4_df['trader_name'].isin([start_trader, reply_trader]))
        ]
        
        best_confirm = None
        
        for confirm_idx, confirm_row in potential_confirms.iterrows():
            confirm_time = datetime.strptime(confirm_row['time'], '%H:%M:%S')
            time_gap = (confirm_time - start_time).total_seconds() / 60
            
            if time_gap <= 5:  # Within 5 minutes
                confirm_message = str(confirm_row['message']).lower()
                
                # Determine status
                status = "unknown"
                if any(kw in confirm_message for kw in ['done', 'ok']):
                    status = "confirmed"
                elif 'not suit' in confirm_message:
                    status = "rejected"
                elif any(kw in confirm_message for kw in ['tks', 'thanks']):
                    status = "acknowledged"
                
                # Extract volume from confirm
                confirm_volume = None
                volume_match = re.search(r'(\d+(?:\.\d+)?)\s*u\b', confirm_message)
                if volume_match:
                    confirm_volume = float(volume_match.group(1))
                
                best_confirm = {
                    'status': status,
                    'volume': confirm_volume,
                    'trader': confirm_row['trader_name']
                }
                break  # Take first valid confirm
        
        # Update START message with confirm info
        if best_confirm:
            step4_df.at[start_idx, 'confirm_found'] = True
            step4_df.at[start_idx, 'confirm_status'] = best_confirm['status']
            step4_df.at[start_idx, 'confirm_volume'] = best_confirm['volume']
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
    
    print(f"START messages with confirmation: {starts_with_confirm}")
    print(f"Actually confirmed deals: {confirmed_deals}")
    print(f"Confirmation rate: {starts_with_confirm/len(start_with_reply)*100:.1f}%")
    print()
    
    return step4_df

def step5_deal_assembly(step4_df):
    """
    Step 5: Assemble final deals
    Output columns: deal_valid, final_buy_side, final_sell_side, final_amount, final_price
    """
    print("STEP 5: DEAL ASSEMBLY")
    print("-" * 23)
    
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
            # Start trader muốn buy
            buy_side = start_bank
            sell_side = reply_bank
        elif start_side == 'offer':
            # Start trader muốn sell
            buy_side = reply_bank
            sell_side = start_bank
        else:
            problems.append("unclear_side")
            continue
        
        # Resolve volume
        volumes = [v for v in [row['entity_volume'], row['reply_volume'], row['confirm_volume']] if pd.notna(v)]
        if volumes:
            final_amount = min(volumes)  # Take minimum as per rules
        else:
            problems.append("no_volume")
            continue
            
        # Get price (chỉ 2 số cuối)
        chat_price = row['entity_price']
        if pd.notna(chat_price):
            if chat_price >= 400:  # Special case: số thứ 3
                final_price = int(chat_price % 100)  # Get last 2 digits
                actual_price = 25000 + int(chat_price)
            elif chat_price <= 99:  # Normal 2-digit
                final_price = int(chat_price)
                actual_price = 25300 + int(chat_price)
            else:
                final_price = int(chat_price % 100)
                actual_price = 25000 + int(chat_price)
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
            'Actual_price_2digit': row['final_price']  # Same as Price
        }
        final_output.append(deal)
    
    final_df = pd.DataFrame(final_output)
    
    return final_df

def main():
    """Main execution with step-by-step processing"""
    
    print("SOLUTION STEP-BY-STEP WITH INTERMEDIATE COLUMNS")
    print("=" * 55)
    print()
    
    # Load input
    input_file = r'D:\Projects\03.FI_crawldata\03_Task_Extract_ChatRoom\input_expanded_banks.csv'
    df = pd.read_csv(input_file, encoding='utf-8-sig')
    
    print(f"Loaded {len(df)} messages from input")
    print()
    
    # Step 1: Intent Detection
    step1_df = step1_intent_detection(df)
    
    # Step 2: Entity Extraction
    step2_df = step2_entity_extraction(step1_df)
    
    # Step 3: Reply Matching
    step3_df = step3_reply_matching(step2_df)
    
    # Step 4: Confirmation Processing
    step4_df = step4_confirmation_processing(step3_df)
    
    # Step 5: Deal Assembly
    step5_df = step5_deal_assembly(step4_df)
    
    # Save intermediate results
    intermediate_file = r'D:\Projects\03.FI_crawldata\03_Task_Extract_ChatRoom\intermediate_results.csv'
    step5_df.to_csv(intermediate_file, index=False, encoding='utf-8-sig')
    print(f"Intermediate results saved: {intermediate_file}")
    
    # Create final output
    final_df = create_final_output(step5_df)
    
    if len(final_df) > 0:
        # Save final results
        output_file = r'D:\Projects\03.FI_crawldata\03_Task_Extract_ChatRoom\solution_step_results.csv'
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