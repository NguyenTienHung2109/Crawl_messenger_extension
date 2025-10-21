#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test OpenRouter API connection
"""

from openai import OpenAI

# Read API key
key_file = r'D:\Projects\03.FI_crawldata\key.txt'
with open(key_file, 'r') as f:
    api_key = f.read().strip()

client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key=api_key,
)

completion = client.chat.completions.create(
  extra_headers={
    "HTTP-Referer": "https://github.com/fx-chatroom", # Optional
    "X-Title": "FX ChatRoom Extraction", # Optional
  },
  extra_body={},
  model="qwen/qwen-2.5-7b-instruct",
  messages=[
    {
      "role": "user",
      "content": "What is the meaning of life?"
    }
  ]
)
print(completion.choices[0].message.content)