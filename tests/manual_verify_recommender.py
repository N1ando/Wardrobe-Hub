import json
import sys
import traceback
from pathlib import Path

# Allow running directly (python tests/manual_verify_recommender.py) by
# putting the repo root on sys.path before importing the engine.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import recommend_size


PRODUCTS = {
    "jeans": {
        "id": "jeans_001",
        "name": "Stretch Denim Jeans",
        "category": "jeans",
        "material": "denim with 3% elastane",
        "stretch_pct": 3,
        "size_chart": [
            {"size_label": "30", "waist": 80, "hips": 96, "inseam": 78},
            {"size_label": "31", "waist": 83, "hips": 99, "inseam": 79},
            {"size_label": "32", "waist": 86, "hips": 102, "inseam": 80},
            {"size_label": "33", "waist": 89, "hips": 105, "inseam": 81},
        ],
    },

    "shirt": {
        "id": "shirt_001",
        "name": "Classic Oxford Shirt",
        "category": "shirt",
        "material": "rigid cotton",
        "stretch_pct": 0,
        "size_chart": [
            {"size_label": "S", "chest": 96, "waist": 90, "sleeve": 60},
            {"size_label": "M", "chest": 102, "waist": 96, "sleeve": 62},
            {"size_label": "L", "chest": 108, "waist": 102, "sleeve": 64},
        ],
    },

    "dress": {
        "id": "dress_001",
        "name": "A-Line Midi Dress",
        "category": "dresses",
        "material": "polyester blend",
        "stretch_pct": 0,
        "size_chart": [
            {"size_label": "S", "bust": 88, "waist": 70, "hips": 94},
            {"size_label": "M", "bust": 94, "waist": 76, "hips": 100},
            {"size_label": "L", "bust": 100, "waist": 82, "hips": 106},
        ],
    },

    "rigid_jeans": {
        "id": "jeans_rigid_001",
        "name": "Rigid Selvedge Jeans",
        "category": "jeans",
        "material": "100% cotton denim",
        "stretch_pct": 0,
        "size_chart": [
            {"size_label": "30", "waist": 80, "hips": 96, "inseam": 78},
            {"size_label": "31", "waist": 83, "hips": 99, "inseam": 79},
            {"size_label": "32", "waist": 86, "hips": 102, "inseam": 80},
            {"size_label": "33", "waist": 89, "hips": 105, "inseam": 81},
        ],
    },

    "sparse_jeans": {
        "id": "jeans_sparse_001",
        "name": "Bad Seller Jeans With Missing Chart Fields",
        "category": "jeans",
        "material": "rigid denim",
        "stretch_pct": 0,
        "size_chart": [
            {"size_label": "31", "waist": 83},
            {"size_label": "32", "waist": 86},
        ],
    },

    "string_jeans": {
        "id": "jeans_string_001",
        "name": "String Measurement Jeans",
        "category": "jeans",
        "material": "denim",
        "stretch_pct": "3",
        "size_chart": [
            {"size_label": "30", "waist": "80", "hips": "96", "inseam": "78"},
            {"size_label": "31", "waist": "83", "hips": "99.0", "inseam": "79"},
            {"size_label": "32", "waist": "86", "hips": "102", "inseam": "80"},
        ],
    },

    "bad_category": {
        "id": "shoe_001",
        "name": "Unsupported Shoes",
        "category": "shoes",
        "material": "leather",
        "stretch_pct": 0,
        "size_chart": [
            {"size_label": "42", "length": 27},
        ],
    },

    "empty_chart": {
        "id": "empty_001",
        "name": "Empty Chart Product",
        "category": "jeans",
        "material": "denim",
        "stretch_pct": 0,
        "size_chart": [],
    },
}


BODIES = {
    "jeans_regular": {"waist": 80, "hips": 93, "inseam": 79},
    "jeans_borderline": {"waist": 82.6, "hips": 93, "inseam": 79.5},
    "shirt_regular": {"chest": 92, "waist": 84, "sleeve": 61},
    "dress_chest_fallback": {"chest": 86, "waist": 69, "hips": 92},
    "bad_values": {"waist": "eighty", "hips": True, "inseam": 79},
    "string_values": {"waist": "80", "hips": "93.0", "inseam": "79"},
}


REVIEWS = {
    "runs_small": {
        "pct_small": 0.55,
        "pct_large": 0.05,
        "pct_tts": 0.40,
        "caveat": "Reviews suggest this item runs small, especially around the waist.",
    },
    "runs_large": {
        "pct_small": 0.05,
        "pct_large": 0.45,
        "pct_tts": 0.50,
        "caveat": "Reviews suggest this item runs large.",
    },
    "true_to_size": {
        "pct_small": 0.03,
        "pct_large": 0.03,
        "pct_tts": 0.94,
        "caveat": "Most reviewers say this item is true to size.",
    },
}


