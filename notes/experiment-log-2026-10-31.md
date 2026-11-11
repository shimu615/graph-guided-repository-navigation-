# October 31, 2026 — Reproducibility Check

## Configuration
- Repository: psf/requests
- Repository commit: `8018b864d79c38cf273c27b7615aaee6ab075d80`
- Independent queries: 12
- Query CSV SHA-256: `16eed990ed42c011b1d751366f7982357a4a5dbef641cf68a21a7fb954e198f3`

## Results
- Evaluation CSV identical across runs: True
- Summary JSON identical across runs: True
- Reproducible under this check: True

## Run fingerprints
- Run 1 CSV SHA-256: `625173c123757117d7fd3f8947149d263bd828c313b29a23b5a63fea5052a58a`
- Run 2 CSV SHA-256: `625173c123757117d7fd3f8947149d263bd828c313b29a23b5a63fea5052a58a`
- Run 1 JSON SHA-256: `a62436eda86abc11a630916c142c35925fb986dd4d2135a95703080236139880`
- Run 2 JSON SHA-256: `a62436eda86abc11a630916c142c35925fb986dd4d2135a95703080236139880`

## Interpretation
Both runs produced byte-identical CSV and JSON outputs.

## Limitations
- This checks repeatability in the current environment only.
- It does not establish generalization to other repositories.
- The query set is small.
- Matching outputs do not prove the scoring method is valid.
