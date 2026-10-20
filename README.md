
# Graph-Guided Repository Navigation for Coding Agents

**Research project | Built with Shimu**

## 1. Overview

This project investigates whether graph-guided repository navigation can help coding agents locate relevant source files more effectively than standard text-based search.

The project will compare simple repository search methods using a controlled set of code-navigation questions.

## 2. Research Question

Can graph-guided repository navigation improve the retrieval of relevant source files compared with standard text-based search?

## 3. Proposed Methods

1. Baseline: keyword-based source-file search.
2. Alternative: improved query and search strategy.
3. Proposed method: graph-guided source-file retrieval using code dependencies.

These methods are proposed for evaluation. Their relative performance has not yet been established.

## 4. Planned Evaluation

The evaluation will use documented test questions and verified expected files.

Planned metrics:
- Top-1 accuracy
- Recall@5
- Search runtime
- Error analysis

All reported results will come from actual experiments.

## 5. Project Structure

- `src/`: search implementations
- `experiments/`: test cases and experiment scripts
- `results/`: metrics and experiment logs
- `references/`: research references
- `notes/`: research notes

## 6. Reproducibility

The project will document the repository used, software dependencies, test questions, evaluation protocol, and limitations.

## 7. Current Status

Research question defined. Implementation and experiments are pending.

## 8. Limitations

The results may depend on repository size, programming language, dependency extraction quality, and the difficulty of the test questions.

## 9. Ethics and Attribution

Code, datasets, and research references will be attributed to their original authors and used according to their licenses.
