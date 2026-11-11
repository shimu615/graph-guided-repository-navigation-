import csv
from pathlib import Path

root = Path(__file__).resolve().parent.parent
repo = root / "external" / "requests"
csv_path = root / "results" / "independent-query-set.csv"

checks = {
    "IND-001": ("src/requests/api.py", ["def request(", "def get("]),
    "IND-002": ("src/requests/sessions.py", ["class Session("]),
    "IND-003": ("src/requests/auth.py", ["class HTTPBasicAuth("]),
    "IND-004": ("src/requests/adapters.py", ["class HTTPAdapter("]),
    "IND-005": ("src/requests/models.py", ["class Request(", "class Response"]),
    "IND-006": ("src/requests/exceptions.py", ["class RequestException", "class HTTPError"]),
    "IND-007": ("src/requests/cookies.py", ["class RequestsCookieJar", "def cookiejar_from_dict("]),
    "IND-008": ("src/requests/status_codes.py", ["codes: LookupDict", "def _init("]),
    "IND-009": ("src/requests/structures.py", ["class CaseInsensitiveDict"]),
    "IND-010": ("src/requests/utils.py", ["def requote_uri(", "def prepend_scheme_if_needed("]),
    "IND-011": ("src/requests/hooks.py", ["def dispatch_hook("]),
    "IND-012": ("src/requests/__init__.py", ["__version__", "__all__ ="]),
}

with csv_path.open(encoding="utf-8-sig", newline="") as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames
    rows = list(reader)

if not fieldnames or not {"query_id", "proposed_target", "review_status", "reviewer_notes"}.issubset(fieldnames):
    raise ValueError("CSV columns do not match the expected schema.")

for row in rows:
    qid = row["query_id"].strip()
    if qid not in checks:
        continue

    relative_path, expected_symbols = checks[qid]
    target = (repo / relative_path).resolve()

    if not target.is_relative_to(repo.resolve()) or not target.is_file():
        row["review_status"] = "NEEDS_REVIEW"
        row["reviewer_notes"] = "Target file missing or outside repository; manual review required."
        continue

    text = target.read_text(encoding="utf-8", errors="replace")
    found = [symbol for symbol in expected_symbols if symbol in text]

    if len(found) == len(expected_symbols):
        row["proposed_target"] = relative_path
        row["review_status"] = "VERIFIED"
        row["reviewer_notes"] = "Checked target source; found: " + ", ".join(found)
    else:
        row["review_status"] = "NEEDS_REVIEW"
        row["reviewer_notes"] = (
            "Expected symbols not all found. Found: "
            + ", ".join(found)
            + "; manual review required."
        )

with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print("Review status counts:")
counts = {}
for row in rows:
    status = row["review_status"].strip()
    counts[status] = counts.get(status, 0) + 1
for status, count in sorted(counts.items()):
    print(f"{status}: {count}")
print(f"Updated: {csv_path}")


