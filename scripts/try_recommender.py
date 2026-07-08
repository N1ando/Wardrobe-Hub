"""Poke the FitOS recommender by hand against the seeded demo products.

Examples (run from the repo root):
    python scripts/try_recommender.py --list
    python scripts/try_recommender.py jeans_001 --waist 81 --hips 94 --inseam 79
    python scripts/try_recommender.py dress_001 --persona riley
    python scripts/try_recommender.py dress_001 --persona riley --no-reviews
    python scripts/try_recommender.py shirt_001 --persona sam --fit regular --json
"""

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from core import recommend_size  # noqa: E402  (needs REPO_ROOT on sys.path)

SEED_DIR = REPO_ROOT / "data" / "seed"
MEASUREMENTS = ("chest", "bust", "waist", "hips", "inseam", "sleeve", "height")


def _load(name: str):
    return json.loads((SEED_DIR / name).read_text(encoding="utf-8"))


def _print_catalog(products, personas):
    print("Products:")
    for p in products.values():
        sizes = "/".join(str(row.get("size_label")) for row in p["size_chart"])
        print(f"  {p['id']:<10}  {p['name']}  [{p['category']}]  sizes {sizes}")
    print("\nPersonas:")
    for name, persona in personas.items():
        body = ", ".join(f"{k}={v}" for k, v in persona["measurements"].items())
        print(f"  {name:<8}  fit={persona['fit_pref']:<8} {body}")
        print(f"            {persona['label']}")


def _print_pretty(result):
    print(f"Recommended size : {result['recommended_size']}")
    print(f"Confidence       : {result['confidence']}% ({result['confidence_level']})")
    if result["runner_up"]:
        print(f"Runner-up        : {result['runner_up']['size']} (score {result['runner_up']['score']})")
    print(f"Material note    : {result['material_note']}")
    if result["missing_fields"]:
        print(f"Missing fields   : {', '.join(result['missing_fields'])}")
    signal = result["review_signal"]
    if signal:
        print(f"Review signal    : bias={signal['bias_direction']}, shift_applied={signal['applied_shift_bias']}")
        if signal["caveat"]:
            print(f"                   caveat: {signal['caveat']}")

    print("\nFit breakdown (recommended size):")
    for d in result["fit_breakdown"]:
        if d["verdict"] == "missing_data":
            print(f"  {d['dim']:<8} missing data")
            continue
        lo, hi = d["ideal_band"]
        print(
            f"  {d['dim']:<8} garment {d['garment']:>6.1f}  body {d['body']:>6.1f}  "
            f"ease {d['raw_ease']:>+6.1f}  ideal {lo:g}..{hi:g}  "
            f"{d['verdict']:<7} score {d['score']}"
        )

    print("\nAll size scores:")
    for s in result["size_scores"]:
        bar = "#" * round(s["adjusted_score"] * 30)
        bonus = f"  (+{s['review_bonus']:g} from reviews)" if s["review_bonus"] else ""
        print(f"  {s['size']:>4}  {s['adjusted_score']:<6} {bar}{bonus}")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("product_id", nargs="?", help="seed product id (see --list)")
    parser.add_argument("--list", action="store_true", help="list seeded products and personas")
    parser.add_argument("--persona", help="start from a persona in data/seed/personas.json")
    parser.add_argument("--fit", choices=["slim", "regular", "relaxed"],
                        help="fit preference (overrides the persona's)")
    parser.add_argument("--no-reviews", action="store_true",
                        help="ignore the product's seeded review_analysis")
    parser.add_argument("--json", action="store_true", help="print the raw recommendation JSON")
    for name in MEASUREMENTS:
        parser.add_argument(f"--{name}", type=float, help=f"body {name} in cm")
    args = parser.parse_args(argv)

    products = {p["id"]: p for p in _load("products.json")}
    personas = _load("personas.json")

    if args.list or not args.product_id:
        _print_catalog(products, personas)
        return 0

    if args.product_id not in products:
        print(f"Unknown product id {args.product_id!r}. Use --list to see options.")
        return 1

    measurements = {}
    fit_pref = "regular"
    if args.persona:
        if args.persona not in personas:
            print(f"Unknown persona {args.persona!r}. Use --list to see options.")
            return 1
        measurements.update(personas[args.persona]["measurements"])
        fit_pref = personas[args.persona]["fit_pref"]
    for name in MEASUREMENTS:  # explicit flags override persona values
        value = getattr(args, name)
        if value is not None:
            measurements[name] = value
    if args.fit:
        fit_pref = args.fit
    if not measurements:
        print("No measurements given. Pass --persona or flags like --waist 81 --hips 94.")
        return 1

    product = products[args.product_id]
    reviews = None if args.no_reviews else product.get("review_analysis")
    result = recommend_size(product, measurements, fit_pref, reviews)

    if args.json:
        print(json.dumps(result, indent=2))
        return 0

    print(f"\n{product['name']} ({product['id']})  |  fit_pref={fit_pref}  |  "
          f"reviews={'off' if reviews is None else 'seeded'}")
    print("-" * 72)
    _print_pretty(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
