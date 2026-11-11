# Literature Review
## Graph-Guided Repository Navigation for Coding Agents

Review started: 5 November 2026

## 1. Research Scope

This review focuses on:
- Source-code retrieval
- Repository-level code navigation
- Code dependency and repository graphs
- Graph-based semantic code retrieval
- Retrieval tools for LLM-based coding agents

## 2. Selected Research Papers

### Paper 1: RepoGraph (Ouyang et al., 2025)

Title: RepoGraph: Enhancing AI Software Engineering with Repository-level Code Graph

Venue: ICLR 2025

Main idea:
RepoGraph introduces a repository-level code graph to help AI
software engineering systems understand repository structure.

Reported evaluation:
The authors evaluate RepoGraph with multiple systems on SWE-bench
and also examine CrossCodeEval.

Relevance:
This work provides direct motivation for representing repository
structure as a graph.

Difference from this project:
Our prototype investigates a simpler file-level retrieval approach
using Python import relationships and a one-hop neighbor score.

Source:
https://proceedings.iclr.cc/paper_files/paper/2025/hash/4a4a3c197deac042461c677219efd36c-Abstract-Conference.html

### Paper 2: CodexGraph (Liu et al., 2025)

Title: CodexGraph: Bridging Large Language Models and Code Repositories
via Code Graph Databases

Venue: NAACL 2025, pages 142-160

Main idea:
CodexGraph integrates LLM agents with graph database interfaces
extracted from code repositories. Agents can construct and execute
graph queries for structure-aware retrieval and navigation.

Reported evaluation:
CrossCodeEval, SWE-bench, and EvoCodeBench, together with
five real-world coding applications.

Relevance:
It demonstrates the use of graph databases for repository-level
code understanding and navigation.

Difference from this project:
Our prototype does not use an LLM agent or graph database.
It uses a lightweight import graph and deterministic ranking.

Source:
https://aclanthology.org/2025.naacl-long.7/

### Paper 3: RepoNav (Chai et al., 2026)

Title: RepoNav: From Snippet Retrieval to File-Centered Repository
Navigation for Code Agents

Venue: EMNLP 2026, pages 33711-33726

Main idea:
RepoNav reorganizes retrieved snippets into a file-centered
navigation scaffold. It provides structural cues and candidate
targets to help agents compare related symbols.

Reported evaluation:
The paper reports improvements in function-level localization
across models on LocBench and repository-level question answering.

Relevance:
It highlights the importance of organizing retrieval results
around files and their internal structure.

Difference from this project:
RepoNav is a post-retrieval interface for coding agents.
Our prototype studies source-file ranking using import relationships.

Source:
https://aclanthology.org/2026.emnlp-main.1474/

### Paper 4: Deep Graph Matching and Searching for Semantic Code
Retrieval (Ling et al., 2021)

Venue: ACM Transactions on Knowledge Discovery from Data,
Volume 15, Issue 5, Article 3447571.

Main idea:
DGMS represents natural-language queries and code snippets
using graph-structured data and applies graph matching with
cross-attention for semantic retrieval.

Reported evaluation:
Two public code retrieval datasets involving Java and Python.
The authors also report ablation studies.

Relevance:
This work establishes an earlier research direction for
graph-structured semantic code retrieval.

Difference from this project:
DGMS uses learned graph matching. Our prototype uses
lexical matching and import-neighbor score propagation.

Source:
https://doi.org/10.1145/3447571

### Paper 5: One Tool Is Enough (Zhang et al., 2026)

Title: One Tool Is Enough: Reinforcement Learning of LLM Agents
for Repository-Level Code Navigation

Venue: ICML 2026, Proceedings of Machine Learning Research,
Volume 306, pages 155168-155194.

Main idea:
RepoNavigator uses an execution-aware tool that jumps to the
definition of an invoked symbol. The agent is trained with
reinforcement learning.

Relevance:
It provides recent context on execution-aware repository navigation.

Difference from this project:
This work trains an LLM agent. Our study evaluates a retrieval
ranking method without training an LLM.

Source:
https://proceedings.mlr.press/v306/zhang26an.html

### Paper 6: CodeGrep (Chen et al., 2026)

