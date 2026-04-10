"""
test_path_utils.py — Tests for normalize_path utility.
No pytest required; run directly with:  python test_path_utils.py
"""

from path_utils import normalize_path


def run_test(name: str, got, expected):
    """Print PASS / FAIL and return True on success."""
    if got == expected:
        print(f"  PASS  {name}")
        return True
    else:
        print(f"  FAIL  {name}")
        print(f"        expected : {expected!r}")
        print(f"        got      : {got!r}")
        return False


# ── Test cases ────────────────────────────────────────────────────────────────

tests = []

# 1. Trailing slash removal
tests.append(run_test(
    "trailing slash stripped",
    normalize_path("/api/v2/payments/"),
    "/api/v2/payments",
))

# 2. Multiple trailing slashes
tests.append(run_test(
    "multiple trailing slashes stripped",
    normalize_path("/api/v1/resource///"),
    "/api/v1/resource",
))

# 3. Root path '/' must NOT be stripped
tests.append(run_test(
    "root path preserved",
    normalize_path("/"),
    "/",
))

# 4. Double-slash collapse (internal)
tests.append(run_test(
    "double slash collapsed",
    normalize_path("//api//v2"),
    "/api/v2",
))

# 5. Many consecutive slashes collapsed
tests.append(run_test(
    "many consecutive slashes collapsed",
    normalize_path("/api///v2////service"),
    "/api/v2/service",
))

# 6. Uppercase to lowercase
tests.append(run_test(
    "uppercase lowercased",
    normalize_path("/API/V2/Payments"),
    "/api/v2/payments",
))

# 7. Mixed case with trailing slash
tests.append(run_test(
    "mixed case + trailing slash",
    normalize_path("/API/V2/Payments/"),
    "/api/v2/payments",
))

# 8. Embedded query parameters stripped
tests.append(run_test(
    "query string stripped",
    normalize_path("/api/v2/resource?foo=bar&baz=1"),
    "/api/v2/resource",
))

# 9. Query string + trailing slash stripped (order matters)
tests.append(run_test(
    "query string + trailing slash stripped",
    normalize_path("/api/v2/resource/?foo=bar"),
    "/api/v2/resource",
))

# 10. Already-clean path passes through unchanged
tests.append(run_test(
    "already clean path unchanged",
    normalize_path("/api/v2/payments"),
    "/api/v2/payments",
))

# 11. All transforms together
tests.append(run_test(
    "all transforms combined",
    normalize_path("//API//V2//Payments/?token=abc"),
    "/api/v2/payments",
))

# 12. Empty string edge case
tests.append(run_test(
    "empty string returns empty string",
    normalize_path(""),
    "",
))

# 13. Slash-only variants  
tests.append(run_test(
    "double root slash normalises to /",
    normalize_path("//"),
    "/",
))

# ── Summary ───────────────────────────────────────────────────────────────────

passed = sum(tests)
total  = len(tests)
print()
print(f"Results: {passed}/{total} passed")
if passed == total:
    print("All tests PASSED.")
else:
    print(f"{total - passed} test(s) FAILED.")
