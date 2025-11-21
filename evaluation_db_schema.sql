-- Database Schema for Research Evaluation Dashboard
-- ===================================================
-- Supabase SQL schema for storing evaluation results

-- Table 1: Evaluation Runs
CREATE TABLE IF NOT EXISTS evaluation_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    experiment_name TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES auth.users(id),

    -- Configuration
    dataset_name TEXT,
    dataset_size INTEGER,

    -- Overall Results
    overall_score DECIMAL(5,4),
    ragas_score DECIMAL(5,4),
    ir_score DECIMAL(5,4),
    semantic_score DECIMAL(5,4),

    -- System Info
    system_name TEXT DEFAULT 'Agentic RAG',
    version TEXT,

    -- Status
    status TEXT DEFAULT 'completed', -- running, completed, failed
    duration_seconds INTEGER,

    -- Metadata
    metadata JSONB,

    created_at_idx TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_evaluation_runs_created_at ON evaluation_runs(created_at DESC);
CREATE INDEX idx_evaluation_runs_created_by ON evaluation_runs(created_by);
CREATE INDEX idx_evaluation_runs_status ON evaluation_runs(status);


-- Table 2: Detailed Metrics
CREATE TABLE IF NOT EXISTS evaluation_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    evaluation_id UUID REFERENCES evaluation_runs(id) ON DELETE CASCADE,

    -- RAGAS Metrics
    ragas_faithfulness DECIMAL(5,4),
    ragas_answer_relevancy DECIMAL(5,4),
    ragas_context_precision DECIMAL(5,4),
    ragas_context_recall DECIMAL(5,4),
    ragas_context_relevancy DECIMAL(5,4),

    -- IR Metrics at different k values
    precision_at_1 DECIMAL(5,4),
    precision_at_3 DECIMAL(5,4),
    precision_at_5 DECIMAL(5,4),
    precision_at_10 DECIMAL(5,4),
    precision_at_20 DECIMAL(5,4),

    recall_at_1 DECIMAL(5,4),
    recall_at_3 DECIMAL(5,4),
    recall_at_5 DECIMAL(5,4),
    recall_at_10 DECIMAL(5,4),
    recall_at_20 DECIMAL(5,4),

    ndcg_at_1 DECIMAL(5,4),
    ndcg_at_3 DECIMAL(5,4),
    ndcg_at_5 DECIMAL(5,4),
    ndcg_at_10 DECIMAL(5,4),
    ndcg_at_20 DECIMAL(5,4),

    mrr DECIMAL(5,4),
    map_score DECIMAL(5,4),

    f1_at_1 DECIMAL(5,4),
    f1_at_3 DECIMAL(5,4),
    f1_at_5 DECIMAL(5,4),
    f1_at_10 DECIMAL(5,4),
    f1_at_20 DECIMAL(5,4),

    -- Semantic Similarity Metrics
    bertscore_precision DECIMAL(5,4),
    bertscore_recall DECIMAL(5,4),
    bertscore_f1 DECIMAL(5,4),

    rouge_l_precision DECIMAL(5,4),
    rouge_l_recall DECIMAL(5,4),
    rouge_l_f1 DECIMAL(5,4),

    bleu_1 DECIMAL(5,4),
    bleu_2 DECIMAL(5,4),
    bleu_3 DECIMAL(5,4),
    bleu_4 DECIMAL(5,4),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_evaluation_metrics_eval_id ON evaluation_metrics(evaluation_id);


