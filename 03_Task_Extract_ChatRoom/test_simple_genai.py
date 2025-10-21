#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test simple GenAI call with FX sample messages
"""

from openai import OpenAI
import json

# Setup client
key_file = r'D:\Projects\03.FI_crawldata\key.txt'
with open(key_file, 'r') as f:
    api_key = f.read().strip()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
)

# Sample FX messages
sample_messages = [
    "22 25, 3u",
    "buy 2u at 25", 
    "done",
    "bid 20 ask 23",
    "sell 1.5u at 20",
    "ok tks",
    "07 12",
    "noise message here",
    "1m swap rate"
]

print("TESTING GENAI WITH FX SAMPLES")
print("=" * 40)

# Test 1: Intent Detection
print("\n1. INTENT DETECTION TEST:")
print("-" * 25)

messages_text = ""
for i, msg in enumerate(sample_messages):
    messages_text += f"{i}: {msg}\n"

intent_prompt = f"""
Classify these FX chat messages:

INTENT TYPES:
- START: Bid/ask offers (e.g., "22 25", "bid 20 ask 22")  
- REPLY: Interest responses (e.g., "buy 2u", "sell 3u")
- CONFIRM: Deal completion (e.g., "done", "ok", "tks")
- NOISE: Other messages

RULES:
- START: Must have numbers, avoid time keywords (1m, 6m, spot)
- Price range: 0-99 only

MESSAGES:
{messages_text}

OUTPUT FORMAT (one line per message):
INDEX:INTENT:CONFIDENCE
Example: 0:START:0.8
"""

try:
    completion = client.chat.completions.create(
        model="qwen/qwen-2.5-7b-instruct",
        messages=[{"role": "user", "content": intent_prompt}],
        temperature=0.1
    )
    
    print("RESPONSE:")
    print(completion.choices[0].message.content)
    
except Exception as e:
    print(f"Error: {e}")

# Test 2: Entity Extraction
print("\n\n2. ENTITY EXTRACTION TEST:")
print("-" * 30)

start_messages = ["22 25, 3u", "bid 20 ask 23", "07 12"]

entity_prompt = f"""
Extract entities from these FX START messages:

EXTRACT:
- bid: Number 0-99
- ask: Number 0-99  
- volume: Volume in millions (e.g., "2u" = 2.0)
- side: "BID" or "ASK"

EXAMPLES:
"22 25" → bid=22, ask=25, side=BID
"bid 20 ask 22, 3u" → bid=20, ask=22, volume=3.0, side=BID
"07 12" → bid=7, ask=12, side=BID

MESSAGES:
{chr(10).join(f"{i}: {msg}" for i, msg in enumerate(start_messages))}

OUTPUT FORMAT:
INDEX:BID:ASK:VOLUME:SIDE
Use NULL for missing values.
"""

try:
    completion = client.chat.completions.create(
        model="qwen/qwen-2.5-7b-instruct",
        messages=[{"role": "user", "content": entity_prompt}],
        temperature=0.1
    )
    
    print("RESPONSE:")
    print(completion.choices[0].message.content)
    
except Exception as e:
    print(f"Error: {e}")

# Test 3: Window Analysis
print("\n\n3. WINDOW ANALYSIS TEST:")
print("-" * 30)

window_context = """
START MESSAGE:
Time: 09:15:30
Trader: nguyen.van.a@tpb.com.vn (TPB)
Message: 22 25, 3u

WINDOW MESSAGES:
09:16:10 le.thi.b@vib.com.vn (VIB): buy 2u at 25
09:16:45 nguyen.van.a@tpb.com.vn (TPB): done
09:17:20 le.thi.b@vib.com.vn (VIB): tks
"""

window_prompt = f"""
Analyze this FX trading window to extract a complete deal.

SEQUENCE: START → REPLY → CONFIRM

EXTRACT:
- start_price: Last 2 digits from START 
- start_volume: Volume from START
- start_side: "BID" or "ASK"
- reply_trader: Who replied
- reply_bank: Reply trader's bank
- reply_volume: Volume from reply
- confirm_trader: Who confirmed
- deal_status: "confirmed", "rejected", or "none"

CONTEXT:
{window_context}

OUTPUT (JSON only):
{{
  "start_price": 25,
  "start_volume": 3.0,
  "start_side": "BID",
  "reply_trader": "le.thi.b@vib.com.vn",
  "reply_bank": "VIB",
  "reply_volume": 2.0,
  "confirm_trader": "nguyen.van.a@tpb.com.vn", 
  "deal_status": "confirmed"
}}
"""

try:
    completion = client.chat.completions.create(
        model="qwen/qwen-2.5-7b-instruct",
        messages=[{"role": "user", "content": window_prompt}],
        temperature=0.1
    )
    
    print("RESPONSE:")
    response = completion.choices[0].message.content
    print(response)
    
    # Try parsing JSON
    try:
        json_start = response.find('{')
        json_end = response.rfind('}') + 1
        if json_start >= 0 and json_end > json_start:
            json_str = response[json_start:json_end]
            result = json.loads(json_str)
            print("\nPARSED JSON:")
            print(json.dumps(result, indent=2))
        else:
            print("\nNo valid JSON found")
    except Exception as e:
        print(f"\nJSON parse error: {e}")
    
except Exception as e:
    print(f"Error: {e}")