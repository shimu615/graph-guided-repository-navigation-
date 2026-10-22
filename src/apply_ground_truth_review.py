import csv
from pathlib import Path

path = Path("notes/ground-truth-review.csv")

# Labels reviewed against the three source files shown by the researcher.
reviews = {
    "Q01": ("student.py", "calculate_student_grade(marks) calculates grades from marks."),
    "Q02": ("report.py", "generate_report creates a student performance report."),
    "Q03": ("database.py", "connect_database handles database host and username."),
    "Q04": ("student.py", "The grade calculation function is defined in student.py."),
    "Q05": ("report.py", "generate_report uses calculate_student_grade to build the report."),
    "Q06": ("database.py", "connect_database accepts the host parameter."),
    "Q07": ("student.py", "calculate_student_grade returns A, B, or C based on marks."),
    "Q08": ("report.py", "generate_report returns the student name and calculated grade."),
    "Q09": ("database.py", "connect_database accepts host and username."),
    "Q10": ("student.py", "The calculate_student_grade function definition is in student.py; report.py imports and calls it."),
    "Q11": ("report.py", "The generate_report function is defined in report.py."),
    "Q12": ("database.py", "The connect_database function is defined in database.py."),
}

if not path.exists():
    raise SystemExit(f"Review CSV not found: {path}")

with path.open("r", encoding="utf-8-sig", newline="") as f:
    rows = list(csv.DictReader(f))

if len(rows) != 12:
    raise SystemExit(f"Expected 12 rows, found {len(rows)}")

seen = set()
for row in rows:
    case_id = row["case_id"]
    if case_id not in reviews:
        raise SystemExit(f"Unexpected case ID: {case_id}")
    if case_id in seen:
        raise SystemExit(f"Duplicate case ID: {case_id}")
    seen.add(case_id)

    label, note = reviews[case_id]
    if row["expected_file_from_dataset"] != label:
        raise SystemExit(
            f"{case_id}: dataset label is {row['expected_file_from_dataset']}, "
            f"but review mapping says {label}. Inspect manually."
        )

    row["reviewer_verified_label"] = label
    row["reviewer_notes"] = note

with path.open("w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)

print("Reviewed labels saved:", path)
print("Cases reviewed:", len(rows))
print("All expected labels matched the source-code review mapping.")
print("Note: this is a source-code-based review, not independent validation.")
