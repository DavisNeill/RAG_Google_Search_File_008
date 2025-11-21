# Research Evaluation Framework for Journal Publication

**Complete evaluation system for Agentic RAG - Ready for journal publication (TACL, JAIR, ACL, EMNLP, etc.)**

This framework provides comprehensive, state-of-the-art evaluation tools to scientifically validate your Agentic RAG system and justify its performance for publication in top-tier journals.

---

## Table of Contents

1. [Overview](#overview)
2. [Framework Components](#framework-components)
3. [Quick Start](#quick-start)
4. [Detailed Usage](#detailed-usage)
5. [Metrics Explained](#metrics-explained)
6. [Running Complete Evaluation](#running-complete-evaluation)
7. [Publication Outputs](#publication-outputs)
8. [Example Workflow](#example-workflow)
9. [Requirements](#requirements)
10. [Citation](#citation)

---

## Overview

### What This Framework Provides

✅ **State-of-the-Art Metrics**
- RAGAS metrics (faithfulness, answer relevancy, context precision/recall)
- Traditional IR metrics (Precision@k, Recall@k, MRR, NDCG, MAP)
- Semantic similarity (BERTScore, ROUGE, BLEU)

✅ **Rigorous Statistical Analysis**
- Paired t-tests with Bonferroni correction
- Cohen's d effect sizes
- Bootstrap confidence intervals
- Wilcoxon signed-rank tests

✅ **Comparative Analysis**
- 5 baseline implementations for comparison
- Ablation studies to prove component contributions
- Error analysis with categorization

✅ **Publication-Ready Outputs**
- LaTeX tables ready for direct inclusion
- High-quality figures (300 DPI, PDF format)
- Comprehensive reports

---

## Framework Components

### Core Modules

```
evaluation_framework.py      Main orchestrator for running experiments
metrics_ragas.py            RAGAS evaluation metrics
metrics_ir.py               Traditional IR metrics
metrics_semantic.py         Semantic similarity metrics
statistical_analysis.py     Statistical significance testing
baselines.py                Baseline system implementations
ablation.py                 Ablation study framework
visualization.py            Publication-quality plots
latex_export.py             LaTeX table generation
error_analysis.py           Error categorization and analysis
dataset_builder.py          Evaluation dataset management
```

---

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Create Evaluation Dataset

```python
from dataset_builder import DatasetBuilder, GroundTruthItem

builder = DatasetBuilder()

# Create dataset from questions
questions = [
    "What is machine learning?",
    "How does neural network training work?",
    # ... more questions
]

dataset = builder.create_from_queries(
    questions,
    "ml_evaluation",
    "Machine Learning QA Dataset"
)

# Add ground truth
builder.add_ground_truth(
    dataset,
    query_id="q_0001",
    ground_truth_answer="Machine learning is...",
    relevant_doc_ids=["doc_1", "doc_5"],
    annotator_id="annotator_1"
)

# Save dataset
builder.save_dataset(dataset, "datasets/ml_eval.json")
```

### 3. Run Evaluation

```python
from evaluation_framework import EvaluationFramework, EvaluationConfig

# Configure evaluation
config = EvaluationConfig(
    experiment_name="agentic_rag_evaluation",
    dataset_path="datasets/ml_eval.json",
    evaluate_baselines=True,
    evaluate_ablations=True,
    compute_ragas=True,
    compute_ir_metrics=True,
    compute_semantic=True,
    compute_significance=True,
    generate_latex=True,
    generate_plots=True
)

# Initialize framework
framework = EvaluationFramework(config)

# Define systems to evaluate
systems = {
    'Agentic RAG': your_agentic_rag_system,
    'Vanilla RAG': vanilla_rag_baseline,
    'RAG + Memory': rag_with_memory_baseline,
    # ... more systems
}

# Run full evaluation
results = framework.run_full_evaluation(systems)
```

### 4. Get Publication Outputs

All outputs are automatically generated:

- **LaTeX Tables**: `latex_tables/`
  - `system_comparison.tex`
  - `ablation_table.tex`
  - `significance_table.tex`

- **Figures**: `figures/`
  - `system_comparison.pdf`
  - `ablation_study.pdf`
  - `performance_latency.pdf`

- **Reports**: `reports/`
  - `evaluation_report.txt`
  - `error_analysis_report.txt`

---

## Detailed Usage

### Metrics Computation

#### RAGAS Metrics

```python
from metrics_ragas import RAGASEvaluator

evaluator = RAGASEvaluator()

# Evaluate single query
scores = evaluator.evaluate_single(
    question="What is AI?",
    answer="AI is artificial intelligence...",
    contexts=["AI stands for...", "Machine learning is a subset..."],
    ground_truth="AI is artificial intelligence..."
)

print(f"Faithfulness: {scores.faithfulness:.3f}")
print(f"Answer Relevancy: {scores.answer_relevancy:.3f}")
print(f"Context Precision: {scores.context_precision:.3f}")
```

#### Traditional IR Metrics

```python
from metrics_ir import IRMetricsEvaluator

evaluator = IRMetricsEvaluator(k_values=[1, 3, 5, 10, 20])

# Evaluate retrieval
scores = evaluator.evaluate_retrieval(
    retrieved_docs=["doc1", "doc2", "doc3", "doc4", "doc5"],
    relevant_docs=["doc1", "doc3", "doc7"]
)

print(f"Precision@5: {scores['precision@5']:.3f}")
print(f"Recall@5: {scores['recall@5']:.3f}")
print(f"NDCG@5: {scores['ndcg@5']:.3f}")
print(f"MRR: {scores['mrr']:.3f}")
```

#### Semantic Similarity

```python
from metrics_semantic import SemanticEvaluator

evaluator = SemanticEvaluator()

# Compute BERTScore
scores = evaluator.compute_bertscore_batch(
    predictions=["Machine learning is...", "AI stands for..."],
    references=["ML is a subset of AI", "Artificial Intelligence..."]
)

print(f"BERTScore F1: {scores['bertscore_f1']:.3f}")

# Compute ROUGE-L
scores = evaluator.compute_rouge_batch(predictions, references)
print(f"ROUGE-L F1: {scores['rouge_l_f1']:.3f}")
```

### Statistical Significance Testing

```python
from statistical_analysis import StatisticalAnalyzer

analyzer = StatisticalAnalyzer(alpha=0.05)

# Paired t-test
system_a_scores = [0.85, 0.82, 0.87, 0.84, 0.86]
system_b_scores = [0.78, 0.75, 0.80, 0.77, 0.79]

result = analyzer.paired_t_test(system_a_scores, system_b_scores)

print(f"t-statistic: {result.statistic:.3f}")
print(f"p-value: {result.p_value:.4f}")
print(f"Significant? {result.is_significant}")
print(f"Effect size (Cohen's d): {result.effect_size:.3f}")
```

### Ablation Studies

```python
from ablation import AblationStudy

# Initialize ablation study
study = AblationStudy(full_agentic_rag_system)

# Define standard ablations
study.define_standard_ablations()

# Run ablations on evaluation questions
questions = ["What is ML?", "How does backprop work?", ...]
results = study.run_batch_ablations(questions)

# Compute impact
analysis = study.compute_ablation_impact(results, metric_name='f1')

# Generate table
table = study.generate_ablation_table(analysis)
print(table)
```

### Baseline Comparisons

```python
from baselines import create_standard_baselines

# Create baseline manager
manager = create_standard_baselines(
    retriever=vector_store.as_retriever(),
    generator=llm,
    query_classifier=query_classifier,
    bm25_retriever=bm25
)

# Run all baselines
questions = ["Question 1", "Question 2", ...]
results = manager.run_batch_evaluation(questions)

# Compare
for system_name, system_results in results.items():
    avg_score = np.mean([r.scores['f1'] for r in system_results])
    print(f"{system_name}: {avg_score:.3f}")
```

### Error Analysis

```python
from error_analysis import ErrorAnalyzer

analyzer = ErrorAnalyzer(score_threshold=0.7)

# Identify errors
errors = analyzer.identify_errors(evaluation_results)

# Categorize errors
categories = analyzer.categorize_errors(errors)

# Analyze patterns
analysis = analyzer.analyze_query_characteristics(errors)

# Generate report
report = analyzer.generate_error_report("error_report.txt")
```

### Visualization

```python
from visualization import PaperVisualizer

viz = PaperVisualizer(output_dir="./figures")

# System comparison
viz.plot_system_comparison(
    results={'Agentic RAG': {'F1': 0.85}, 'Vanilla RAG': {'F1': 0.72}},
    metric_name='F1',
    title='System Performance Comparison'
)

# Ablation study
viz.plot_ablation_study(
    ablation_results={'No Memory': 0.75, 'No Query Agent': 0.70},
    baseline_score=0.85,
    title='Component Contribution Analysis'
)

# Performance vs Latency
viz.plot_performance_vs_latency(
    systems_data={
        'Agentic RAG': (0.85, 250),
        'Vanilla RAG': (0.72, 100)
    }
)
```

### LaTeX Export

```python
from latex_export import LaTeXExporter

exporter = LaTeXExporter(output_dir="./latex_tables")

# System comparison table
exporter.export_system_comparison(
    results=system_results,
    metrics=['precision', 'recall', 'f1', 'ndcg'],
    caption="Performance comparison across systems"
)

# Ablation table
exporter.export_ablation_table(
    ablation_results=ablation_data,
    baseline_score=0.85,
    caption="Ablation study results showing component contributions"
)

# Statistical significance
exporter.export_significance_table(
    comparisons=[
        ('Agentic RAG', 'Vanilla RAG', 0.001, 12.5, 0.8),
        ('Agentic RAG', 'RAG+Memory', 0.032, 2.3, 0.3)
    ],
    caption="Statistical significance of system comparisons"
)
```

---

## Metrics Explained

### RAGAS Metrics

| Metric | What It Measures | Range | Higher Is Better? |
|--------|------------------|-------|-------------------|
| **Faithfulness** | Is answer grounded in retrieved contexts? | 0-1 | Yes |
| **Answer Relevancy** | Does answer address the question? | 0-1 | Yes |
| **Context Precision** | Are retrieved contexts relevant? | 0-1 | Yes |
| **Context Recall** | Did we retrieve all necessary info? | 0-1 | Yes |
| **Context Relevancy** | How focused are retrieved contexts? | 0-1 | Yes |

### Traditional IR Metrics

| Metric | What It Measures | Formula |
|--------|------------------|---------|
| **Precision@k** | Fraction of top-k that are relevant | relevant_in_top_k / k |
| **Recall@k** | Fraction of relevant docs in top-k | relevant_in_top_k / total_relevant |
| **MRR** | Mean Reciprocal Rank of first relevant | 1 / rank_of_first_relevant |
| **NDCG@k** | Normalized discounted cumulative gain | DCG@k / IDCG@k |
| **MAP** | Mean average precision | mean(precision at each relevant doc) |

### Semantic Similarity

| Metric | What It Measures | Best For |
|--------|------------------|----------|
| **BERTScore** | Semantic similarity using BERT embeddings | Meaning preservation |
| **ROUGE-L** | Longest common subsequence | Summary quality |
| **BLEU** | N-gram overlap | Translation, generation |

---

## Running Complete Evaluation

### Full Workflow Example

```python
# 1. Setup
from evaluation_framework import EvaluationFramework, EvaluationConfig
from baselines import create_standard_baselines
from dataset_builder import DatasetBuilder

# 2. Load/Create dataset
builder = DatasetBuilder()
dataset = builder.load_dataset("datasets/evaluation.json")

# 3. Configure evaluation
config = EvaluationConfig(
    experiment_name="full_evaluation",
    dataset_path="datasets/evaluation.json",
    evaluate_baselines=True,
    evaluate_ablations=True,
    compute_ragas=True,
    compute_ir_metrics=True,
    compute_semantic=True,
    compute_significance=True,
    include_human_eval=False,  # Set True if you have human annotations
    generate_latex=True,
    generate_plots=True
)

# 4. Initialize framework
framework = EvaluationFramework(config)

# 5. Define systems
systems = {
    'Agentic RAG (Full)': agentic_rag_system,
    'Vanilla RAG': vanilla_rag,
    'RAG + Memory': rag_memory,
    'RAG + Agents': rag_agents,
    'BM25 Baseline': bm25_baseline
}

# 6. Run evaluation
results = framework.run_full_evaluation(systems)

# 7. Outputs are automatically generated in:
#    - latex_tables/
#    - figures/
#    - reports/
```

---

## Publication Outputs

### What You Get for Your Paper

#### Tables (LaTeX)

1. **System Comparison Table** (`system_comparison.tex`)
   - Ready to copy-paste into paper
   - Best scores automatically bolded
   - Includes all metrics

2. **Ablation Study Table** (`ablation_table.tex`)
   - Shows contribution of each component
   - Performance drop when components removed
   - Sorted by impact

3. **Statistical Significance Table** (`significance_table.tex`)
   - p-values for all pairwise comparisons
   - t-statistics
   - Significance markers (*, **, ***)

4. **Query Type Breakdown** (`query_type_table.tex`)
   - Performance by question type
   - Shows where system excels

#### Figures (PDF, 300 DPI)

1. **System Comparison** (`system_comparison.pdf`)
   - Bar chart comparing systems
   - Professional, camera-ready

2. **Ablation Study** (`ablation_study.pdf`)
   - Component contribution visualization
   - Two-panel figure

3. **Performance vs Latency** (`performance_latency.pdf`)
   - Trade-off analysis
   - Scatter plot

4. **Statistical Significance** (`statistical_significance.pdf`)
   - p-value visualization
   - Significance thresholds

#### Reports

1. **Evaluation Report** (`evaluation_report.txt`)
   - Complete numerical results
   - All metrics for all systems
   - Statistical summaries

2. **Error Analysis Report** (`error_analysis_report.txt`)
   - Error categorization
   - Failure pattern analysis
   - Recommendations

---

## Example Workflow

### Journal Submission Checklist

- [ ] **Dataset Created**: Well-documented evaluation dataset with ground truth
- [ ] **Baselines Implemented**: At least 4 baseline systems for comparison
- [ ] **Metrics Computed**: RAGAS + IR metrics + semantic similarity
- [ ] **Ablation Studies**: Systematic component removal to show contributions
- [ ] **Statistical Tests**: p-values < 0.05 for all key comparisons
- [ ] **Effect Sizes**: Cohen's d computed (aim for |d| > 0.5)
- [ ] **Error Analysis**: Detailed analysis of failure cases
- [ ] **Reproducibility**: Code and data availability statement
- [ ] **Figures**: High-quality, publication-ready (300 DPI)
- [ ] **Tables**: LaTeX formatted, ready for inclusion

### Writing Your Results Section

```markdown
## Results

### Overall Performance

Table 1 shows the performance comparison across all systems. Our Agentic RAG
system significantly outperforms all baselines (p < 0.001, Cohen's d = 0.85).

**[Insert: system_comparison.tex]**

### Ablation Study

To validate the contribution of each component, we conducted systematic ablation
studies (Table 2). Removing the Query Agent resulted in the largest performance
drop (Δ = -0.12, 14% relative decrease), demonstrating its critical role.

**[Insert: ablation_table.tex]**

### Statistical Significance

All improvements over baselines are statistically significant (Table 3), with
p-values well below the conventional threshold of 0.05.

**[Insert: significance_table.tex]**

### Performance Analysis

Figure 1 illustrates the performance-latency trade-off. Our system achieves
superior performance (F1 = 0.85) with reasonable latency (250ms), positioning
it favorably compared to baselines.

**[Insert: system_comparison.pdf, ablation_study.pdf]**
```

---

## Requirements

### Python Packages

```
# Core evaluation
ragas>=0.1.0
scikit-learn>=1.3.0
scipy>=1.11.0
numpy>=1.24.0

# Metrics
bert-score>=0.3.13
sentence-transformers>=2.2.2
rouge-score>=0.1.2
nltk>=3.8.0

# Visualization
matplotlib>=3.7.0
seaborn>=0.12.0
plotly>=5.17.0

# Data handling
datasets>=2.14.0
pandas>=2.0.0

# Statistical analysis
statsmodels>=0.14.0

# Export
tabulate>=0.9.0
```

### Installation

```bash
pip install -r requirements.txt

# Download NLTK data
python -c "import nltk; nltk.download('punkt')"
```

---

## Citation

If you use this evaluation framework in your research, please cite:

```bibtex
@software{agentic_rag_eval_framework,
  title = {Research Evaluation Framework for Agentic RAG Systems},
  author = {Your Name},
  year = {2025},
  url = {https://github.com/yourusername/agentic-rag}
}
```

---

## Best Practices for Journal Publication

### 1. Dataset Quality
- Minimum 100 queries for robust evaluation
- Diverse query types
- Multiple annotators for ground truth (inter-annotator agreement > 0.8)
- Clear annotation guidelines

### 2. Baseline Selection
- Include at least 4 baselines:
  - Simple baseline (BM25, TF-IDF)
  - Standard RAG baseline
  - 2-3 relevant published methods
- Use same evaluation data for all systems

### 3. Statistical Rigor
- Report p-values for all comparisons
- Use Bonferroni correction for multiple comparisons
- Report effect sizes (Cohen's d)
- Include confidence intervals

### 4. Ablation Studies
- Remove one component at a time
- Show statistical significance of each component
- Explain why components contribute

### 5. Error Analysis
- Categorize failure cases
- Discuss limitations
- Propose future improvements

### 6. Reproducibility
- Share code and data
- Document all hyperparameters
- Provide random seeds
- Include system requirements

---

## Support

For questions or issues:
1. Check this documentation
2. Review example code in each module
3. See inline code comments
4. Check the evaluation examples

---

**🎯 This framework is designed to meet the highest standards of journal publication. All metrics, visualizations, and statistical tests are publication-ready!**