Title: CodeGrep: An RL-Trained Retrieval Agent for LLM Coding Agents

Venue: REALM 2026

Main idea:
CodeGrep is a retrieval agent trained to issue multi-turn grep,
glob, and file-reading tool calls for coding agents.

Reported evaluation:
The paper reports experiments on SWE-Bench Verified and
compares retrieval approaches in terms of downstream utility
and efficiency.

Relevance:
It provides a recent comparison point for retrieval systems
used by coding agents.

Difference from this project:
CodeGrep is an RL-trained agentic retriever, whereas our
prototype is a deterministic file-ranking method.

Source:
https://aclanthology.org/2026.realm-1.80/

## 3. Preliminary Comparison

Existing research explores repository graphs, graph databases,
semantic code matching, file-centered navigation, and
agent-based retrieval.

This project investigates a narrower and simpler setting:
a lexical baseline compared with a one-hop import-graph-guided
file-ranking method.

The comparison is limited to one repository and a manually
reviewed set of 12 queries.

## 4. Preliminary Research Gap

A possible experimental gap is the need for a transparent,
lightweight comparison of lexical file retrieval and
import-neighbor score propagation under the same verified
file-target queries.

This is a proposed positioning, not a claim that no prior
work has studied similar methods.

## 5. Evidence Limitations

The notes above are based on the published metadata and
abstract-level descriptions of the selected papers.

Before final paper submission:
- Read the full text of the most relevant papers.
- Verify their exact methods and datasets.
- Check reported metrics from the papers themselves.
- Add precise in-text citations.
- Revise the research gap after full-text review.

## 6. Step 3 Progress

- [x] Identified six relevant research papers.
- [x] Recorded publication venues and source links.
- [x] Prepared preliminary paper summaries.
- [x] Prepared an initial comparison with our prototype.
- [ ] Read full text of the selected papers.
- [ ] Verify detailed methods and reported results.
- [ ] Finalize related-work discussion and research gap.

## 7. Full-Text Review — 5 November 2026

### 7.1 RepoGraph (Ouyang et al., ICLR 2025)

Full-text review:
RepoGraph uses Tree-sitter and AST-based parsing to construct
a repository graph. Its graph contains reference and definition
nodes, with invoke and contain relationships. It retrieves
k-hop ego-graphs around relevant code elements.

Evaluation:
The authors evaluate RepoGraph with four software engineering
frameworks on SWE-bench Lite. They also evaluate transferability
using CrossCodeEval with 2,665 Python samples.

Important findings:
The paper reports improvements when RepoGraph is integrated
with the evaluated frameworks. It also investigates graph
retrieval variants and their context/token costs.

Limitations:
The main experiments use proprietary LLMs and Python.
The authors identify broader model and language coverage
as future work.

Relevance:
This paper directly motivates repository-level structural
information. Our prototype is much simpler: it ranks files
using lexical overlap and one-hop import-neighbor score
propagation rather than retrieving AST-based k-hop ego-graphs.

Citation key: ouyang2025repograph

### 7.2 CodexGraph (Liu et al., NAACL 2025)

Full-text review:
CodexGraph applies static analysis to construct a graph
database. Its Python schema includes MODULE, CLASS, METHOD,
FUNCTION, FIELD, and GLOBAL_VARIABLE nodes, and relationships
such as CONTAINS, INHERITS, HAS_METHOD, HAS_FIELD, and USES.

Evaluation:
The paper uses CrossCodeEval Lite (Python), SWE-bench Lite,
and EvoCodeBench. It evaluates multiple LLM backbones and
compares with BM25, AutoCodeRover, and No-RAG baselines.

Important findings:
The authors report that graph-edge information can be useful.
Their ablation removes graph edges and observes performance
decreases for some model/metric combinations.

Limitations:
The paper reports Python-only evaluation and identifies
graph construction efficiency and schema completeness
as areas for improvement. It also reports increased token
consumption in some settings.

Relevance:
CodexGraph is a close related work. Unlike its graph database
and LLM-generated graph queries, our prototype uses a
lightweight import graph and deterministic ranking.

Citation key: liu2025codexgraph

### 7.3 RepoNav (Chai et al., EMNLP 2026)

