# Step 5: Experimental Analysis and Error Investigation

Date: 2026-11-05

## 1. Experimental setup

- Repository: `psf/requests`
- Queries: 12
- Python files indexed: 37
- Directed graph edges: 304
- Graph boost: 0.1

## 2. Aggregate comparison

| Metric | Baseline | Graph | Difference |
|---|---:|---:|---:|
| Top-1 Accuracy | 0.2500 | 0.2500 | +0.0000 |
| Recall@5 | 0.5833 | 0.5833 | +0.0000 |
| MRR | 0.4213 | 0.4204 | -0.0009 |

## 3. Query-level ranking changes

| Query | Baseline rank | Graph rank | Change | Category |
|---|---:|---:|---:|---|
| IND-001 | 7 | 7 | +0 | UNCHANGED |
| IND-002 | 1 | 1 | +0 | UNCHANGED |
| IND-003 | 3 | 3 | +0 | UNCHANGED |
| IND-004 | 1 | 1 | +0 | UNCHANGED |
| IND-005 | 4 | 4 | +0 | UNCHANGED |
| IND-006 | 9 | 9 | +0 | UNCHANGED |
| IND-007 | 2 | 2 | +0 | UNCHANGED |
| IND-008 | 13 | 15 | -2 | REGRESSED |
| IND-009 | 2 | 2 | +0 | UNCHANGED |
| IND-010 | 1 | 1 | +0 | UNCHANGED |
| IND-011 | 20 | 20 | +0 | UNCHANGED |
| IND-012 | 11 | 11 | +0 | UNCHANGED |

## 4. Error investigation

### Improved queries

- None

### Regressed queries

- IND-008

### Unchanged queries

- IND-001
- IND-002
- IND-003
- IND-004
- IND-005
- IND-006
- IND-007
- IND-009
- IND-010
- IND-011
- IND-012

## 5. Interpretation and limitations

The graph method adds a one-hop neighbor score to the direct lexical score. This can raise files that are connected to lexically relevant files, even when the target itself has little direct lexical evidence.

A ranking change is not automatically an improvement in retrieval quality. The verified target rank is the evaluation reference used here.

This experiment uses one repository and twelve manually reviewed queries. It is exploratory and does not establish statistical significance or general superiority.

No parameter tuning was performed in this analysis.

## 6. Query-level score diagnostics

| Query | Direct score | Best neighbor score | Graph score | Neighbor count |
|---|---:|---:|---:|---:|
| IND-001 | 0.6429 | 0.8571 | 0.7286 | 18 |
| IND-002 | 0.8333 | 0.7500 | 0.9083 | 18 |
| IND-003 | 0.7000 | 0.9000 | 0.7900 | 12 |
| IND-004 | 0.7857 | 0.6429 | 0.8500 | 18 |
| IND-005 | 0.7500 | 0.8333 | 0.8333 | 18 |
| IND-006 | 0.4000 | 0.6000 | 0.4600 | 9 |
| IND-007 | 0.7273 | 0.7273 | 0.8000 | 12 |
| IND-008 | 0.2857 | 0.7143 | 0.3571 | 9 |
| IND-009 | 0.8333 | 0.8333 | 0.9167 | 11 |
| IND-010 | 0.8182 | 0.6364 | 0.8818 | 18 |
| IND-011 | 0.2308 | 0.6923 | 0.3000 | 18 |
| IND-012 | 0.2727 | 0.6364 | 0.3364 | 18 |
