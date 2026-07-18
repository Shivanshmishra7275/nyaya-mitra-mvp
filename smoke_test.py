"""
Smoke Test module.
Part of the Project Nyaya Mitra package.
"""

import json
import requests
import os
import sys

# Color helpers
def print_header(title):
    print(f"\n\033[94m=== {title} ===\033[0m")

def print_success(msg):
    print(f"\033[92m[PASS]\033[0m {msg}")

def print_fail(msg):
    print(f"\033[91m[FAIL]\033[0m {msg}")

def check_field(body, field_name, expected_type=None):
    if field_name not in body:
        print_fail(f"Missing field: {field_name}")
        return False

    val = body[field_name]
    if expected_type and not isinstance(val, expected_type):
        print_fail(f"Field '{field_name}' should be {expected_type.__name__}, got {type(val).__name__}")
        return False

    return True

def run_scenario(name, query, api_key):
    print_header(name)
    url = "http://localhost:8000/api/v1/legal-query"
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
    payload = {"user_query": query}

    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code != 200:
            print_fail(f"Expected HTTP 200, got {response.status_code}")
            print(response.text)
            return False

        body = response.json()

        # Check required shape
        fields_to_check = [
            ("answer", str),
            ("legal_gps", str),
            ("issue_graph", list),
            ("opposition_view", list),
            ("strategy_tree", list),
            ("next_actions", list),
            ("scope_status", str),
            ("confidence", dict)
        ]

        all_passed = True
        for field, t in fields_to_check:
            if not check_field(body, field, t):
                all_passed = False

        if not all_passed:
            return False

        print_success(f"Shape validated. scope_status = {body['scope_status']}")
        print(f"Answer snippet: {body['answer'][:100]}...")
        if 'confidence' in body:
            print(f"Confidence: {body['confidence'].get('label')} - {body['confidence'].get('reason')}")

        return True

    except requests.exceptions.ConnectionError:
        print_fail("Could not connect to localhost:8000. Is the server running?")
        return False
    except Exception as e:
        print_fail(f"Unexpected error: {e}")
        return False

def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("\n\033[93mWARNING: GEMINI_API_KEY environment variable not found.\033[0m")
        print("To run the full LLM smoke test, provide a valid API key.")
        print("Example: set GEMINI_API_KEY=your_key && python smoke_test.py")
        print("Proceeding anyway, but expect 401s unless the server has a default key.\n")
    else:
        print("\n\033[92mFound GEMINI_API_KEY. Running live smoke tests against localhost:8000...\033[0m\n")

    # The 3 Canonical Scenarios
    scenarios = [
        {
            "name": "Scenario 1: In-scope criminal-law query",
            "query": "Someone stole my phone from my office desk yesterday."
        },
        {
            "name": "Scenario 2: Partial-scope ambiguous query",
            "query": "There was an argument at work and I felt very uncomfortable."
        },
        {
            "name": "Scenario 3: Clearly out-of-scope query",
            "query": "How do I file for divorce and child custody in India?"
        }
    ]

    all_passed = True
    for s in scenarios:
        passed = run_scenario(s["name"], s["query"], api_key)
        if not passed:
            all_passed = False

    print("\n---")
    if all_passed:
        print("\033[92mALL SMOKE TESTS PASSED.\033[0m")
    else:
        print("\033[91mSOME TESTS FAILED. See output above.\033[0m")

if __name__ == "__main__":
    main()