Full-text review:
RepoNav reorganizes retrieved snippets into a file-centered
navigation scaffold. It separates file discovery from
within-file function verification and provides structural
cues and candidate targets.

Evaluation:
The paper evaluates seven models on LocBench and also studies
repository-level question answering using SWE-QA-Bench.
Its controlled ablation includes 560 LocBench instances.

Important findings:
The authors report that structured evidence organization
improves function-level localization over the compared
retrieval interfaces. Their ablation compares File-Only,
Inline Scaffold, and Tree Scaffold settings.

Limitations:
The implementation uses Python AST extraction and the
evaluation focuses on Python repositories and two benchmarks.
The authors leave other programming languages and additional
downstream tasks for future evaluation.

Relevance:
RepoNav focuses on post-retrieval navigation, whereas our
prototype focuses on ranking candidate source files.

Citation key: chai2026reponav

### 7.4 Deep Graph Matching and Searching for Semantic Code Retrieval
(Ling et al., 2021)

Full-text review:
DGMS represents natural-language queries and code snippets
as graph-structured data. It uses graph neural networks and
cross-attention-based matching to estimate semantic similarity.

Evaluation:
The paper evaluates on two public code retrieval datasets
covering Java and Python and reports ablation studies.

Important distinction:
DGMS performs learned semantic matching between queries
and code snippets. Our prototype does not train a graph
neural network; it uses lexical token overlap and import
neighbor score propagation.

Citation key: ling2021dgms

### 7.5 One Tool Is Enough (Zhang et al., ICML 2026)

Full-text review:
RepoNavigator is an LLM agent with an execution-aware
jump-to-definition tool. The agent is trained using
reinforcement learning to navigate repository code.

Evaluation:
The paper reports repository-level issue-localization
experiments and comparisons with other agent systems.

Relevance:
This work illustrates the importance of execution-aware
navigation. Our current project does not train an LLM agent
and does not evaluate patch resolution.

Citation key: zhang2026onetoole

### 7.6 CodeGrep (Chen et al., REALM 2026)

Full-text review:
CodeGrep is a 14B retrieval agent trained using GRPO.
It issues multi-turn grep, glob, and file-reading calls
and returns candidate files to a downstream coding agent.

Evaluation:
The paper evaluates on 500 SWE-Bench Verified instances
using an OpenHands downstream agent.

Important findings:
The authors report fewer downstream agent rounds and tokens
while preserving the reported resolve rate. They also compare
BM25, Jina, and CodeGrep retrieval.

Limitations:
The authors state that the resolve-rate difference is not
statistically distinguishable from noise in their paired
set. Their downstream results use one agent stack and one
benchmark. Retrieval-side generation and serving costs are
not included in the reported downstream efficiency figures.

Relevance:
CodeGrep studies learned agentic retrieval, while our
prototype studies deterministic file ranking.

Citation key: chen2026codegrep

## 8. Final Related-Work Synthesis

Prior work has investigated repository-level code graphs,
graph database interfaces, learned graph matching,
file-centered navigation scaffolds, execution-aware
navigation tools, and agentic retrieval.

The present prototype investigates a narrower experimental
setting: lexical source-file retrieval compared with
deterministic one-hop import-neighbor score propagation.

The study uses one Python repository and twelve manually
reviewed file-target queries. Its contribution should
therefore be framed as a small, transparent comparative
evaluation rather than a general solution to repository
navigation.

## 9. Final Literature Review Limitations

- The six papers study different tasks and evaluation settings.
- Their reported benchmark metrics are not directly comparable
  with our Top-1 Accuracy, Recall@5, or MRR.
- The current project uses only one repository and twelve queries.
- The review does not establish that the proposed method is novel
  across the entire code-navigation literature.
- No claim of general superiority is justified.

## 10. Step 3 Final Status

- [x] Six relevant papers identified.
- [x] Publication metadata and source links checked.
- [x] Full-text or publicly available full-paper versions reviewed.
- [x] Methods, evaluation settings, and limitations summarized.
- [x] Comparison with the current prototype documented.
- [x] Preliminary research gap revised.
- [x] Related-work synthesis prepared.
