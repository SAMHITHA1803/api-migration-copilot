from backend.migration_service import analyze_migration


TEST_CASES = [
    # ============================================================
    # 1-5: Single deprecated API
    # ============================================================

    {
        "name": "01 - Single append",
        "code": """import pandas as pd

df = df.append(new_row)
""",
        "expected_findings": {"append"},
        "expected_strings": ["pd.concat"],
        "forbidden_strings": [".append("],
    },

    {
        "name": "02 - Single iteritems",
        "code": """import pandas as pd

for column, series in df.iteritems():
    print(column)
""",
        "expected_findings": {"iteritems"},
        "expected_strings": [".items("],
        "forbidden_strings": [".iteritems("],
    },

    {
        "name": "03 - Append inside function",
        "code": """import pandas as pd

def add_row(df, row):
    return df.append(row)
""",
        "expected_findings": {"append"},
        "expected_strings": ["pd.concat"],
        "forbidden_strings": [".append("],
    },

    {
        "name": "04 - Iteritems inside function",
        "code": """import pandas as pd

def print_columns(df):
    for column, series in df.iteritems():
        print(column)
""",
        "expected_findings": {"iteritems"},
        "expected_strings": [".items("],
        "forbidden_strings": [".iteritems("],
    },

    {
        "name": "05 - Append in conditional",
        "code": """import pandas as pd

if condition:
    df = df.append(new_row)
""",
        "expected_findings": {"append"},
        "expected_strings": ["pd.concat"],
        "forbidden_strings": [".append("],
    },

    # ============================================================
    # 6-10: Multiple / combined deprecated APIs
    # ============================================================

    {
        "name": "06 - Append and iteritems",
        "code": """import pandas as pd

df = df.append(new_row)

for column, series in df.iteritems():
    print(column)
""",
        "expected_findings": {"append", "iteritems"},
        "expected_strings": ["pd.concat", ".items("],
        "forbidden_strings": [".append(", ".iteritems("],
    },

    {
        "name": "07 - Multiple append calls",
        "code": """import pandas as pd

df = df.append(row1)
df = df.append(row2)
df = df.append(row3)
""",
        "expected_findings": {"append"},
        "expected_strings": ["pd.concat"],
        "forbidden_strings": [".append("],
    },

    {
        "name": "08 - Multiple iteritems calls",
        "code": """import pandas as pd

for column, series in df.iteritems():
    print(column)

for column, series in another_df.iteritems():
    print(column)
""",
        "expected_findings": {"iteritems"},
        "expected_strings": [".items("],
        "forbidden_strings": [".iteritems("],
    },

    {
        "name": "09 - Multiple APIs in function",
        "code": """import pandas as pd

def process(df, row):
    df = df.append(row)

    for column, series in df.iteritems():
        print(column)

    return df
""",
        "expected_findings": {"append", "iteritems"},
        "expected_strings": ["pd.concat", ".items("],
        "forbidden_strings": [".append(", ".iteritems("],
    },

    {
        "name": "10 - APIs across branches",
        "code": """import pandas as pd

if condition:
    df = df.append(row1)
else:
    df = df.append(row2)

for column, series in df.iteritems():
    print(column)
""",
        "expected_findings": {"append", "iteritems"},
        "expected_strings": ["pd.concat", ".items("],
        "forbidden_strings": [".append(", ".iteritems("],
    },

    # ============================================================
    # 11-13: Different code structures
    # ============================================================

    {
        "name": "11 - API inside class method",
        "code": """import pandas as pd

class DataProcessor:

    def process(self, df):
        return df.append(self.row)
""",
        "expected_findings": {"append"},
        "expected_strings": ["pd.concat"],
        "forbidden_strings": [".append("],
    },

    {
        "name": "12 - API inside loop",
        "code": """import pandas as pd

for row in rows:
    df = df.append(row)
""",
        "expected_findings": {"append"},
        "expected_strings": ["pd.concat"],
        "forbidden_strings": [".append("],
    },

    {
        "name": "13 - API with additional operations",
        "code": """import pandas as pd

df = df.append(new_row).reset_index(drop=True)
""",
        "expected_findings": {"append"},
        "expected_strings": ["pd.concat"],
        "forbidden_strings": [".append("],
    },

    # ============================================================
    # 14-16: Negative / clean cases
    # ============================================================

    {
        "name": "14 - Clean pandas code",
        "code": """import pandas as pd

df = pd.DataFrame(data)
result = df.head()
""",
        "expected_findings": set(),
        "expected_strings": [],
        "forbidden_strings": [".append(", ".iteritems("],
    },

    {
        "name": "15 - Normal Python list append",
        "code": """items = []

items.append("hello")
items.append("world")
""",
        "expected_findings": set(),
        "expected_strings": [],
        "forbidden_strings": [".iteritems("],
    },

    {
        "name": "16 - Pandas not imported",
        "code": """data = []

result = data.append(10)
""",
        "expected_findings": set(),
        "expected_strings": [],
        "forbidden_strings": [".append(", ".iteritems("],
    },

    # ============================================================
    # 17-18: Import variations
    # ============================================================

    {
        "name": "17 - Pandas alias",
        "code": """import pandas as pd

df = df.append(row)
""",
        "expected_findings": {"append"},
        "expected_strings": ["pd.concat"],
        "forbidden_strings": [".append("],
    },

    {
        "name": "18 - From pandas import",
        "code": """from pandas import DataFrame

df = df.append(row)
""",
        "expected_findings": {"append"},
        "expected_strings": ["pd.concat"],
        "forbidden_strings": [".append("],
    },

    # ============================================================
    # 19: Invalid input
    # ============================================================

    {
        "name": "19 - Invalid Python",
        "code": """import pandas as pd

df = df.append(
""",
        "expected_findings": set(),
        "expected_strings": [],
        "forbidden_strings": [],
        "invalid": True,
    },

    # ============================================================
    # 20: No-op migration
    # ============================================================

    {
        "name": "20 - Already migrated code",
        "code": """import pandas as pd

df = pd.concat([df, new_row], ignore_index=True)

for column, series in df.items():
    print(column)
""",
        "expected_findings": set(),
        "expected_strings": ["pd.concat", ".items("],
        "forbidden_strings": [".append(", ".iteritems("],
    },
]


