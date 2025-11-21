# Practical Guide: From Code to Published Paper

**Your Complete Roadmap from Running Experiments to Journal Publication**

---

## Table of Contents

1. [What You Need to Understand](#what-you-need-to-understand)
2. [Two Paths to Publication](#two-paths-to-publication)
3. [Step-by-Step: Running Experiments](#step-by-step-running-experiments)
4. [Understanding the Results](#understanding-the-results)
5. [Writing the Narrative](#writing-the-narrative)
6. [From Results to Paper](#from-results-to-paper)
7. [Timeline and Effort](#timeline-and-effort)

---

## What You Need to Understand

### What Are "Standard Benchmarks"?

**Standard benchmarks** = Public datasets that all researchers use to compare systems fairly.

**Analogy:** Just like SAT scores let colleges compare students fairly, benchmarks let reviewers compare RAG systems.

**Popular RAG benchmarks:**
- **HotpotQA**: 113k questions requiring multi-hop reasoning
- **Natural Questions**: 307k real Google search queries
- **MS MARCO**: 1M passage ranking questions
- **SQuAD**: 100k reading comprehension questions

**Why reviewers want benchmarks:**
✅ Reproducibility (they can verify your results)
✅ Fair comparison (same test for everyone)
✅ Established difficulty (known hard problems)

### What Does "Run Experiments" Mean?

**Experiment** = Testing your system against baselines on questions with known answers

**What you're measuring:**
1. **Quality**: How accurate are the answers?
2. **Cost**: How much does it cost to run?
3. **Speed**: How fast does it respond?
4. **Reliability**: Does it fail or produce errors?

**What you get:**
- Numbers (metrics like "Recall@5: 0.78")
- Comparisons ("Our system: 0.78 vs Baseline: 0.74 = +5.4% improvement")
- Statistical proof ("p < 0.01" = improvement is real, not random)

### What Does "Write the Narrative" Mean?

**Narrative** = The story that explains WHY your numbers matter

**Example:**

❌ **Bad (just numbers):**
"Our system achieved Recall@5 of 0.78, NDCG@10 of 0.79, and BERTScore of 0.85."

✅ **Good (narrative):**
"Production RAG deployments face a critical cost challenge: using premium models like GPT-4 for all queries costs $125 per 1,000 queries, limiting scalability. We introduce smart model routing, which analyzes query complexity and routes simple questions to inexpensive models. This achieves 58% cost reduction while maintaining competitive quality (Recall@5: 0.78 vs 0.74 baseline, +5.4%). The cost savings enable large-scale deployment: at 10M queries/year, our approach saves $800k compared to single-model baselines."

**See the difference?** The narrative:
- Explains the PROBLEM (cost is too high)
- Introduces your SOLUTION (smart routing)
- Shows IMPACT (58% cheaper, still accurate)
- Demonstrates REAL-WORLD value ($800k savings)

---

## Two Paths to Publication

### Path 1: Quick Publication (Custom Dataset) ⚡

**Timeline:** 3-6 months
**Difficulty:** Medium
**Best for:** Domain-specific applications, industry conferences

**What you do:**
1. Create 100-200 questions in your domain
2. Manually write reference answers
3. Run your system and baselines
4. Write paper showing your system is better

**Pros:**
✅ Faster (no need to download/process huge datasets)
✅ Domain-specific (relevant to your application)
✅ Full control over questions

**Cons:**
❌ Less prestigious (reviewers prefer standard benchmarks)
❌ Harder to compare with published work
❌ May need to justify dataset quality

**Good for venues:**
- EMNLP Industry Track
- ACL Industry Track
- Domain-specific journals

**Use script:** `run_evaluation_simple.py`

---

### Path 2: Top-Tier Publication (Standard Benchmarks) 🏆

**Timeline:** 6-12 months
**Difficulty:** Hard
**Best for:** Academic conferences (EMNLP, ACL, NAACL)

**What you do:**
1. Download public benchmarks (HotpotQA, Natural Questions)
2. Run your system on them (takes longer, more questions)
3. Compare against published baselines
4. Show statistically significant improvements

**Pros:**
✅ Most prestigious (top conference tier)
✅ Direct comparison with published work
✅ Reproducible (reviewers can verify)
✅ Stronger impact

**Cons:**
❌ Slower (processing thousands of questions)
❌ More complex (benchmark formats vary)
❌ Need strong computational resources

**Good for venues:**
- EMNLP (main track)
- ACL (main track)
- NAACL (main track)
- TACL (journal)

**Use script:** `run_evaluation_benchmarks.py`

---

## Step-by-Step: Running Experiments

### Prerequisites

```bash
# 1. Install dependencies
pip install datasets  # For downloading benchmarks
pip install ragas bert-score rouge-score  # For metrics
pip install matplotlib seaborn plotly  # For figures

# 2. Set API key
export GEMINI_API_KEY='your-api-key-here'

# 3. Create directories
mkdir -p datasets
mkdir -p evaluation_results
mkdir -p benchmark_results
```

### Option A: Quick Start (Custom Dataset)

**Step 1: Create Your Dataset (30 minutes - 2 hours)**

```python
# Edit run_evaluation_simple.py

# Replace the example questions with YOUR questions
questions = [
    "What is [topic in your domain]?",
    "How does [process in your domain] work?",
    "Compare [A] and [B] in [your domain]",
    # Add 50-200 questions
]

# Add reference answers
ground_truths = {
    "q_0001": "Your reference answer here...",
    "q_0002": "Another reference answer...",
    # Add answers for all questions
}
```

**Where to get questions:**
- Your product's FAQ
- Customer support queries
- Domain expert interviews
- Literature review questions
- Exam questions in your field

**Step 2: Prepare Knowledge Base (1-2 hours)**

Gather documents for your RAG system to search:

```python
# Your documents (PDFs, text files, etc.)
file_paths = [
    "docs/manual.pdf",
    "docs/faq.txt",
    "docs/technical_spec.pdf",
    # Add all relevant documents (10-100+ files)
]
```

**Step 3: Run Evaluation (2-6 hours depending on dataset size)**

```bash
python run_evaluation_simple.py
```

**What happens:**
1. Creates dataset: `datasets/evaluation_dataset.json`
2. Uploads documents to all systems
3. Runs each system on each question
4. Computes metrics (RAGAS, BERTScore, etc.)
5. Runs statistical tests
6. Generates LaTeX tables and PDF figures

**Output:**
```
evaluation_results/
├── latex_tables/
│   ├── system_comparison.tex
│   ├── ablation_table.tex
│   └── significance_table.tex
├── figures/
│   ├── system_comparison.pdf
│   ├── ablation_study.pdf
│   └── performance_latency.pdf
└── reports/
    ├── evaluation_report.txt
    └── error_analysis_report.txt
```

---

### Option B: Standard Benchmarks

**Step 1: Download Benchmarks (10-30 minutes)**

```bash
python run_evaluation_benchmarks.py
```

This automatically downloads:
- HotpotQA (multi-hop questions)
- Natural Questions (factual questions)

**Step 2: Prepare Knowledge Base**

For benchmarks, you typically need a large general corpus:

```python
# Option 1: Use Wikipedia dump
# Download from: https://dumps.wikimedia.org/

# Option 2: Use context from datasets
# Many benchmarks include relevant passages

# Option 3: Use general knowledge corpus
file_paths = [
    "wikipedia/articles_1.txt",
    "wikipedia/articles_2.txt",
    # ... many files
]
```

**Step 3: Run Benchmark Evaluation (4-12 hours)**

```bash
python run_evaluation_benchmarks.py
```

**What happens:**
- Downloads 100-1000 questions from each benchmark
- Runs 4 systems on each question
- Computes all metrics
- Generates publication materials

**Output:**
Same structure as Option A, but in `benchmark_results/` directory

---

## Understanding the Results

### What the Numbers Mean

After running evaluation, you'll see output like:

```
System Comparison:
System                          Recall@5    NDCG@10    BERTScore   Cost/1k
--------------------------------------------------------------------------------
Enhanced RAG (Full)             0.780       0.790      0.850       $52.50
Enhanced RAG (No Routing)       0.778       0.788      0.848       $125.00
RAG (No Validation)             0.775       0.785      0.845       $125.00
Vanilla RAG                     0.740       0.760      0.820       $125.00
```

**How to interpret:**

1. **Recall@5** (0-1, higher is better)
   - "Of the top 5 retrieved documents, what % were actually relevant?"
   - 0.780 = 78% of top-5 docs were relevant
   - **Your system: 0.780 vs Baseline: 0.740 = +5.4% improvement**

2. **NDCG@10** (0-1, higher is better)
   - "How good is the ranking of top 10 documents?"
   - Considers both relevance AND position
   - **Your system: 0.790 vs Baseline: 0.760 = +3.9% improvement**

3. **BERTScore** (0-1, higher is better)
   - "How semantically similar is generated answer to reference?"
   - Uses BERT embeddings to measure meaning overlap
   - **Your system: 0.850 vs Baseline: 0.820 = +3.7% improvement**

4. **Cost/1k** (dollars, lower is better)
   - "Cost to run 1,000 queries"
   - **Your system: $52.50 vs Baseline: $125 = 58% cost reduction**

### Statistical Significance

You'll also see:

```
Statistical Significance:
Enhanced RAG vs Vanilla RAG: p = 0.0008 (**, highly significant)
Cohen's d = 0.85 (large effect size)
```

**What this means:**
- **p < 0.05**: Improvement is real (not random chance)
- **p < 0.01**: Highly confident (marked with **)
- **Cohen's d = 0.85**: Large practical difference

**For your paper:**
"Our system significantly outperforms Vanilla RAG (p < 0.001, Cohen's d = 0.85), demonstrating both statistical and practical significance."

---

## Writing the Narrative

### From Numbers to Story

You have the numbers. Now tell the story.

### Paper Structure Template

#### 1. Abstract (200-250 words)

```
Production deployment of Retrieval-Augmented Generation (RAG) systems
faces three critical challenges: prohibitive costs from using premium
LLMs for all queries, reliability issues from unstructured outputs, and
limited observability for debugging. We introduce [Your System Name], a
novel RAG architecture that addresses these challenges through smart
model routing, structured output validation, and comprehensive tracing.

Our system analyzes query complexity and routes simple questions to
inexpensive models (gemini-1.5-flash: $0.075/1k tokens) and complex
queries to premium models (gemini-1.5-pro: $1.25/1k tokens), achieving
40-60% cost reduction. Structured output validation using Pydantic
reduces parsing errors from 12% to <0.1%. Comprehensive observability
with Logfire provides full pipeline tracing with <2ms overhead.

We evaluate on HotpotQA and Natural Questions benchmarks (n=1,000 each).
Our system achieves competitive quality (Recall@5: 0.78 vs 0.74 baseline,
+5.4%, p<0.001) while reducing costs by 58%. At 10M queries/year, this
represents $800k savings compared to single-model baselines. Ablation
studies confirm that model routing contributes 138% cost impact and
structured validation eliminates 96% of errors.

Our work demonstrates that production-ready RAG systems can achieve both
high quality and economic viability through intelligent model selection
and robust output validation.
```

#### 2. Introduction (1-1.5 pages)

**Paragraph 1: Motivation**
```
Retrieval-Augmented Generation (RAG) has emerged as a promising approach
for grounding large language model outputs in factual knowledge [citations].
However, production deployment at scale faces significant economic barriers.
Using premium models like GPT-4 for all queries costs $125 per 1,000
queries, making 10M query/year deployments cost $1.2M annually. This
prohibitive cost limits RAG adoption for many applications.
```

**Paragraph 2: Gap in existing work**
```
While prior work focuses on improving retrieval quality [citations], cost
optimization remains underexplored. Existing RAG systems [LangChain,
LlamaIndex] use a single model for all queries, ignoring the observation
that query complexity varies widely: simple factual questions ("What is X?")
require less sophisticated reasoning than complex analytical queries
("Analyze the relationship between X and Y").
```

**Paragraph 3: Your contribution**
```
We introduce smart model routing, which analyzes query complexity and
selects appropriate models dynamically. Simple queries (70% of workload)
use inexpensive models, while complex queries use premium models only when
necessary. This achieves 40-60% cost reduction while maintaining quality.
```

**Paragraph 4: Key results**
```
We evaluate on standard benchmarks (HotpotQA, Natural Questions, n=2,000)
and show:
- 58% cost reduction vs single-model baselines
- Competitive quality (+5.4% Recall@5, p<0.001)
- 96% reduction in parsing errors through structured validation
- Full observability with <2ms overhead
```

**Paragraph 5: Impact**
```
Our work makes three contributions:
1. Smart model routing algorithm for cost-aware RAG
2. Structured output validation framework (Pydantic integration)
3. Comprehensive evaluation showing production viability

Code and datasets available at: [URL]
```

#### 3. Related Work (1-2 pages)

**Subsection: Retrieval-Augmented Generation**
```
Lewis et al. [citation] introduced RAG, combining retrieval with generation...
[Summarize 5-10 key RAG papers]

Our work differs by focusing on cost optimization rather than just quality.
```

**Subsection: Query Complexity Analysis**
```
Query difficulty estimation has been studied in IR [citations]...
We adapt these techniques for model selection in RAG systems.
```

**Subsection: Cost Optimization in LLMs**
```
Recent work explores inference optimization [citations]...
We introduce dynamic model selection based on query characteristics.
```

#### 4. Method (2-3 pages)

**Subsection: System Architecture**
```
Figure 1 shows our six-tier architecture...

[Describe each tier briefly, focus on Tier 6 novel contributions]
```

**Subsection: Smart Model Routing**
```
Algorithm 1 shows our routing algorithm.

Input: Query q
Output: Model m

1. Extract features from q (length, keywords, patterns)
2. Classify complexity: SIMPLE, MODERATE, COMPLEX
3. Select model based on complexity and cost policy:
   - SIMPLE → gemini-1.5-flash
   - MODERATE → gemini-1.5-flash
   - COMPLEX → gemini-1.5-pro
4. Return m

We classify queries using pattern matching:
- SIMPLE: Greetings, factual questions, definitions
- MODERATE: How-to questions, explanations
- COMPLEX: Analysis, reasoning, multi-step

[Include actual algorithm or pseudocode]
```

**Subsection: Structured Output Validation**
```
We enforce a strict schema using Pydantic...

[Show the RAGResponse schema]
[Explain validation and retry logic]
```

#### 5. Experimental Setup (1-2 pages)

**Subsection: Datasets**
```
We evaluate on two standard benchmarks:

1. HotpotQA [citation]: 1,000 multi-hop questions requiring reasoning
   across multiple documents. Difficulty: hard.

2. Natural Questions [citation]: 1,000 factual questions from real
   Google searches. Difficulty: medium.

Both datasets provide ground truth answers for automatic evaluation.
```

**Subsection: Baselines**
```
We compare against:

1. Vanilla RAG: BM25 retrieval + direct generation
2. Our System (No Routing): All features except model routing
3. Our System (No Validation): All features except Pydantic
4. Our System (Full): All features enabled
```

**Subsection: Metrics**
```
We report:

- Retrieval Quality: Recall@5, NDCG@10, MRR
- Generation Quality: BERTScore F1, ROUGE-L
- RAG-Specific: RAGAS Faithfulness, Answer Relevancy
- Efficiency: Latency (ms), Cost per 1k queries ($)
- Reliability: Parse error rate (%)
```

**Subsection: Implementation Details**
```
- LLMs: gemini-1.5-flash ($0.075/1k), gemini-1.5-pro ($1.25/1k)
- Embeddings: text-embedding-004
- Vector DB: Qdrant
- Reranker: cross-encoder/ms-marco-MiniLM-L-6-v2

All experiments run on [hardware details].
Statistical significance tested with paired t-test (α=0.05).
```

#### 6. Results (2-3 pages)

**Subsection: Overall Performance**
```
Table 1 shows performance comparison across all systems.

[Include the auto-generated LaTeX table]

Our full system achieves:
- Recall@5: 0.780 (+5.4% vs Vanilla, p<0.001)
- NDCG@10: 0.790 (+3.9% vs Vanilla, p<0.001)
- BERTScore: 0.850 (+3.7% vs Vanilla, p<0.001)
- Cost: $52.50 (-58% vs Vanilla)

All quality improvements are statistically significant.
```

**Subsection: Ablation Study**
```
Table 2 presents ablation results showing each component's contribution.

[Include ablation table]

Key findings:
- Model Routing: 138% cost increase when disabled (most impactful)
- Structured Validation: 33x more parse errors without it
- Hybrid Search: 7.7% recall decrease without it
```

**Subsection: Cost Analysis**
```
Figure 2 shows cost breakdown.

Our system routes:
- 70% queries to Flash ($0.075/1k)
- 25% queries to Pro ($1.25/1k)
- 5% queries to advanced models

This achieves 58% cost reduction vs always-using-Pro.

At scale (10M queries/year):
- Baseline cost: $1,250,000
- Our system cost: $525,000
- Savings: $725,000/year
```

**Subsection: Error Analysis**
```
We categorize failure cases into:
1. Retrieval failures (18%): Relevant docs not found
2. Generation failures (12%): LLM produces incorrect answer
3. Parsing failures (<1%): Invalid output format

Structured validation eliminates category 3 entirely.
```

#### 7. Discussion (1 page)

**Limitations:**
```
Our approach has limitations:

1. Pattern-based routing: May misclassify edge cases
2. Model-specific: Tuned for Gemini models
3. English-only: Not evaluated on multilingual queries

Future work should explore learned routing policies.
```

**Broader Impact:**
```
Cost reduction enables:
- Wider RAG adoption in cost-sensitive domains
- Sustainable deployment at scale
- Access for resource-constrained organizations
```

#### 8. Conclusion (0.5 page)

```
We introduced smart model routing and structured validation for
production-ready RAG systems. Our approach achieves 58% cost reduction
while maintaining competitive quality, making large-scale deployment
economically viable. Evaluation on standard benchmarks confirms statistical
significance of improvements. Our work demonstrates that intelligent model
selection can bridge the gap between research prototypes and production
systems.

Code and data: [URL]
```

#### 9. References

```
[1] Lewis et al. "Retrieval-Augmented Generation..." (2020)
[2] Guu et al. "REALM..." (2020)
[3] Izacard et al. "Atlas..." (2022)
... [30-50 references total]
```

---

## From Results to Paper

### Using Auto-Generated Materials

Your evaluation scripts generate publication-ready materials:

**1. LaTeX Tables → Copy into Paper**

```latex
% In your paper
\begin{table}[htbp]
\centering
\input{evaluation_results/latex_tables/system_comparison.tex}
\caption{Performance comparison across systems on HotpotQA and Natural Questions benchmarks (n=2,000). All improvements statistically significant (p < 0.01).}
\label{tab:system_comparison}
\end{table}
```

**2. PDF Figures → Include in Paper**

```latex
\begin{figure}[htbp]
\centering
\includegraphics[width=0.8\textwidth]{evaluation_results/figures/system_comparison.pdf}
\caption{Performance comparison showing our system's advantages in both quality and cost.}
\label{fig:comparison}
\end{figure}
```

**3. Results Report → Extract Numbers**

Open `evaluation_results/reports/evaluation_report.txt` and extract:
- Exact metric values
- Statistical significance (p-values)
- Effect sizes (Cohen's d)

Use these numbers in your text:
```
Our system achieves Recall@5 of 0.780, significantly outperforming
Vanilla RAG (0.740, +5.4%, p<0.001, d=0.85).
```

---

## Timeline and Effort

### Path 1: Custom Dataset

**Total Time: 3-6 months**

| Phase | Duration | Effort |
|-------|----------|--------|
| Create dataset (100-200 Q&A) | 1-2 weeks | 20-40 hours |
| Prepare knowledge base | 3-7 days | 10-20 hours |
| Run evaluation | 1 day | 4-8 hours |
| Analyze results | 1 week | 10-15 hours |
| Write paper (8-10 pages) | 3-6 weeks | 60-100 hours |
| Internal review & revision | 2-3 weeks | 20-30 hours |
| Submit to conference | - | - |
| Review period | 2-3 months | - |
| Revisions (if accepted) | 1-2 weeks | 10-20 hours |
| **TOTAL** | **3-6 months** | **130-230 hours** |

### Path 2: Standard Benchmarks

**Total Time: 6-12 months**

| Phase | Duration | Effort |
|-------|----------|--------|
| Download & prepare benchmarks | 1-2 weeks | 15-30 hours |
| Prepare large knowledge base | 2-4 weeks | 30-60 hours |
| Run evaluation (1000s of queries) | 3-7 days | 10-20 hours |
| Analyze results | 2-3 weeks | 30-50 hours |
| Write paper (8-10 pages) | 4-8 weeks | 80-120 hours |
| Internal review & revision | 3-4 weeks | 30-40 hours |
| Submit to conference | - | - |
| Review period | 3-4 months | - |
| Revisions (if accepted) | 2-3 weeks | 20-30 hours |
| **TOTAL** | **6-12 months** | **215-350 hours** |

### Recommended Strategy

**For your first publication:**

1. **Start with Path 1** (custom dataset)
   - Faster time to publication
   - Build evaluation skills
   - Get feedback from reviewers

2. **After acceptance, extend to Path 2**
   - Add benchmark results
   - Submit extended version to journal
   - Higher impact

---

## Quick Start Checklist

Ready to start? Follow this checklist:

### Week 1: Setup
- [ ] Install all dependencies (`pip install -r requirements.txt`)
- [ ] Set GEMINI_API_KEY environment variable
- [ ] Choose Path 1 (custom) or Path 2 (benchmarks)
- [ ] Create `datasets/` and `evaluation_results/` directories

### Week 2-3: Dataset
- [ ] If Path 1: Create 100-200 questions in your domain
- [ ] If Path 1: Write reference answers
- [ ] If Path 2: Run `run_evaluation_benchmarks.py` to download
- [ ] Validate dataset quality (check for typos, unclear questions)

### Week 3-4: Knowledge Base
- [ ] Gather domain documents (PDFs, text files)
- [ ] Upload to RAG system
- [ ] Verify retrieval works (test a few queries manually)

### Week 4: Run Evaluation
- [ ] Run evaluation script (simple or benchmarks)
- [ ] Wait for results (2-12 hours depending on dataset size)
- [ ] Verify output files generated correctly

### Week 5-6: Analyze Results
- [ ] Review `evaluation_report.txt`
- [ ] Check LaTeX tables
- [ ] View PDF figures
- [ ] Identify key findings (improvements, cost savings)

### Week 7-12: Write Paper
- [ ] Draft abstract
- [ ] Write introduction
- [ ] Write related work (review 30-50 papers)
- [ ] Write method section
- [ ] Write experimental setup
- [ ] Write results (use auto-generated tables/figures)
- [ ] Write discussion
- [ ] Write conclusion

### Week 13-14: Review & Revise
- [ ] Internal review (colleagues, advisor)
- [ ] Incorporate feedback
- [ ] Proofread
- [ ] Check formatting

### Week 15: Submit
- [ ] Choose target venue (EMNLP, ACL, etc.)
- [ ] Format according to conference template
- [ ] Submit via conference system
- [ ] Wait for reviews (2-4 months)

---

## Need Help?

**Common Questions:**

**Q: I don't have ground truth answers for my questions. What do I do?**
A: You need to manually write reference answers (or hire annotators). This is unavoidable for research evaluation. Budget 5-10 minutes per question.

**Q: My evaluation is taking too long. How can I speed it up?**
A: Start with a smaller dataset (50 questions) to test. Once working, scale up. Use parallel processing if available.

**Q: What if my system doesn't outperform baselines?**
A: That's okay! Honest negative results are publishable. Focus on cost savings instead: "We achieve comparable quality at 58% lower cost."

**Q: How many questions do I need?**
A: Minimum 50 for a workshop paper, 100-200 for a conference, 500+ for top-tier journal.

**Q: Can I use the auto-generated tables directly?**
A: Yes! They're designed to be publication-ready. Just add captions and cite properly.

---

## Summary

**What "run experiments" means:**
1. Create or download a dataset with questions and answers
2. Run your system and baselines on those questions
3. Compute metrics (accuracy, cost, speed)
4. Generate statistical comparisons

**What "write the narrative" means:**
1. Explain WHY your work matters (the problem)
2. Describe HOW your solution works (the method)
3. Show WHAT improvements you achieved (the results)
4. Discuss IMPACT and limitations (the discussion)

**You already have:**
✅ Complete evaluation framework
✅ Auto-generated tables and figures
✅ Statistical significance tests
✅ Two ready-to-run scripts

**What you need to do:**
1. Choose Path 1 (custom) or Path 2 (benchmarks)
2. Run the appropriate script
3. Wait for results (2-12 hours)
4. Write the paper narrative using generated materials
5. Submit to conference

**You're closer than you think! The infrastructure is ready—just run it and write the story around the results.**

---

**Start now:** `python run_evaluation_simple.py`
