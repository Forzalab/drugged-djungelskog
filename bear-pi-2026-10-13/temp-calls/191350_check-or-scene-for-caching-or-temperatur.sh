# 2026-10-13T19:13:50.152019Z UTC  agent=main  (verbatim command from transcript; secrets REDACTED)
# result head: '21:MODELS = [\n34:    "google/gemini-3.5-flash-lite": {"reasoning": {"effort": "minimal"}, "max_tokens": 400},\n35:    "google/gemini-3.8-flash": {"reasoning": {"effort": "minimal"}, "max_tokens": 400},\n36:    "x-ai/grok-4.7": {"reasoning": {"effort": "low"}, "max_tokens": 400},\n127:                "m'
cd ~/tony-tests; grep -nE "temperature|cache|lru|seed|_last|MODELS = |max_tokens" or_scene.py | head -15
