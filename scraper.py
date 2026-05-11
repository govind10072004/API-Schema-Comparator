# import httpx
# import asyncio
# import time


# # ─────────────────────────────────────────────────────────────────
# #  Existing functions (unchanged)
# # ─────────────────────────────────────────────────────────────────

# def fetch_global_url(url: str) -> dict:
#     try:
#         response = httpx.get(url, timeout=60, follow_redirects=True)
#         response.raise_for_status()
#         return {"url": url, "data": response.json(), "error": None}
#     except Exception as e:
#         return {"url": url, "data": None, "error": f"{type(e).__name__}: {str(e)}"}


# async def _fetch_one(client: httpx.AsyncClient, endpoint: dict) -> dict:
#     start = time.time()
#     try:
#         response = await client.get(endpoint["url"], timeout=60)
#         response.raise_for_status()
#         elapsed_ms = round((time.time() - start) * 1000, 2)
#         return {
#             "url":             endpoint["url"],
#             "label":           endpoint.get("label", endpoint["url"]),
#             "data":            response.json(),
#             "response_time_ms": elapsed_ms,
#             "error":           None,
#         }
#     except Exception as e:
#         return {
#             "url":             endpoint["url"],
#             "label":           endpoint.get("label", endpoint["url"]),
#             "data":            None,
#             "response_time_ms": None,
#             "error":           f"{type(e).__name__}: {str(e)}",
#         }


# async def _fetch_all_async(endpoints: list) -> list:
#     async with httpx.AsyncClient(follow_redirects=True, limits=httpx.Limits(max_connections=10)) as client:
#         tasks = [_fetch_one(client, ep) for ep in endpoints]
#         results = await asyncio.gather(*tasks)
#     return list(results)


# def fetchall(endpoints: list) -> list:
#     """Fetch a list of {url: ...} dicts concurrently. Returns list of result dicts."""
#     return asyncio.run(_fetch_all_async(endpoints))


# # ─────────────────────────────────────────────────────────────────
# #  NEW: fetch_pairs — takes old/new URL pairs, fetches both sides
# # ─────────────────────────────────────────────────────────────────

# def fetch_pairs(pairs: list) -> list:
#     """
#     Input:
#         pairs = [
#             {"old": "http://old-url-1", "new": "http://new-url-1"},
#             {"old": "http://old-url-2", "new": "http://new-url-2"},
#             ...
#         ]

#     Fetches OLD URLs and NEW URLs concurrently (separately),
#     then zips them back into combined result dicts.

#     Output:
#         [
#             {
#                 "old_url":  "http://old-url-1",
#                 "old_data": { ...json... },
#                 "new_url":  "http://new-url-1",
#                 "new_data": { ...json... },
#                 "error":    None   # or error string if fetch failed
#             },
#             ...
#         ]
#     """
#     print("=" * 60)
#     print(f"  FETCHING {len(pairs)} URL PAIRS")
#     print("=" * 60)

#     old_endpoints = [{"url": p["old"], "label": f"OLD-{i+1}"} for i, p in enumerate(pairs)]
#     new_endpoints = [{"url": p["new"], "label": f"NEW-{i+1}"} for i, p in enumerate(pairs)]

#     print(f"  Fetching {len(old_endpoints)} OLD URLs...")
#     old_results = fetchall(old_endpoints)

#     print(f"  Fetching {len(new_endpoints)} NEW URLs...")
#     new_results = fetchall(new_endpoints)

#     combined = []
#     ok_count  = 0
#     err_count = 0

#     print("\n  Results:")
#     print("-" * 60)
#     for i, (old_r, new_r) in enumerate(zip(old_results, new_results), start=1):
#         old_err = old_r.get("error")
#         new_err = new_r.get("error")
#         err_msg = None

#         if old_err:
#             err_msg = f"OLD fetch error: {old_err}"
#         elif new_err:
#             err_msg = f"NEW fetch error: {new_err}"

#         status = "✓ OK " if not err_msg else "✗ ERR"
#         if not err_msg:
#             ok_count += 1
#         else:
#             err_count += 1

#         print(f"  Pair {i:3}  [{status}]")
#         if err_msg:
#             print(f"           {err_msg}")

#         combined.append({
#             "old_url":  old_r["url"],
#             "old_data": old_r.get("data"),
#             "new_url":  new_r["url"],
#             "new_data": new_r.get("data"),
#             "error":    err_msg,
#         })

#     print("-" * 60)
#     print(f"  Success : {ok_count}")
#     print(f"  Errors  : {err_count}")
#     print("=" * 60)
#     return combined


# # ─────────────────────────────────────────────────────────────────
# if __name__ == "__main__":
#     from url import load_url_pairs
#     pairs   = load_url_pairs("Old_URL.txt", "New_URL.txt")
#     fetched = fetch_pairs(pairs)
#     for item in fetched:
#         print(f"OLD: {item['old_url']}")
#         print(f"NEW: {item['new_url']}")
#         print(f"ERR: {item['error']}")
#         print()



















import httpx
import asyncio
import time


async def fetch_one(client: httpx.AsyncClient, url: str) -> dict:
    start = time.time()
    try:
        response = await client.get(url, timeout=60)
        response.raise_for_status()
        return {
            "url":     url,
            "data":    response.json(),
            "time_ms": round((time.time() - start) * 1000, 2),
            "error":   None
        }
    except Exception as e:
        return {
            "url":     url,
            "data":    None,
            "time_ms": None,
            "error":   f"{type(e).__name__}: {str(e)}"
        }


async def fetch_all_async(urls: list) -> list:
    async with httpx.AsyncClient(
        follow_redirects=True,
        limits=httpx.Limits(max_connections=10)
    ) as client:
        tasks = [fetch_one(client, url) for url in urls]
        return list(await asyncio.gather(*tasks))


def fetch_all(urls: list) -> list:
    return asyncio.run(fetch_all_async(urls))


def fetch_pairs(pairs: list) -> list:
    """
    Takes pairs from load_url_pairs:
        [{"old": "http://...", "new": "http://..."}, ...]

    Fetches OLD and NEW URLs separately (both concurrently inside each batch).

    Returns:
        [
            {
                "old_url":  "http://...",
                "new_url":  "http://...",
                "old_data": {...},
                "new_data": {...},
                "error":    None
            },
            ...
        ]
    """
    old_urls = [p["old"] for p in pairs]
    new_urls = [p["new"] for p in pairs]

    print(f"  Fetching {len(old_urls)} OLD URLs...")
    old_results = fetch_all(old_urls)

    print(f"  Fetching {len(new_urls)} NEW URLs...")
    new_results = fetch_all(new_urls)

    combined = []
    print()
    print("  Results:")
    print("-" * 60)

    for i, (o, n) in enumerate(zip(old_results, new_results), start=1):
        error  = o["error"] or n["error"]
        status = "✓ OK " if not error else "✗ ERR"
        print(f"  Pair {i:3}  [{status}]")
        if error:
            print(f"           {error}")
        combined.append({
            "old_url":  o["url"],
            "new_url":  n["url"],
            "old_data": o["data"],
            "new_data": n["data"],
            "error":    error
        })

    ok  = sum(1 for c in combined if not c["error"])
    err = sum(1 for c in combined if c["error"])
    print("-" * 60)
    print(f"  Success : {ok}")
    print(f"  Errors  : {err}")
    print("=" * 60)
    return combined   