# Evaluation Dashboard Setup Guide

Complete guide for setting up and using the Research Evaluation Dashboard for your Agentic RAG system.

---

## Table of Contents

1. [Overview](#overview)
2. [Database Setup](#database-setup)
3. [Application Setup](#application-setup)
4. [Using the Dashboard](#using-the-dashboard)
5. [Running Evaluations](#running-evaluations)
6. [Exporting Results](#exporting-results)
7. [Troubleshooting](#troubleshooting)

---

## Overview

The Evaluation Dashboard provides a comprehensive web interface for:
- ✅ Viewing evaluation metrics in real-time
- ✅ Comparing your system against baselines
- ✅ Analyzing ablation studies
- ✅ Tracking performance over time
- ✅ Error analysis and categorization
- ✅ Statistical significance testing
- ✅ Exporting LaTeX tables and reports

This dashboard is **separate** from the main analytics dashboard and focuses specifically on **research evaluation** for journal publication.

---

## Database Setup

### Step 1: Create Supabase Tables

The evaluation dashboard stores data in Supabase. You need to run the SQL schema to create the required tables.

**Option A: Using Supabase Dashboard**

1. Log in to your Supabase project dashboard
2. Navigate to **SQL Editor**
3. Open the file `evaluation_db_schema.sql`
4. Copy and paste the entire contents into the SQL editor
5. Click **Run** to execute the schema

**Option B: Using Supabase CLI**

```bash
# If you have Supabase CLI installed
supabase db push evaluation_db_schema.sql
```

### Step 2: Verify Tables Created

Run this query in Supabase SQL Editor to verify:

```sql
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name LIKE 'evaluation%'
OR table_name LIKE '%_analysis'
OR table_name LIKE '%_comparisons'
OR table_name LIKE '%_studies';
```

You should see these tables:
- `evaluation_runs`
- `evaluation_metrics`
- `baseline_comparisons`
- `ablation_studies`
- `statistical_tests`
- `error_analysis`
- `query_type_performance`
- `efficiency_metrics`
- `evaluation_datasets`
- `evaluation_exports`

### Step 3: Set Up Row Level Security (RLS)

The schema automatically enables RLS. Verify policies are created:

```sql
SELECT policyname, tablename, permissive, roles, qual
FROM pg_policies
WHERE tablename LIKE 'evaluation%';
```

---

## Application Setup

### Step 1: Install Dependencies

The evaluation dashboard requires additional Python packages:

```bash
pip install -r requirements.txt
```

Key new dependencies:
- `ragas` - RAG evaluation metrics
- `bert-score` - Semantic similarity
- `scikit-learn`, `scipy`, `statsmodels` - Statistical analysis
- `matplotlib`, `seaborn` - Visualizations

### Step 2: Environment Variables

Ensure these environment variables are set (already required for main app):

```bash
export SUPABASE_URL="your-supabase-url"
export SUPABASE_KEY="your-supabase-anon-key"
export GEMINI_API_KEY="your-gemini-api-key"
```

### Step 3: Verify Integration

The evaluation dashboard is automatically integrated into `app.py` via blueprints.

Check that these lines exist in `app.py`:

```python
from evaluation_routes import evaluation_bp

# ... later in the file ...

app.register_blueprint(evaluation_bp)
```

### Step 4: Start the Application

```bash
python app.py
```

The evaluation dashboard will be available at:
```
http://localhost:5000/evaluation/dashboard
```

---

## Using the Dashboard

### Accessing the Dashboard

1. **Navigate to**: `http://localhost:5000/evaluation/dashboard`
2. **Login**: You must be logged in as an **admin** user
3. **Admin Permission**: Only users with `is_admin: true` in Supabase user metadata can access

### Dashboard Sections

#### 1. **Overview Cards** (Top of Page)
- Overall Score
- RAGAS Score
- IR Metrics Score
- Average Latency

Shows the latest evaluation results at a glance.

#### 2. **Performance Trends** (Line Chart)
- Tracks metrics over time (last 30 days)
- Shows Overall, RAGAS, and IR score trends
- Helps identify improvements or regressions

#### 3. **Tabbed Detailed Views**

**System Comparisons Tab:**
- Bar chart comparing your system vs 5 baselines
- Performance gaps and improvements
- Visual comparison

**Ablation Studies Tab:**
- Component contribution analysis
- Performance drops when removing components
- Helps justify each component's value

**Detailed Metrics Tab:**
- RAGAS metrics (5 metrics)
- IR metrics at different k values (Precision@k, Recall@k, NDCG@k, MRR, MAP)
- Semantic similarity (BERTScore, ROUGE, BLEU)

**Error Analysis Tab:**
- Error distribution by type
- Error severity breakdown
- Example error cases
- Helps identify system weaknesses

**Statistical Tests Tab:**
- p-values for all comparisons
- Cohen's d effect sizes
- Significance markers
- Proves improvements are real

**Efficiency Tab:**
- Latency analysis (avg, median, P95, P99)
- Token usage statistics
- Cost estimates
- Performance vs latency trade-off

#### 4. **Query Type Performance** (Bottom Section)
- Bar chart showing performance by query type
- Identifies which queries your system handles best
- Helps target improvements

#### 5. **Export Actions**
- Export LaTeX tables → For your paper
- Export JSON data → For analysis
- Generate PDF report → Comprehensive report

---

## Running Evaluations

### Option 1: Via Dashboard UI

1. Click **"Run New Evaluation"** button
2. Fill in form:
   - **Experiment Name**: e.g., "Agentic RAG v2.1"
   - **Dataset**: Select evaluation dataset
   - **Options**: Check "Run baselines" and "Run ablations"
3. Click **"Start Evaluation"**
4. Evaluation runs in background
5. Dashboard updates when complete

### Option 2: Via Python Code

```python
from evaluation_framework import EvaluationFramework, EvaluationConfig
from evaluation_db import EvaluationDB
from supabase import create_client

# Initialize
supabase = create_client(supabase_url, supabase_key)
eval_db = EvaluationDB(supabase)

# Create evaluation run
run = eval_db.create_evaluation_run(
    experiment_name="Agentic RAG Evaluation",
    created_by=user_id,
    dataset_name="eval_dataset_v1",
    system_name="Agentic RAG",
    version="2.1"
)

# Configure evaluation
config = EvaluationConfig(
    experiment_name="Agentic RAG Evaluation",
    dataset_path="datasets/eval.json",
    evaluate_baselines=True,
    evaluate_ablations=True,
    compute_ragas=True,
    compute_ir_metrics=True,
    compute_semantic=True,
    compute_significance=True
)

# Run evaluation
framework = EvaluationFramework(config)
results = framework.run_full_evaluation(systems)

# Save results to database
eval_db.update_evaluation_run(
    evaluation_id=run['id'],
    overall_score=results['overall_score'],
    ragas_score=results['ragas_score'],
    ir_score=results['ir_score'],
    semantic_score=results['semantic_score'],
    status='completed'
)

# Save detailed metrics
eval_db.save_evaluation_metrics(run['id'], results['metrics'])

# Save baseline comparisons
for baseline in results['baselines']:
    eval_db.save_baseline_comparison(
        run['id'],
        baseline['name'],
        baseline['score'],
        results['overall_score'],
        baseline['metrics']
    )

# Save ablation results
for ablation in results['ablations']:
    eval_db.save_ablation_result(
        run['id'],
        ablation['name'],
        ablation['components_removed'],
        ablation['score'],
        results['overall_score'],
        ablation['metrics']
    )
```

### Option 3: Command Line Script

Create a script `run_evaluation.py`:

```python
#!/usr/bin/env python3
import os
import sys
from evaluation_framework import EvaluationFramework, EvaluationConfig
from evaluation_db import EvaluationDB
from supabase import create_client

def main():
    # Get environment variables
    supabase_url = os.environ.get('SUPABASE_URL')
    supabase_key = os.environ.get('SUPABASE_KEY')

    if not supabase_url or not supabase_key:
        print("Error: SUPABASE_URL and SUPABASE_KEY must be set")
        sys.exit(1)

    # Initialize
    supabase = create_client(supabase_url, supabase_key)
    eval_db = EvaluationDB(supabase)

    # Create evaluation run
    run = eval_db.create_evaluation_run(
        experiment_name=sys.argv[1] if len(sys.argv) > 1 else "Evaluation",
        created_by="admin",
        dataset_name="eval_dataset_v1"
    )

    print(f"Starting evaluation: {run['id']}")

    # Configure and run
    config = EvaluationConfig(
        experiment_name=run['experiment_name'],
        dataset_path="datasets/eval.json",
        evaluate_baselines=True,
        evaluate_ablations=True,
        compute_ragas=True,
        compute_ir_metrics=True,
        compute_semantic=True
    )

    framework = EvaluationFramework(config)

    # TODO: Provide your systems to evaluate
    systems = {
        'Agentic RAG': your_system_here
    }

    results = framework.run_full_evaluation(systems)

    # Save to database
    eval_db.update_evaluation_run(
        evaluation_id=run['id'],
        overall_score=results['overall_score'],
        status='completed'
    )

    print(f"Evaluation complete! View at: http://localhost:5000/evaluation/dashboard")

if __name__ == '__main__':
    main()
```

Run it:
```bash
python run_evaluation.py "My Experiment Name"
```

---

## Exporting Results

### LaTeX Tables

1. Go to evaluation dashboard
2. Scroll to **"Export Results"** section
3. Click **"Export LaTeX Tables"**
4. Download `.tex` file
5. Include in your paper:

```latex
\input{system_comparison.tex}
```

### JSON Data

1. Click **"Export JSON Data"**
2. Downloads complete evaluation data
3. Use for further analysis or backup

### PDF Report

**Coming soon**: One-click PDF generation with all figures and tables.

---

## API Endpoints

The dashboard provides these API endpoints:

### GET Endpoints

```
GET /evaluation/api/stats
    → Dashboard statistics

GET /evaluation/api/recent?limit=10
    → Recent evaluations

GET /evaluation/api/trends?days=30
    → Performance trends

GET /evaluation/api/runs/<evaluation_id>
    → Complete evaluation details

GET /evaluation/api/runs/<evaluation_id>/baselines
    → Baseline comparisons

GET /evaluation/api/runs/<evaluation_id>/ablations
    → Ablation study results

GET /evaluation/api/runs/<evaluation_id>/errors
    → Error analysis

GET /evaluation/api/runs/<evaluation_id>/query-types
    → Query type performance

GET /evaluation/api/runs/<evaluation_id>/efficiency
    → Efficiency metrics

GET /evaluation/api/runs/<evaluation_id>/statistical-tests
    → Statistical significance tests
```

### POST Endpoints

```
POST /evaluation/api/run
    → Start new evaluation
    Body: {
        "experiment_name": "...",
        "dataset_name": "...",
        "metadata": {...}
    }
```

### Export Endpoints

```
GET /evaluation/api/runs/<evaluation_id>/export/latex
    → Download LaTeX tables

GET /evaluation/api/runs/<evaluation_id>/export/json
    → Download JSON data
```

### DELETE Endpoints

```
DELETE /evaluation/api/runs/<evaluation_id>
    → Delete evaluation (admin only)
```

---

## Troubleshooting

### Dashboard shows "Database not configured"

**Solution**: Ensure Supabase client is initialized:
- Check `SUPABASE_URL` and `SUPABASE_KEY` environment variables
- Verify Supabase client initialization in `app.py`

### "Admin access required" error

**Solution**: Make sure your user has admin permissions:

```sql
-- In Supabase SQL Editor
UPDATE auth.users
SET raw_user_meta_data = jsonb_set(
    COALESCE(raw_user_meta_data, '{}'::jsonb),
    '{is_admin}',
    'true'::jsonb
)
WHERE email = 'your-admin-email@example.com';
```

### Tables not found

**Solution**: Run the database schema:
1. Open `evaluation_db_schema.sql`
2. Execute in Supabase SQL Editor
3. Verify tables created

### No data showing in dashboard

**Solution**:
1. Run at least one evaluation first
2. Check browser console for errors
3. Verify API endpoints return data:
   ```bash
   curl http://localhost:5000/evaluation/api/stats
   ```

### Charts not rendering

**Solution**:
- Ensure Chart.js is loading (check browser console)
- Verify data format from API
- Check for JavaScript errors

### Import errors when starting app

**Solution**:
```bash
# Reinstall dependencies
pip install -r requirements.txt

# Verify imports
python -c "import ragas; import bert_score; print('OK')"
```

---

## Best Practices

### 1. Regular Evaluations
- Run evaluations after each major change
- Track performance trends over time
- Compare versions systematically

### 2. Dataset Management
- Create well-documented evaluation datasets
- Include 100+ questions for statistical validity
- Update datasets as system capabilities grow

### 3. Baseline Comparisons
- Always compare against multiple baselines
- Include both simple and sophisticated baselines
- Document baseline configurations

### 4. Statistical Rigor
- Always check p-values < 0.05
- Report effect sizes (Cohen's d)
- Use Bonferroni correction for multiple comparisons

### 5. Error Analysis
- Regularly review error cases
- Categorize failure patterns
- Use insights to improve system

### 6. Documentation
- Document each evaluation run
- Include experiment notes in metadata
- Keep track of system versions

---

## Integration with Research Workflow

### For Journal Papers

1. **Run comprehensive evaluation**:
   - All baselines
   - All ablations
   - Statistical tests
   - Error analysis

2. **Export results**:
   - LaTeX tables → Direct inclusion in paper
   - Figures → Convert to EPS/PDF for journals
   - JSON data → For reviewers

3. **Include in paper**:
   ```latex
   \section{Evaluation}

   \subsection{Overall Performance}
   Table~\ref{tab:system_comparison} shows...
   \input{tables/system_comparison.tex}

   \subsection{Ablation Study}
   Table~\ref{tab:ablation} demonstrates...
   \input{tables/ablation_table.tex}
   ```

4. **Respond to reviewers**:
   - Have detailed data ready
   - Can re-run evaluations with reviewer suggestions
   - Export updated results

---

## Support

For issues or questions:
1. Check this documentation
2. Review API endpoint responses for errors
3. Check browser console for JavaScript errors
4. Verify database schema is up to date

---

**🎯 The evaluation dashboard is designed to streamline your research evaluation workflow and provide publication-ready outputs!**
