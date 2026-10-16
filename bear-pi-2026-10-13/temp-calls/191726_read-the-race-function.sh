# 2026-10-13T19:17:26.591336Z UTC  agent=main  (verbatim command from transcript; secrets REDACTED)
# result head: 'def race(frame, prompt, timeout=CALL_TIMEOUT, slack=1.5):\n    """Gemini and OpenRouter in parallel; first valid non-NONE reply wins. Returns (text|None, who)."""\n    t0 = time.monotonic()\n    futs = {_pool.submit(_gemini, frame, prompt, timeout): "gemini",\n            _pool.submit(_openrouter, frame'
cd ~/tony-tests && sed -n 333,360p frankie_pipe.py
