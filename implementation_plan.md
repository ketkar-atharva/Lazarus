# Replace Gemini API with Local AI Engine

Remove all external Gemini API dependencies and replace with a rule-based + context-aware local AI engine that uses the existing security dataset (`EXPECTED_CATALOG`, `LIVE_TRAFFIC_FLOW`, `SECURITY_POSTURES`) to generate intelligent responses. No external API calls, no API keys, fully offline.

## Proposed Changes

### Backend — Local AI Engine

#### [MODIFY] [ai_engine.py](file:///c:/Users/athar/Desktop/Coding/Lazarus_V2/ai_engine.py)

Complete rewrite. Remove all Gemini SDK code (`google.genai`, `dotenv`, [_get_client](file:///c:/Users/athar/Desktop/Coding/Lazarus_V2/ai_engine.py#34-46), [_call_with_retry](file:///c:/Users/athar/Desktop/Coding/Lazarus_V2/ai_engine.py#83-105), etc.) and replace with:

- **`generate_local_response(question, api_data, analysis)`** — keyword-based NLP:
  - "no authentication" / "auth" → filter APIs with failed auth status
  - "critical" / "risk" → filter APIs with CRITICAL risk level
  - "zombie" → explain deprecated-but-active APIs
  - "shadow" → explain undocumented APIs
  - "data exposure" / "pii" → show APIs exposing sensitive data
  - "encryption" / "tls" → show encryption issues
  - Fallback → generic security posture summary

- **[explain_risk(api_detail)](file:///c:/Users/athar/Desktop/Coding/Lazarus_V2/ai_engine.py#118-155)** — template-based risk explanation using the API's `security_posture` data
- **[generate_report(api_detail)](file:///c:/Users/athar/Desktop/Coding/Lazarus_V2/ai_engine.py#209-279)** — template-based compliance report
- **[simulate_attack(api_detail)](file:///c:/Users/athar/Desktop/Coding/Lazarus_V2/ai_engine.py#285-339)** — template-based attack scenarios derived from actual vulnerabilities
- **[security_summary(all_apis, analysis)](file:///c:/Users/athar/Desktop/Coding/Lazarus_V2/ai_engine.py#345-379)** — generate executive summary by counting statuses, risks, and scores
- **[query_security(question, all_apis, analysis)](file:///c:/Users/athar/Desktop/Coding/Lazarus_V2/ai_engine.py#161-203)** — delegates to `generate_local_response`

All responses use f-strings and templates to produce human-like, markdown-formatted output. A simulated 0.3–0.8s delay is added for realistic UX.

---

#### [MODIFY] [server.py](file:///c:/Users/athar/Desktop/Coding/Lazarus_V2/server.py)

- Remove `dotenv` import and `load_dotenv()` call (lines 16–23)
- Remove `ai_engine.API_KEY` assignment
- Update startup banner: replace `AI Engine: ✅ API Key Set` with `AI Engine: ✅ Local Engine Active`
- All AI endpoints (`/api/ai/query`, `/api/ai/explain-risk`, `/api/ai/generate-report`, `/api/ai/attack-simulation`, `/api/ai/security-summary`) remain but now call the local engine

---

#### [MODIFY] [.env](file:///c:/Users/athar/Desktop/Coding/Lazarus_V2/.env)

- Remove `GEMINI_API_KEY` line (keep any other vars)

---

#### [MODIFY] [test_ai.py](file:///c:/Users/athar/Desktop/Coding/Lazarus_V2/test_ai.py)

- Rewrite to test local AI engine functions directly (no API key checks)

---

#### [DELETE] [inspect_response.py](file:///c:/Users/athar/Desktop/Coding/Lazarus_V2/inspect_response.py)

Gemini-specific debug script, no longer needed.

#### [DELETE] [inspect_genai.py](file:///c:/Users/athar/Desktop/Coding/Lazarus_V2/inspect_genai.py)

Gemini-specific inspection script, no longer needed.

---

### Frontend — UI Updates

#### [MODIFY] [AiInsights.jsx](file:///c:/Users/athar/Desktop/Coding/Lazarus_V2/frontend/src/components/AiInsights.jsx)

- Replace "Powered by Gemini AI" badge → "Local AI Engine"
- Update error messages to remove Gemini references

#### [MODIFY] [AiChat.jsx](file:///c:/Users/athar/Desktop/Coding/Lazarus_V2/frontend/src/components/AiChat.jsx)

- Update header: "Lazarus AI" → "Lazarus AI Assistant (Local Engine)"
- Remove Gemini-specific error messages ("Make sure GEMINI_API_KEY is set")
- Keep existing typing dots animation (already present)
- Keep existing suggested question buttons (already present)

---

## What is NOT Changing

- [mock_data.py](file:///c:/Users/athar/Desktop/Coding/Lazarus_V2/mock_data.py) — security datasets remain untouched
- [database.py](file:///c:/Users/athar/Desktop/Coding/Lazarus_V2/database.py) — MongoDB integration unchanged
- [email_notifier.py](file:///c:/Users/athar/Desktop/Coding/Lazarus_V2/email_notifier.py) — unchanged
- Decommission / honeypot features — unchanged
- All non-AI API endpoints — unchanged

## Verification Plan

### Automated Tests

1. **Backend endpoints test** — Run [test_ai.py](file:///c:/Users/athar/Desktop/Coding/Lazarus_V2/test_ai.py) after rewrite:
   ```
   cd c:\Users\athar\Desktop\Coding\Lazarus_V2
   python test_ai.py
   ```

2. **Start backend and test API endpoints**:
   ```
   cd c:\Users\athar\Desktop\Coding\Lazarus_V2
   python server.py
   ```
   Then test via browser/curl:
   - `POST /api/ai/query` with `{"question": "Which APIs have no authentication?"}`
   - `GET /api/ai/security-summary`
   - `POST /api/ai/explain-risk` with `{"api_id": "API-BNK-004"}`

### Manual Verification

1. Start both backend (`python server.py`) and frontend (`cd frontend && npm run dev`)
2. Open the app in browser → navigate to "AI Assistant" page
3. Verify "Powered by Gemini AI" is gone, replaced with "Local AI Engine"
4. Open the floating chat → verify title says "Local Engine"
5. Try suggested questions — verify responses appear with typing animation
6. Verify no network errors in browser console
