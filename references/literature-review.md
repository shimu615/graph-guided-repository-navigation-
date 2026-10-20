
# Literature Review Notes

## 1. CodeSearchNet Challenge (2019)

Authors: Hamel Husain, Ho-Hsiang Wu, Tiferet Gazit,
Miltiadis Allamanis, Marc Brockschmidt.

Link: https://arxiv.org/abs/1909.09436

Key idea:
Natural-language queries can be evaluated against relevant code
using documented retrieval benchmarks and relevance judgments.

Use in this project:
Motivates consistent test queries and explicit expected files.

## 2. GraphCodeBERT (2020)

Authors: Daya Guo et al.

Link: https://arxiv.org/abs/2009.08366

Key idea:
Code has structural information, including data-flow relationships,
that may help code understanding.

Use in this project:
Motivates testing whether repository structure helps retrieval.

Important distinction:
This project currently uses a simple import-dependency graph.
It does not reproduce GraphCodeBERT or its neural architecture.

## Research Gap to Investigate

Can a lightweight import-dependency graph improve file retrieval
on a small, controlled repository-navigation benchmark?

This is a research question, not an established finding.
It requires evaluation against a baseline.
