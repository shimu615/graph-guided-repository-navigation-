# Graph-Guided Repository Navigation for Coding Agents

**An Exploratory Evaluation of Import-Graph-Guided File Retrieval Against Lexical Search**

## Overview

This research investigates whether lightweight graph-guided repository navigation can improve source-file retrieval compared with lexical search.

We implement a deterministic one-hop import-neighbor scoring approach and evaluate it on the Python source files of the [`psf/requests`](https://github.com/psf/requests) repository.

The study provides an exploratory comparison of lexical and graph-guided retrieval, including parameter sensitivity, robustness checks, and statistical analysis.

## Research Question

**Does graph-guided repository navigation improve source-file retrieval effectiveness compared with lexical search in software repositories?**

## Repository and Dataset

- Target repository: `psf/requests`
- Commit: `611c6162cbc4ac2020a2f91c7cfa4f3abf9bbb60`
- Indexed Python files: 37
- Directed import-graph entries: 304
- Manually reviewed retrieval queries: 12

## Methods

### 1. Lexical Baseline

Retrieves candidate source files using lexical matching.

### 2. Graph-Guided Retrieval

Uses one-hop import-neighbor information to adjust file retrieval scores.

### Evaluation Metrics

- Top-1 Accuracy
- Recall@5
- Mean Reciprocal Rank (MRR)

Additional experiments examine graph-boost sensitivity, edge dropout, ranking repeatability, and statistical comparisons.

## Main Results

| Metric | Lexical Baseline | Graph-Guided (0.10) |
|---|---:|---:|
| Top-1 Accuracy | 0.2500 | 0.2500 |
| Recall@5 | 0.5833 | 0.5833 |
| MRR | 0.421261 | 0.420406 |

The graph-guided method did not improve Top-1 accuracy or Recall@5. Its MRR was marginally lower than the lexical baseline.

The paired comparison produced 0 wins, 11 ties, and 1 loss for graph-guided retrieval.

These findings are exploratory and do not establish that graph-based navigation is generally ineffective.

## Reproducibility

The project includes:

- Retrieval implementations
- Import-graph construction
- Evaluation scripts
- Dataset validation
- Ablation and robustness experiments
- Statistical analysis
- Automated tests

The final project test suite completed with **86 passed tests**.

## Project Structure

```text
.
├── configs/
├── experiments/
├── notes/
├── references/
├── results/
├── src/
├── tests/
├── README.md
├── requirements.txt
└── pytest.ini
```

## Installation

```bash
git clone https://github.com/shimu615/graph-guided-repository-navigation.git
cd graph-guided-repository-navigation

python -m venv .venv
```

Activate the environment:

**Windows PowerShell**
```powershell
.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run tests:

```bash
pytest -q
```

## Limitations

- The evaluation uses one Python repository.
- The query set contains only 12 manually reviewed queries.
- The graph representation focuses on one-hop import relationships.
- The experiment evaluates file retrieval, not end-to-end coding-agent task completion.
- Results should not be generalized to other repositories or programming languages without further evaluation.

## Future Work

Future research will investigate:

- Evaluation across multiple repositories.
- Larger and more diverse query sets.
- Additional lexical and structural retrieval baselines.
- Multi-hop and richer repository graphs.
- Integration with end-to-end coding-agent workflows.

## Research Scope

This repository presents an exploratory study of graph-guided source-file retrieval. It does not claim that the experiments were conducted using Gemma 4 or that an end-to-end Gemma 4 coding agent was evaluated.

## Citation

If you use this research, please cite the project repository:

**Graph-Guided Repository Navigation for Coding Agents.**

## License

A license will be added after selecting an appropriate open-source license.