def run_evaluation():

    total = len(TEST_CASES)

    detection_passed = 0
    migration_passed = 0
    verification_passed = 0

    true_positives = 0
    false_positives = 0
    false_negatives = 0

    syntax_valid_count = 0

    print("=" * 70)
    print("API MIGRATION COPILOT")
    print("20-CASE END-TO-END EVALUATION")
    print("=" * 70)

    for test in TEST_CASES:

        print(f"\n{'-' * 70}")
        print(f"Test: {test['name']}")

        try:

            # ----------------------------------------------------
            # Run the actual migration pipeline
            # ----------------------------------------------------

            result = analyze_migration(
                code=test["code"],
                library="pandas",
                version_range="1.x->2.x",
                file_path="evaluation_test.py"
            )

            findings = result.get("findings", [])

            detected = {
                finding["api"]
                for finding in findings
            }

            expected = test["expected_findings"]

            # ----------------------------------------------------
            # Detection metrics
            # ----------------------------------------------------

            true_positives += len(detected & expected)
            false_positives += len(detected - expected)
            false_negatives += len(expected - detected)

            if detected == expected:
                detection_passed += 1
                print("Detection: PASS")
            else:
                print("Detection: FAIL")
                print(f"Expected: {expected}")
                print(f"Detected: {detected}")

            # ----------------------------------------------------
            # Invalid input
            # ----------------------------------------------------

            if test.get("invalid"):

                if not result.get("valid", True):
                    migration_passed += 1
                    print("Invalid input handling: PASS")
                else:
                    print("Invalid input handling: FAIL")

                continue

            # ----------------------------------------------------
            # Get migrated code
            # ----------------------------------------------------

            migrated_code = result.get("migrated_code", "")

            # ----------------------------------------------------
            # Syntax validity
            # ----------------------------------------------------

            verification = result.get("verification", {})

            if verification.get("syntax_valid"):
                syntax_valid_count += 1

            # ----------------------------------------------------
            # Check expected output
            # ----------------------------------------------------

            migration_success = True

            for expected_string in test["expected_strings"]:

                if expected_string not in migrated_code:
                    migration_success = False
                    print(
                        f"Missing expected output: "
                        f"{expected_string}"
                    )

            # ----------------------------------------------------
            # Check deprecated APIs are removed
            # ----------------------------------------------------

            for forbidden_string in test["forbidden_strings"]:

                if forbidden_string in migrated_code:
                    migration_success = False
                    print(
                        f"Deprecated API still present: "
                        f"{forbidden_string}"
                    )

            if migration_success:
                migration_passed += 1
                print("Migration: PASS")
            else:
                print("Migration: FAIL")

            # ----------------------------------------------------
            # Verification
            # ----------------------------------------------------

            if verification.get("valid"):

                verification_passed += 1
                print("Verification: PASS")

            else:

                print("Verification: FAIL")
                print(
                    verification.get(
                        "message",
                        "Verification failed."
                    )
                )

        except Exception as e:

            print("Test execution: FAIL")
            print(f"{type(e).__name__}: {e}")

    # ============================================================
    # Metrics
    # ============================================================

    precision_denominator = (
        true_positives + false_positives
    )

    recall_denominator = (
        true_positives + false_negatives
    )

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

    detection_success_rate = (
        detection_passed / total
    )

    migration_success_rate = (
        migration_passed / total
    )

    verification_rate = (
        verification_passed / total
    )

    syntax_valid_rate = (
        syntax_valid_count / total
    )

    # ============================================================
    # Final results
    # ============================================================

    print("\n")
    print("=" * 70)
    print("FINAL EVALUATION RESULTS")
    print("=" * 70)

    print(f"Total test cases:          {total}")
    print(f"Detection cases passed:    {detection_passed}")
    print(f"Migration cases passed:    {migration_passed}")
    print(f"Verification cases passed: {verification_passed}")

    print()
    print(f"Detection precision:       {precision:.2%}")
    print(f"Detection recall:          {recall:.2%}")
    print(f"Detection success rate:    {detection_success_rate:.2%}")
    print(f"Migration success rate:    {migration_success_rate:.2%}")
    print(f"Verification pass rate:    {verification_rate:.2%}")
    print(f"Syntax validity rate:      {syntax_valid_rate:.2%}")

    print("=" * 70)


if __name__ == "__main__":
    run_evaluation()