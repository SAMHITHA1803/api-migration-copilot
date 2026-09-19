from backend.analyzer.python_analyzer import (
    detect_deprecated_apis,
    verify_code
)


TEST_CASES = [
    {
        "name": "Single append",
        "code": """
import pandas as pd

df = df.append(new_row)
""",
        "expected_apis": {"append"}
    },
    {
        "name": "Single iteritems",
        "code": """
import pandas as pd

for column, series in df.iteritems():
    print(column)
""",
        "expected_apis": {"iteritems"}
    },
    {
        "name": "Both deprecated APIs",
        "code": """
import pandas as pd

df = df.append(new_row)

for column, series in df.iteritems():
    print(column)
""",
        "expected_apis": {"append", "iteritems"}
    },
    {
        "name": "Multiple append calls",
        "code": """
import pandas as pd

df = df.append(row1)
df = df.append(row2)
df = df.append(row3)
""",
        "expected_apis": {"append"}
    },
    {
        "name": "Clean pandas code",
        "code": """
import pandas as pd

df = pd.DataFrame(data)
result = df.head()
""",
        "expected_apis": set()
    },
    {
        "name": "Pandas not imported",
        "code": """
data = []

result = data.append(10)
""",
        "expected_apis": set()
    },
    {
        "name": "Unrelated append call",
        "code": """
items = []

items.append("hello")
""",
        "expected_apis": set()
    },
    {
        "name": "Invalid Python",
        "code": """
import pandas as pd

df = df.append(
""",
        "expected_apis": set(),
        "invalid": True
    }
]


def run_evaluation():

    total_cases = len(TEST_CASES)

    true_positives = 0
    false_positives = 0
    false_negatives = 0

    syntax_valid = 0
    verification_passed = 0

    print("=" * 70)
    print("API MIGRATION COPILOT - EVALUATION")
    print("=" * 70)

    for test in TEST_CASES:

        name = test["name"]
        code = test["code"]
        expected = test["expected_apis"]

        print(f"\nTest: {name}")

        analysis = detect_deprecated_apis(
            code=code,
            library="pandas",
            version_range="1.x->2.x"
        )

        if analysis.get("valid"):
            syntax_valid += 1

        actual = {
            finding["api"]
            for finding in analysis.get("findings", [])
        }

        # Calculate TP / FP / FN
        true_positives += len(actual & expected)
        false_positives += len(actual - expected)
        false_negatives += len(expected - actual)

        print(f"Expected: {expected}")
        print(f"Detected: {actual}")

        if test.get("invalid"):
            if not analysis.get("valid"):
                print("Result: PASS")
            else:
                print("Result: FAIL")
        else:
            if actual == expected:
                print("Result: PASS")
            else:
                print("Result: FAIL")

        # Verification test for clean code
        if not expected and analysis.get("valid"):

            verification = verify_code(
                code=code,
                library="pandas",
                version_range="1.x->2.x"
            )

            if verification.get("valid"):
                verification_passed += 1

    # ---------------------------------------------------------
    # Metrics
    # ---------------------------------------------------------

    precision_denominator = true_positives + false_positives
    recall_denominator = true_positives + false_negatives

    precision = (
        true_positives / precision_denominator
        if precision_denominator
        else 1.0
    )

    recall = (
        true_positives / recall_denominator
        if recall_denominator
        else 1.0
    )

    syntax_valid_rate = syntax_valid / total_cases

    clean_cases = sum(
        1
        for test in TEST_CASES
        if not test["expected_apis"]
        and not test.get("invalid")
    )

    verification_rate = (
        verification_passed / clean_cases
        if clean_cases
        else 1.0
    )

    passed_cases = 0

    for test in TEST_CASES:

        analysis = detect_deprecated_apis(
            code=test["code"],
            library="pandas",
            version_range="1.x->2.x"
        )

        if test.get("invalid"):
            passed = not analysis.get("valid")
        else:
            actual = {
                finding["api"]
                for finding in analysis.get("findings", [])
            }
            passed = actual == test["expected_apis"]

        if passed:
            passed_cases += 1

    test_success_rate = passed_cases / total_cases

    print("\n")
    print("=" * 70)
    print("EVALUATION RESULTS")
    print("=" * 70)

    print(f"Total test cases:        {total_cases}")
    print(f"Passed test cases:       {passed_cases}")
    print(f"Test success rate:       {test_success_rate:.2%}")
    print(f"Detection precision:     {precision:.2%}")
    print(f"Detection recall:        {recall:.2%}")
    print(f"Syntax validity rate:    {syntax_valid_rate:.2%}")
    print(f"Verification pass rate:  {verification_rate:.2%}")

    print("=" * 70)


if __name__ == "__main__":
    run_evaluation()