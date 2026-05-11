import json
import os
from datetime import datetime


def get_type(value):
    if value is None:            return "null" ##check the value is which type of data using isinstance function
    if isinstance(value, bool):  return "bool"
    if isinstance(value, int):   return "int"
    if isinstance(value, float): return "float"
    if isinstance(value, str):   return "str"
    if isinstance(value, list):  return "array"
    if isinstance(value, dict):  return "object"
    return "unknown"


def is_empty(value):
    return value is None or value == "" or value == [] or value == {}


def find_item_label(item):
    ID_KEYS = ["id", "pid", "uid", "cid", "tid", "mid",
               "match_id", "team_id", "player_id", "competition_id",
               "venue_id", "season_id", "slug", "code", "key"]
    if not isinstance(item, dict):
        return str(item)
    for k in ID_KEYS:
        if k in item:
            return f"{k}={item[k]}"
    for k, v in item.items():
        if isinstance(v, (str, int)) and not isinstance(v, bool):
            return f"{k}={v}"
    return "?"


def compare_json(old, new, path=""):
    diffs = []

    old_type = get_type(old)
    new_type = get_type(new)

    if old_type != new_type:
        diffs.append({"type": "TYPE_MISMATCH", "path": path, "old_type": old_type, "new_type": new_type})
        return diffs

    if isinstance(old, dict):
        old_keys = set(old.keys())
        new_keys = set(new.keys())

        for key in sorted(old_keys - new_keys):
            diffs.append({
                "type":     "MISSING_IN_NEW",
                "path":     f"{path}.{key}" if path else key,
                "old_type": get_type(old[key]),
            })

        for key in sorted(new_keys - old_keys):
            diffs.append({
                "type":     "ADDED_IN_NEW",
                "path":     f"{path}.{key}" if path else key,
                "new_type": get_type(new[key]),
            })

        # KEY ORDER CHECK — same keys but different sequence?
        common = old_keys & new_keys
        old_order = [k for k in old.keys() if k in common]
        new_order = [k for k in new.keys() if k in common]
        if old_order != new_order:
            diffs.append({
                "type":      "KEY_ORDER_MISMATCH",
                "path":      path if path else "(root)",
                "old_order": old_order,
                "new_order": new_order,
            })

        for key in sorted(old_keys & new_keys):
            cur = f"{path}.{key}" if path else key
            diffs.extend(compare_json(old[key], new[key], cur))

    elif isinstance(old, list):
        if not old and not new:
            return diffs

        if not old:
            diffs.append({"type": "ARRAY_EMPTY_IN_OLD", "path": path})
            return diffs

        if not new:
            diffs.append({"type": "ARRAY_EMPTY_IN_NEW", "path": path})
            return diffs

        if len(old) != len(new):
            old_label_set = {find_item_label(item) for item in old}
            new_label_set = {find_item_label(item) for item in new}
            diffs.append({
                "type":      "COUNT_MISMATCH",
                "path":      path,
                "old_count": len(old),
                "new_count": len(new),
                "missing":   sorted(old_label_set - new_label_set),
                "extra":     sorted(new_label_set - old_label_set),
            })
        else:
            # ARRAY ORDER CHECK — same count, check if items sequence changed
            old_labels = [find_item_label(item) for item in old]
            new_labels = [find_item_label(item) for item in new]
            if old_labels != new_labels and set(old_labels) == set(new_labels):
                diffs.append({
                    "type":      "ARRAY_ORDER_MISMATCH",
                    "path":      path,
                    "old_order": old_labels,
                    "new_order": new_labels,
                })

        if isinstance(old[0], dict) and isinstance(new[0], dict):
            old_rep = {}
            for item in old:
                for k, v in item.items():
                    if k not in old_rep:
                        old_rep[k] = v

            new_rep = {}
            for item in new:
                for k, v in item.items():
                    if k not in new_rep:
                        new_rep[k] = v

            seen = set()
            for d in compare_json(old_rep, new_rep, path + "[*]"):
                if d["path"] not in seen:
                    seen.add(d["path"])
                    diffs.append(d)
        else:
            diffs.extend(compare_json(old[0], new[0], path + "[*]"))

    else:
        if is_empty(old) != is_empty(new):
            diffs.append({
                "type":      "EMPTY_VALUE_MISMATCH",
                "path":      path,
                "old_value": old,
                "new_value": new,
            })

    return diffs