-- Table 3: Baseline Comparisons
CREATE TABLE IF NOT EXISTS baseline_comparisons (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    evaluation_id UUID REFERENCES evaluation_runs(id) ON DELETE CASCADE,

    baseline_name TEXT NOT NULL,
    baseline_score DECIMAL(5,4),

    -- Detailed metrics for baseline
    metrics JSONB,

    -- Performance gap
    performance_gap DECIMAL(5,4), -- main_system_score - baseline_score
    relative_improvement DECIMAL(5,2), -- percentage

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_baseline_comparisons_eval_id ON baseline_comparisons(evaluation_id);


-- Table 4: Ablation Studies
CREATE TABLE IF NOT EXISTS ablation_studies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    evaluation_id UUID REFERENCES evaluation_runs(id) ON DELETE CASCADE,

    configuration_name TEXT NOT NULL,
    components_removed TEXT[], -- Array of component names

    score DECIMAL(5,4),
    performance_drop DECIMAL(5,4), -- full_system_score - ablation_score
    relative_drop_percent DECIMAL(5,2),

    -- Detailed metrics
    metrics JSONB,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_ablation_studies_eval_id ON ablation_studies(evaluation_id);


-- Table 5: Statistical Significance Tests
CREATE TABLE IF NOT EXISTS statistical_tests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    evaluation_id UUID REFERENCES evaluation_runs(id) ON DELETE CASCADE,

    system_a TEXT NOT NULL,
    system_b TEXT NOT NULL,

    test_name TEXT, -- 'paired_t_test', 'wilcoxon', etc.
    statistic DECIMAL(10,4),
    p_value DECIMAL(10,8),
    is_significant BOOLEAN,
    alpha DECIMAL(3,2) DEFAULT 0.05,

    -- Effect size
    effect_size DECIMAL(5,4), -- Cohen's d
    effect_size_interpretation TEXT, -- 'small', 'medium', 'large'

    -- Confidence interval
    ci_lower DECIMAL(5,4),
    ci_upper DECIMAL(5,4),
    confidence_level DECIMAL(3,2) DEFAULT 0.95,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_statistical_tests_eval_id ON statistical_tests(evaluation_id);


-- Table 6: Error Analysis
CREATE TABLE IF NOT EXISTS error_analysis (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    evaluation_id UUID REFERENCES evaluation_runs(id) ON DELETE CASCADE,

    query_id TEXT,
    question TEXT,
    ground_truth TEXT,
    predicted_answer TEXT,

    error_type TEXT, -- 'hallucination', 'poor_retrieval', 'incomplete_answer', etc.
    error_severity TEXT, -- 'low', 'medium', 'high'

    score DECIMAL(5,4),

    retrieved_contexts JSONB,
    scores JSONB, -- All individual metric scores

    metadata JSONB,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_error_analysis_eval_id ON error_analysis(evaluation_id);
CREATE INDEX idx_error_analysis_error_type ON error_analysis(error_type);
CREATE INDEX idx_error_analysis_severity ON error_analysis(error_severity);


-- Table 7: Query Type Performance
CREATE TABLE IF NOT EXISTS query_type_performance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    evaluation_id UUID REFERENCES evaluation_runs(id) ON DELETE CASCADE,

    query_type TEXT NOT NULL, -- 'FACTUAL', 'ANALYTICAL', 'COMPARATIVE', 'TEMPORAL', 'PROCEDURAL'

    total_queries INTEGER,
    avg_score DECIMAL(5,4),

    -- Metrics breakdown
    metrics JSONB,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_query_type_performance_eval_id ON query_type_performance(evaluation_id);


-- Table 8: Efficiency Metrics
CREATE TABLE IF NOT EXISTS efficiency_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    evaluation_id UUID REFERENCES evaluation_runs(id) ON DELETE CASCADE,

    avg_latency_ms DECIMAL(10,2),
    median_latency_ms DECIMAL(10,2),
    p95_latency_ms DECIMAL(10,2),
    p99_latency_ms DECIMAL(10,2),

    avg_tokens_used INTEGER,
    total_tokens_used INTEGER,

    estimated_cost_usd DECIMAL(10,4),

    -- Latency breakdown
    latency_distribution JSONB,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_efficiency_metrics_eval_id ON efficiency_metrics(evaluation_id);


-- Table 9: Evaluation Datasets
CREATE TABLE IF NOT EXISTS evaluation_datasets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    version TEXT DEFAULT '1.0',

    created_by UUID REFERENCES auth.users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Dataset statistics
    total_items INTEGER,
    query_type_distribution JSONB,
    difficulty_distribution JSONB,
    domain_distribution JSONB,

    -- Dataset file path or URL
    file_path TEXT,

    -- Metadata
    metadata JSONB,

    is_active BOOLEAN DEFAULT TRUE
);

CREATE INDEX idx_evaluation_datasets_name ON evaluation_datasets(name);
CREATE INDEX idx_evaluation_datasets_created_by ON evaluation_datasets(created_by);


-- Table 10: Export History
CREATE TABLE IF NOT EXISTS evaluation_exports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    evaluation_id UUID REFERENCES evaluation_runs(id) ON DELETE CASCADE,

    export_type TEXT NOT NULL, -- 'latex', 'pdf', 'json', 'csv'
    export_name TEXT,

    file_path TEXT,
    file_size INTEGER,

    exported_by UUID REFERENCES auth.users(id),
    exported_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_evaluation_exports_eval_id ON evaluation_exports(evaluation_id);


-- Row Level Security (RLS) Policies
-- ===================================

-- Enable RLS
ALTER TABLE evaluation_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE evaluation_metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE baseline_comparisons ENABLE ROW LEVEL SECURITY;
ALTER TABLE ablation_studies ENABLE ROW LEVEL SECURITY;
ALTER TABLE statistical_tests ENABLE ROW LEVEL SECURITY;
ALTER TABLE error_analysis ENABLE ROW LEVEL SECURITY;
ALTER TABLE query_type_performance ENABLE ROW LEVEL SECURITY;
ALTER TABLE efficiency_metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE evaluation_datasets ENABLE ROW LEVEL SECURITY;
ALTER TABLE evaluation_exports ENABLE ROW LEVEL SECURITY;

-- Policies: Users can view all evaluation data (read-only for most users)
CREATE POLICY "Users can view evaluation runs" ON evaluation_runs
    FOR SELECT USING (true);

CREATE POLICY "Users can view evaluation metrics" ON evaluation_metrics
    FOR SELECT USING (true);

CREATE POLICY "Users can view baseline comparisons" ON baseline_comparisons
    FOR SELECT USING (true);

CREATE POLICY "Users can view ablation studies" ON ablation_studies
    FOR SELECT USING (true);

CREATE POLICY "Users can view statistical tests" ON statistical_tests
    FOR SELECT USING (true);

CREATE POLICY "Users can view error analysis" ON error_analysis
    FOR SELECT USING (true);

CREATE POLICY "Users can view query type performance" ON query_type_performance
    FOR SELECT USING (true);

CREATE POLICY "Users can view efficiency metrics" ON efficiency_metrics
    FOR SELECT USING (true);

CREATE POLICY "Users can view evaluation datasets" ON evaluation_datasets
    FOR SELECT USING (true);

CREATE POLICY "Users can view evaluation exports" ON evaluation_exports
    FOR SELECT USING (true);

-- Policies: Only admins can insert/update/delete (check user metadata for is_admin = true)
CREATE POLICY "Admins can insert evaluation runs" ON evaluation_runs
    FOR INSERT WITH CHECK (
        auth.uid() IN (
            SELECT id FROM auth.users WHERE raw_user_meta_data->>'is_admin' = 'true'
        )
    );

CREATE POLICY "Admins can update evaluation runs" ON evaluation_runs
    FOR UPDATE USING (
        auth.uid() IN (
            SELECT id FROM auth.users WHERE raw_user_meta_data->>'is_admin' = 'true'
        )
    );

CREATE POLICY "Admins can delete evaluation runs" ON evaluation_runs
    FOR DELETE USING (
        auth.uid() IN (
            SELECT id FROM auth.users WHERE raw_user_meta_data->>'is_admin' = 'true'
        )
    );

-- Similar policies for other tables (admins only for write operations)
CREATE POLICY "Admins can manage evaluation metrics" ON evaluation_metrics
    FOR ALL USING (
        auth.uid() IN (
            SELECT id FROM auth.users WHERE raw_user_meta_data->>'is_admin' = 'true'
        )
    );

CREATE POLICY "Admins can manage datasets" ON evaluation_datasets
    FOR ALL USING (
        auth.uid() IN (
            SELECT id FROM auth.users WHERE raw_user_meta_data->>'is_admin' = 'true'
        )
    );


-- Views for easier querying
-- ==========================

-- View: Latest evaluation summary
CREATE OR REPLACE VIEW latest_evaluation_summary AS
SELECT
    er.id,
    er.experiment_name,
    er.created_at,
    er.overall_score,
    er.ragas_score,
    er.ir_score,
    er.semantic_score,
    er.status,
    er.duration_seconds,
    COUNT(DISTINCT bc.id) as baseline_count,
    COUNT(DISTINCT as2.id) as ablation_count,
    COUNT(DISTINCT ea.id) as error_count
FROM evaluation_runs er
LEFT JOIN baseline_comparisons bc ON er.id = bc.evaluation_id
LEFT JOIN ablation_studies as2 ON er.id = as2.evaluation_id
LEFT JOIN error_analysis ea ON er.id = ea.evaluation_id
GROUP BY er.id
ORDER BY er.created_at DESC;


-- View: Performance trends over time
CREATE OR REPLACE VIEW performance_trends AS
SELECT
    DATE(created_at) as evaluation_date,
    AVG(overall_score) as avg_overall_score,
    AVG(ragas_score) as avg_ragas_score,
    AVG(ir_score) as avg_ir_score,
    AVG(semantic_score) as avg_semantic_score,
    COUNT(*) as evaluation_count
FROM evaluation_runs
WHERE status = 'completed'
GROUP BY DATE(created_at)
ORDER BY evaluation_date DESC;


-- Functions for analytics
-- ========================

-- Function: Get latest evaluation ID
CREATE OR REPLACE FUNCTION get_latest_evaluation_id()
RETURNS UUID AS $$
    SELECT id FROM evaluation_runs
    WHERE status = 'completed'
    ORDER BY created_at DESC
    LIMIT 1;
$$ LANGUAGE SQL;


-- Function: Calculate performance improvement over time
CREATE OR REPLACE FUNCTION calculate_performance_improvement(days INTEGER DEFAULT 30)
RETURNS TABLE(
    metric_name TEXT,
    current_score DECIMAL,
    previous_score DECIMAL,
    improvement DECIMAL,
    improvement_percent DECIMAL
) AS $$
BEGIN
    RETURN QUERY
    WITH current_period AS (
        SELECT
            AVG(overall_score) as overall,
            AVG(ragas_score) as ragas,
            AVG(ir_score) as ir,
            AVG(semantic_score) as semantic
        FROM evaluation_runs
        WHERE created_at >= NOW() - INTERVAL '1 day' * days
        AND status = 'completed'
    ),
    previous_period AS (
        SELECT
            AVG(overall_score) as overall,
            AVG(ragas_score) as ragas,
            AVG(ir_score) as ir,
            AVG(semantic_score) as semantic
        FROM evaluation_runs
        WHERE created_at >= NOW() - INTERVAL '1 day' * (days * 2)
        AND created_at < NOW() - INTERVAL '1 day' * days
        AND status = 'completed'
    )
    SELECT
        'Overall'::TEXT,
        cp.overall,
        pp.overall,
        cp.overall - pp.overall,
        ((cp.overall - pp.overall) / NULLIF(pp.overall, 0) * 100)
    FROM current_period cp, previous_period pp
    UNION ALL
    SELECT
        'RAGAS'::TEXT,
        cp.ragas,
        pp.ragas,
        cp.ragas - pp.ragas,
        ((cp.ragas - pp.ragas) / NULLIF(pp.ragas, 0) * 100)
    FROM current_period cp, previous_period pp
    UNION ALL
    SELECT
        'IR Metrics'::TEXT,
        cp.ir,
        pp.ir,
        cp.ir - pp.ir,
        ((cp.ir - pp.ir) / NULLIF(pp.ir, 0) * 100)
    FROM current_period cp, previous_period pp
    UNION ALL
    SELECT
        'Semantic'::TEXT,
        cp.semantic,
        pp.semantic,
        cp.semantic - pp.semantic,
        ((cp.semantic - pp.semantic) / NULLIF(pp.semantic, 0) * 100)
    FROM current_period cp, previous_period pp;
END;
$$ LANGUAGE plpgsql;


-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_evaluation_runs_created_at_status ON evaluation_runs(created_at DESC, status);
CREATE INDEX IF NOT EXISTS idx_error_analysis_eval_type ON error_analysis(evaluation_id, error_type);

-- Comments for documentation
COMMENT ON TABLE evaluation_runs IS 'Stores metadata and summary results for each evaluation run';
COMMENT ON TABLE evaluation_metrics IS 'Detailed metrics for each evaluation including RAGAS, IR, and semantic scores';
COMMENT ON TABLE baseline_comparisons IS 'Comparison results between main system and baseline systems';
COMMENT ON TABLE ablation_studies IS 'Results from ablation studies showing component contributions';
COMMENT ON TABLE statistical_tests IS 'Statistical significance test results for system comparisons';
COMMENT ON TABLE error_analysis IS 'Detailed error case analysis including failure patterns';
COMMENT ON TABLE query_type_performance IS 'Performance breakdown by query type';
COMMENT ON TABLE efficiency_metrics IS 'Latency, token usage, and cost metrics';
COMMENT ON TABLE evaluation_datasets IS 'Metadata about evaluation datasets used';
COMMENT ON TABLE evaluation_exports IS 'History of exported LaTeX tables and PDF reports';
