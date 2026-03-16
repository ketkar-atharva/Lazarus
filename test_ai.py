"""Quick test to verify Gemini API key + SDK call works."""
import traceback
import os

# 1. Check env var
key = os.environ.get("GEMINI_API_KEY", "")
print(f"[1] GEMINI_API_KEY from env: {'SET (' + key[:8] + '...)' if key else 'NOT SET'}")

# 2. Check ai_engine loads key
from ai_engine import API_KEY, _get_client, _MODEL
print(f"[2] ai_engine.API_KEY: {'SET (' + API_KEY[:8] + '...)' if API_KEY else 'NOT SET'}")
print(f"[3] Model: {_MODEL}")

# 3. Create client
try:
    client = _get_client()
    print(f"[4] Client created: {type(client).__name__}")
except Exception as e:
    print(f"[4] FAILED to create client: {e}")
    traceback.print_exc()
    exit(1)

# 4. Make a simple API call
try:
    response = client.models.generate_content(
        model=_MODEL,
        contents="Say hello in one word."
    )
    print(f"[5] API call SUCCESS!")
    print(f"    Response type: {type(response).__name__}")
    text = getattr(response, "text", None)
    print(f"    Response text: {text}")
except Exception as e:
    print(f"[5] API call FAILED: {e}")
    traceback.print_exc()

print("\n=== TEST COMPLETE ===")