def format_report(old_url, new_url, differences, index, total):
    SEP   = "=" * 68
    lines = []

    status = "PASS" if not differences else f"NEEDS FIX: {len(differences)} issue(s)"

    lines.append(SEP)
    lines.append(f"  ENDPOINT {index}/{total}")
    lines.append(f"  OLD : {old_url}")
    lines.append(f"  NEW : {new_url}")
    lines.append(f"  Status : {status}")
    lines.append(SEP)

    if differences:
        count    = [d for d in differences if d["type"] == "COUNT_MISMATCH"]
        added    = [d for d in differences if d["type"] == "ADDED_IN_NEW"]
        missing  = [d for d in differences if d["type"] == "MISSING_IN_NEW"]
        mismatch = [d for d in differences if d["type"] == "TYPE_MISMATCH"]
        empty    = [d for d in differences if d["type"] == "EMPTY_VALUE_MISMATCH"]
        arr_old  = [d for d in differences if d["type"] == "ARRAY_EMPTY_IN_OLD"]
        arr_new  = [d for d in differences if d["type"] == "ARRAY_EMPTY_IN_NEW"]

        if count:
            lines.append("")
            lines.append("  ARRAY COUNT MISMATCH:")
            for d in count:
                lines.append(f"    - {d['path']}  (OLD={d['old_count']}, NEW={d['new_count']})")
                if d["missing"]:
                    lines.append(f"        Missing in NEW : {', '.join(d['missing'])}")
                if d["extra"]:
                    lines.append(f"        Extra in NEW   : {', '.join(d['extra'])}")

        if added:
            lines.append("")
            lines.append("  ADDED IN NEW (remove from NEW):")
            for d in added:
                lines.append(f"    - {d['path']}  (type: {d.get('new_type', '?')})")

        if missing:
            lines.append("")
            lines.append("  MISSING IN NEW (add to NEW):")
            for d in missing:
                lines.append(f"    - {d['path']}  (type: {d.get('old_type', '?')})")

        if mismatch:
            lines.append("")
            lines.append("  DATATYPE CHANGED:")
            for d in mismatch:
                lines.append(f"    - {d['path']}")
                lines.append(f"        OLD: {d['old_type']}  ->  NEW: {d['new_type']}")

        if empty:
            lines.append("")
            lines.append("  EMPTY VALUE MISMATCH:")
            for d in empty:
                lines.append(f"    - {d['path']}")
                lines.append(f"        OLD: {repr(d['old_value'])}  ->  NEW: {repr(d['new_value'])}")

        if arr_old or arr_new:
            lines.append("")
            lines.append("  EMPTY ARRAY ISSUE:")
            for d in arr_old:
                lines.append(f"    - {d['path']}  empty in OLD, has data in NEW")
            for d in arr_new:
                lines.append(f"    - {d['path']}  has data in OLD, empty in NEW")

        key_order = [d for d in differences if d["type"] == "KEY_ORDER_MISMATCH"]
        arr_order = [d for d in differences if d["type"] == "ARRAY_ORDER_MISMATCH"]

        if key_order:
            lines.append("")
            lines.append("  KEY ORDER MISMATCH (dict keys in wrong sequence):")
            for d in key_order:
                lines.append(f"    - {d['path']}")
                lines.append(f"        OLD : {' -> '.join(d['old_order'])}")
                lines.append(f"        NEW : {' -> '.join(d['new_order'])}")

        if arr_order:
            lines.append("")
            lines.append("  ARRAY ORDER MISMATCH (items in wrong sequence):")
            for d in arr_order:
                lines.append(f"    - {d['path']}")
                lines.append(f"        OLD : {' -> '.join(d['old_order'])}")
                lines.append(f"        NEW : {' -> '.join(d['new_order'])}")

    lines.append("")
    return "\n".join(lines)


def run_comparator(fetched_pairs):
    os.makedirs("output", exist_ok=True)
    output_path = os.path.join("output", "groqsummaries.txt")

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
        lines.append("  FETCH ERRORS (could not compare these)")
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

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(SEP)
    print(f"  Done!  PASS: {pass_count}   NEEDS FIX: {fail_count}   Issues: {total_issues}")
    print(f"  Saved -> {output_path}")
    print(SEP)
    return output_path