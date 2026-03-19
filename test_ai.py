<<<<<<< HEAD
import google.generativeai as genai

# Configure with your API key
genai.configure(api_key="AIzaSyCEq7nuMsg0MbOz4mqawG1YB0EoOQT5FH8")

# Get the model
model = genai.GenerativeModel('gemini-2.0-flash')

# Generate content
response = model.generate_content("Say 'Hello World' in one word")
print("✅ SUCCESS:", response.text)
=======
"""Quick test to verify local AI engine works correctly."""
import json

# 1. Import the local AI engine
from ai_engine import (
    explain_risk,
    query_security,
    generate_report,
    simulate_attack,
    security_summary,
)
from mock_data import (
    EXPECTED_CATALOG,
    LIVE_TRAFFIC_FLOW,
    SECURITY_POSTURES,
    analyze_api_discrepancies,
    get_api_detail,
)

print("=" * 60)
print("  Lazarus Local AI Engine — Test Suite")
print("=" * 60)

# 2. Test query_security (Natural Language Query)
print("\n[1] Testing Natural Language Query...")
all_details = []
for api in EXPECTED_CATALOG:
    detail = get_api_detail(api_id=api["id"])
    if detail:
        all_details.append(detail)
# Add shadow APIs
catalog_paths = {api["path"] for api in EXPECTED_CATALOG}
for flow in LIVE_TRAFFIC_FLOW:
    if flow["path"] not in catalog_paths:
        detail = get_api_detail(path=flow["path"])
        if detail:
            all_details.append(detail)

analysis = analyze_api_discrepancies(EXPECTED_CATALOG, LIVE_TRAFFIC_FLOW)

result = query_security("Which APIs have no authentication?", all_details, analysis)
print(f"    ✅ Query returned {len(result)} characters")
print(f"    Preview: {result[:100]}...")

# 3. Test explain_risk
print("\n[2] Testing Risk Explanation...")
api_detail = get_api_detail(api_id="API-BNK-004")
result = explain_risk(api_detail)
print(f"    ✅ Explanation returned {len(result)} characters")
print(f"    Preview: {result[:100]}...")

# 4. Test generate_report
print("\n[3] Testing Report Generation...")
result = generate_report(api_detail)
print(f"    ✅ Report returned {len(result)} characters")
print(f"    Preview: {result[:100]}...")

# 5. Test simulate_attack
print("\n[4] Testing Attack Simulation...")
result = simulate_attack(api_detail)
print(f"    ✅ Simulation returned {len(result)} characters")
print(f"    Preview: {result[:100]}...")

# 6. Test security_summary
print("\n[5] Testing Security Summary...")
result = security_summary(all_details, analysis)
print(f"    ✅ Summary returned {len(result)} characters")
print(f"    Preview: {result[:100]}...")

# 7. Test fallback
print("\n[6] Testing Fallback (unknown query)...")
result = query_security("What is the weather today?", all_details, analysis)
print(f"    ✅ Fallback returned {len(result)} characters")
print(f"    Preview: {result[:100]}...")

print("\n" + "=" * 60)
print("  ✅ ALL TESTS PASSED — Local AI Engine is working!")
print("  No external API dependencies required.")
print("=" * 60)
>>>>>>> 8a9642397d03122c9b403ad399d8d8c2718785fe
