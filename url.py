import os


def load_compare_urls(filepath: str = "urls.txt") -> list:
    """Original function — kept for backward compatibility."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(
            f"urls.txt not found at {os.path.abspath(filepath)}\n"
            f"Please create urls.txt and paste your Compare URLs one per line"
        )
    compare_urls = []
    skipped = []
    errors = []

    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()
    print(f"  Reading {filepath}: {len(lines)} lines found")
    print("-" * 50)

    for i, line in enumerate(lines, start=1):
        line = line.strip()
        if not line:
            continue
        if line.startswith("#"):
            skipped.append(f"Line {i}: comment — {line[:60]}")
            continue
        if not line.startswith("http"):
            errors.append(f"Line {i}: Invalid URL — {line[:60]}")
            continue
        compare_urls.append({"url": line})
        print(f"  Line {i:3} ✓  {line[:70]}{'...' if len(line) > 70 else ''}")

    print("-" * 50)
    print(f"  Total URLs loaded : {len(compare_urls)}")
    print(f"  Comments skipped  : {len(skipped)}")
    if errors:
        print(f"  Errors found      : {len(errors)}")
        for err in errors:
            print(f"    {err}")

    if len(compare_urls) == 0:
        raise ValueError("No valid URLs found in urls.txt!")
    print(f"  {len(compare_urls)} Compare URLs ready!")
    return compare_urls


# ─────────────────────────────────────────────────────────────────
#  NEW: Load Old + New URL pairs  line-by-line
# ─────────────────────────────────────────────────────────────────

def _read_urls_from_file(filepath: str) -> list:
    """Read a txt file and return list of valid URLs (strips blanks & comments)."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(
            f"File not found: {os.path.abspath(filepath)}\n"
            f"Please create '{filepath}' and add one URL per line."
        )
    urls = []
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for i, line in enumerate(lines, start=1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if not line.startswith("http"):
            print(f"  [SKIP] Line {i} in {filepath}: not a valid URL → {line[:60]}")
            continue
        urls.append(line)
    return urls


def load_url_pairs(old_file: str = "Old_URL.txt", new_file: str = "New_URL.txt") -> list:
    """
    Reads Old_URL.txt and New_URL.txt line by line.
    Pairs them index-wise: line 1 ↔ line 1, line 2 ↔ line 2 ...

    Returns:
        [
            {"old": "http://old-url-1", "new": "http://new-url-1"},
            {"old": "http://old-url-2", "new": "http://new-url-2"},
            ...
        ]
    """
    print("=" * 60)
    print("  LOADING URL PAIRS")
    print("=" * 60)

    old_urls = _read_urls_from_file(old_file)
    new_urls = _read_urls_from_file(new_file)

    print(f"  Old URLs loaded : {len(old_urls)}  (from {old_file})")
    print(f"  New URLs loaded : {len(new_urls)}  (from {new_file})")

    # Count mismatch check
    if len(old_urls) != len(new_urls):
        raise ValueError(
            f"\nURL count MISMATCH!\n"
            f"  {old_file} has {len(old_urls)} URLs\n"
            f"  {new_file} has {len(new_urls)} URLs\n"
            f"Both files must have the same number of URLs (one per line)."
        )

    pairs = []
    print("\n  Pairing URLs:")
    print("-" * 60)
    for i, (old, new) in enumerate(zip(old_urls, new_urls), start=1):
        pairs.append({"old": old, "new": new})
        print(f"  Pair {i:3}:")
        print(f"    OLD → {old[:70]}{'...' if len(old) > 70 else ''}")
        print(f"    NEW → {new[:70]}{'...' if len(new) > 70 else ''}")

    print("-" * 60)
    print(f"  Total pairs ready: {len(pairs)}")
    print("=" * 60)
    return pairs


# ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Test load_url_pairs
    pairs = load_url_pairs("Old_URL.txt", "New_URL.txt")
    print("\nFinal pairs:")
    for i, p in enumerate(pairs, start=1):
        print(f"  {i}. OLD: {p['old']}")
        print(f"     NEW: {p['new']}")