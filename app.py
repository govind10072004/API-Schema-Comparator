




import time
import asyncio
from datetime import datetime

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import Response

from scraper import fetch_all_async
from comparator import compare_json, format_report

app = FastAPI(
    title="API Schema Comparator",
    description="Upload 2 URL files and download a JSON diff report",
    version="1.0.0",
)


@app.get("/")
def root():
    return {
        "status": "running",
        "usage": "POST /compare → upload Old_URLs file + New_URLs file",
    }


def parse_url_file(content: bytes, label: str) -> list[str]:
    """Read uploaded file bytes and return a clean list of URLs."""
    lines = content.decode("utf-8").strip().splitlines()
    urls = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if not line.startswith("http"):
            raise HTTPException(
                status_code=400,
                detail=f"{label}: Invalid URL '{line[:80]}' — must start with http",
            )
        urls.append(line)

    if not urls:
        raise HTTPException(
            status_code=400,
            detail=f"{label} is empty or has no valid URLs.",
        )
    return urls


def build_fetched_pairs(old_results: list, new_results: list) -> list:
    """Zip old and new fetch results into matched pairs."""
    pairs = []
    for old_r, new_r in zip(old_results, new_results):
        old_url = old_r["url"]
        new_url = new_r["url"]
        error   = old_r.get("error") or new_r.get("error")

        pairs.append({
            "old_url":  old_url,
            "new_url":  new_url,
            "old_data": None if error else old_r["data"],
            "new_data": None if error else new_r["data"],
            "error":    error,
        })
    return pairs


def build_report(fetched_pairs: list) -> str:
    """Run comparator on each pair and build the full report string."""
    ok_pairs  = [p for p in fetched_pairs if not p.get("error")]
    err_pairs = [p for p in fetched_pairs if p.get("error")]
    total     = len(ok_pairs)

    SEP   = "=" * 68
    lines = []

    lines.append(SEP)
    lines.append("  API SCHEMA COMPARISON REPORT")
    lines.append(f"  Generated : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"  Endpoints : {total} OK   {len(err_pairs)} Errors")
    lines.append(SEP)
    lines.append("")

    pass_count   = 0
    fail_count   = 0
    total_issues = 0

    for i, pair in enumerate(ok_pairs, start=1):
        diffs = compare_json(pair["old_data"], pair["new_data"])
        lines.append(format_report(pair["old_url"], pair["new_url"], diffs, i, total))
        if diffs:
            fail_count   += 1
            total_issues += len(diffs)
        else:
            pass_count += 1

    if err_pairs:
        lines.append(SEP)
        lines.append("  FETCH ERRORS")
        lines.append(SEP)
        for ep in err_pairs:
            lines.append(f"  OLD : {ep.get('old_url', 'N/A')}")
            lines.append(f"  NEW : {ep.get('new_url', 'N/A')}")
            lines.append(f"  ERR : {ep.get('error')}")
            lines.append("")

    lines.append(SEP)
    lines.append("  SUMMARY")
    lines.append(SEP)
    lines.append(f"  Total endpoints : {total}")
    lines.append(f"  PASS            : {pass_count}")
    lines.append(f"  NEEDS FIX       : {fail_count}")
    lines.append(f"  Total issues    : {total_issues}")
    lines.append(SEP)

    return "\n".join(lines)


@app.post("/compare")
async def compare(
    old_urls_file: UploadFile = File(..., description="Old API URLs — one per line"),
    new_urls_file: UploadFile = File(..., description="New API URLs — one per line"),
):
    pipeline_start = time.time()

    # Step 1 — Read uploaded files and parse URLs
    old_content = await old_urls_file.read()
    new_content = await new_urls_file.read()

    old_urls = parse_url_file(old_content, label="Old_URLs file")
    new_urls = parse_url_file(new_content, label="New_URLs file")

    if len(old_urls) != len(new_urls):
        raise HTTPException(
            status_code=400,
            detail=(
                f"Line count mismatch: "
                f"Old file has {len(old_urls)} URLs, "
                f"New file has {len(new_urls)} URLs. "
                f"Both files must have the same number of URLs."
            ),
        )

    # Step 2 — Fetch both URL sets concurrently
    old_results, new_results = await asyncio.gather(
        fetch_all_async(old_urls),
        fetch_all_async(new_urls),
    )

    fetched_pairs = build_fetched_pairs(old_results, new_results)

    ok  = [p for p in fetched_pairs if not p.get("error")]
    err = [p for p in fetched_pairs if p.get("error")]

    if not ok:
        raise HTTPException(
            status_code=502,
            detail="All URL fetches failed. Please check your URLs and try again.",
        )

    # Step 3 — Compare and build report
    report_text = build_report(fetched_pairs)
    total_time  = round(time.time() - pipeline_start, 2)
    ts_display  = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    SEP = "=" * 68
    report_text += (
        f"\n{SEP}\n"
        f"  PIPELINE SUMMARY\n"
        f"{SEP}\n"
        f"  Finished   : {ts_display}\n"
        f"  Total time : {total_time}s\n"
        f"  Pairs      : {len(fetched_pairs)}  (OK: {len(ok)}  Errors: {len(err)})\n"
        f"{SEP}\n"
    )

    # Step 4 — Send .txt file as download
    filename = f"Comparison_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt"

    return Response(
        content=report_text,
        media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )