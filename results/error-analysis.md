# Error Analysis

- Evaluation rows: 24
- Top-1 errors: 2

This report describes observed rankings; it does not establish
that either retrieval method is generally better.

## baseline — Q10

- Query: `calculate_student_grade`
- Expected file: `student.py`
- Top-1 file: `report.py`
- Expected rank: `2`
- Ranked files: `report.py > student.py`

### Initial interpretation

Inspect whether the query contains an exact identifier,
whether that identifier is imported or referenced in other
files, and whether the ranking score distinguishes definition
from usage. Treat this as a hypothesis to investigate.

## graph — Q10

- Query: `calculate_student_grade`
- Expected file: `student.py`
- Top-1 file: `report.py`
- Expected rank: `2`
- Ranked files: `report.py > student.py`

### Initial interpretation

Inspect whether the query contains an exact identifier,
whether that identifier is imported or referenced in other
files, and whether the ranking score distinguishes definition
from usage. Treat this as a hypothesis to investigate.

