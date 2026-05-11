import time
from datetime import datetime

from url        import load_url_pairs
from scraper    import fetch_pairs
from comparator import run_comparator

OLD_FILE = "Old_URL.txt"
NEW_FILE = "New_URL.txt"


def main():
    pipeline_start = time.time()

    print()
    print("=" * 65)
    print("  API SCHEMA COMPARATOR")
    print(f"  Started : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 65)

    # STEP 1: Load URL pairs from Old_URL.txt and New_URL.txt
    print("\nSTEP 1/3  Loading URL pairs...")
    print("=" * 65)
    try:
        pairs = load_url_pairs(OLD_FILE, NEW_FILE)
    except (FileNotFoundError, ValueError) as e:
        print(f"  ERROR: {e}")
        return
    print(f"  {len(pairs)} pairs loaded")

    # STEP 2: Fetch both OLD and NEW URLs concurrently
    print(f"\nSTEP 2/3  Fetching {len(pairs)} OLD + {len(pairs)} NEW URLs...")
    print("=" * 65)
    t2      = time.time()
    fetched = fetch_pairs(pairs)
    ok      = [f for f in fetched if not f["error"]]
    err     = [f for f in fetched if f["error"]]
    print(f"  Fetched in {round(time.time()-t2, 2)}s — OK: {len(ok)}  Errors: {len(err)}")

    if not ok:
        print("  No successful pairs to compare. Exiting.")
        return

    # STEP 3: Run pure Python schema comparator
    print(f"\nSTEP 3/3  Running schema comparison on {len(ok)} pairs...")
    print("=" * 65)
    t3          = time.time()
    output_file = run_comparator(fetched)
    print(f"  Done in {round(time.time()-t3, 2)}s")

    total_time = round(time.time() - pipeline_start, 2)
    print()
    print("=" * 65)
    print("  PIPELINE COMPLETE")
    print("=" * 65)
    print(f"  Finished    : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Total time  : {total_time}s")
    print(f"  Pairs       : {len(pairs)}  (OK: {len(ok)}  Errors: {len(err)})")
    print(f"  Output file : {output_file}")
    print("=" * 65)
    print()


if __name__ == "__main__":
    main()