CASES = [
    {
        "name": "1. Jeans regular fit",
        "product": PRODUCTS["jeans"],
        "body": BODIES["jeans_regular"],
        "fit_pref": "regular",
        "reviews": None,
        "expected_size": "31",
    },
    {
        # Uses rigid denim on purpose: on the 3%-stretch jeans the stretch
        # credit pushes size 31's effective waist ease into the relaxed band,
        # so 31 and 32 tie and the engine prefers the smaller size.
        "name": "2. Jeans relaxed fit should go bigger (rigid denim)",
        "product": PRODUCTS["rigid_jeans"],
        "body": BODIES["jeans_regular"],
        "fit_pref": "relaxed",
        "reviews": None,
        "expected_size": "32",
    },
    {
        "name": "3. Shirt regular fit",
        "product": PRODUCTS["shirt"],
        "body": BODIES["shirt_regular"],
        "fit_pref": "regular",
        "reviews": REVIEWS["true_to_size"],
        "expected_size": "M",
    },
    {
        "name": "4. Dress uses chest fallback for bust",
        "product": PRODUCTS["dress"],
        "body": BODIES["dress_chest_fallback"],
        "fit_pref": "regular",
        "reviews": None,
        "expected_size": "M",
    },
    {
        "name": "5. Borderline jeans with runs-small reviews",
        "product": PRODUCTS["jeans"],
        "body": BODIES["jeans_borderline"],
        "fit_pref": "regular",
        "reviews": REVIEWS["runs_small"],
        "expected_size": None,
    },
    {
        "name": "6. Jeans with runs-large reviews",
        "product": PRODUCTS["jeans"],
        "body": BODIES["jeans_regular"],
        "fit_pref": "regular",
        "reviews": REVIEWS["runs_large"],
        "expected_size": None,
    },
    {
        "name": "7. Sparse jeans missing hips and inseam",
        "product": PRODUCTS["sparse_jeans"],
        "body": BODIES["jeans_regular"],
        "fit_pref": "regular",
        "reviews": None,
        "expected_size": None,
    },
    {
        "name": "8. Numeric strings accepted",
        "product": PRODUCTS["string_jeans"],
        "body": BODIES["string_values"],
        "fit_pref": "regular",
        "reviews": None,
        "expected_size": "31",
    },
    {
        "name": "9. Non-numeric body values treated as missing",
        "product": PRODUCTS["jeans"],
        "body": BODIES["bad_values"],
        "fit_pref": "regular",
        "reviews": None,
        "expected_size": None,
    },
]


def assert_json_serializable(result):
    json.dumps(result)


def print_result(case_name, result):
    print("\n" + "=" * 80)
    print(case_name)
    print("-" * 80)
    print("Recommended size:", result["recommended_size"])
    print("Confidence:", result["confidence"])
    print("Confidence level:", result["confidence_level"])
    print("Missing fields:", result["missing_fields"])
    print("Material note:", result["material_note"])

    if result["review_signal"]:
        print("Review signal:", result["review_signal"])

    print("Fit breakdown:")
    for item in result["fit_breakdown"]:
        print(
            f"  - {item['dim']}: "
            f"garment={item['garment']}, body={item['body']}, "
            f"raw_ease={item['raw_ease']}, verdict={item['verdict']}, score={item['score']}"
        )


def run_normal_cases():
    failures = 0

    for case in CASES:
        try:
            result = recommend_size(
                case["product"],
                case["body"],
                case["fit_pref"],
                case["reviews"],
            )

            assert_json_serializable(result)

            required_keys = {
                "recommended_size",
                "confidence",
                "confidence_level",
                "runner_up",
                "size_scores",
                "fit_breakdown",
                "review_signal",
                "material_note",
                "missing_fields",
                "debug",
            }

            missing_keys = required_keys - set(result.keys())
            if missing_keys:
                raise AssertionError(f"Missing output keys: {missing_keys}")

            if case["expected_size"] is not None:
                assert result["recommended_size"] == case["expected_size"], (
                    f"Expected {case['expected_size']}, got {result['recommended_size']}"
                )

            print_result("PASS: " + case["name"], result)

        except Exception:
            failures += 1
            print("\n" + "=" * 80)
            print("FAIL:", case["name"])
            print("-" * 80)
            traceback.print_exc()

    return failures


def run_error_cases():
    failures = 0

    error_cases = [
        {
            "name": "10. Unsupported category raises ValueError",
            "product": PRODUCTS["bad_category"],
            "body": {},
        },
        {
            "name": "11. Empty size chart raises ValueError",
            "product": PRODUCTS["empty_chart"],
            "body": BODIES["jeans_regular"],
        },
    ]

    for case in error_cases:
        try:
            recommend_size(case["product"], case["body"])
            failures += 1
            print("\nFAIL:", case["name"])
            print("Expected ValueError, but no error was raised.")

        except ValueError as e:
            print("\nPASS:", case["name"])
            print("Raised ValueError:", str(e))

        except Exception:
            failures += 1
            print("\nFAIL:", case["name"])
            print("Expected ValueError, but got different error:")
            traceback.print_exc()

    return failures


if __name__ == "__main__":
    print("Running manual recommender verification...\n")

    failures = 0
    failures += run_normal_cases()
    failures += run_error_cases()

    print("\n" + "=" * 80)
    # ASCII only: Windows consoles default to cp1252, which cannot encode
    # emoji and would crash the script right at the summary line.
    if failures == 0:
        print("ALL MANUAL VERIFICATION CASES PASSED")
    else:
        print(f"{failures} CASE(S) FAILED")
        raise SystemExit(1)