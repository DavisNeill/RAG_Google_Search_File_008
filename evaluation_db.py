"""
Evaluation Database Interface
==============================

Python interface for storing and retrieving evaluation results from Supabase.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import json


class EvaluationDB:
    """Database interface for evaluation results"""

    def __init__(self, supabase_client):
        """
        Initialize with Supabase client

        Args:
            supabase_client: Supabase client instance
        """
        self.client = supabase_client

    # ==================== Evaluation Runs ====================

    def create_evaluation_run(
        self,
        experiment_name: str,
        created_by: str,
        dataset_name: str = None,
        dataset_size: int = 0,
        system_name: str = "Agentic RAG",
        version: str = None,
        metadata: Dict = None
    ) -> Dict:
        """
        Create a new evaluation run

        Returns:
            Created evaluation run record with ID
        """
        data = {
            'experiment_name': experiment_name,
            'created_by': created_by,
            'dataset_name': dataset_name,
            'dataset_size': dataset_size,
            'system_name': system_name,
            'version': version,
            'status': 'running',
            'metadata': metadata or {}
        }

        result = self.client.table('evaluation_runs').insert(data).execute()
        return result.data[0] if result.data else None

    def update_evaluation_run(
        self,
        evaluation_id: str,
        overall_score: float = None,
        ragas_score: float = None,
        ir_score: float = None,
        semantic_score: float = None,
        status: str = None,
        duration_seconds: int = None
    ) -> Dict:
        """Update evaluation run with results"""
        data = {}
        if overall_score is not None:
            data['overall_score'] = overall_score
        if ragas_score is not None:
            data['ragas_score'] = ragas_score
        if ir_score is not None:
            data['ir_score'] = ir_score
        if semantic_score is not None:
            data['semantic_score'] = semantic_score
        if status is not None:
            data['status'] = status
        if duration_seconds is not None:
            data['duration_seconds'] = duration_seconds

        result = self.client.table('evaluation_runs')\
            .update(data)\
            .eq('id', evaluation_id)\
            .execute()

        return result.data[0] if result.data else None

    def get_evaluation_run(self, evaluation_id: str) -> Dict:
        """Get evaluation run by ID"""
        result = self.client.table('evaluation_runs')\
            .select('*')\
            .eq('id', evaluation_id)\
            .single()\
            .execute()

        return result.data if result.data else None

    def get_recent_evaluations(self, limit: int = 10) -> List[Dict]:
        """Get recent evaluation runs"""
        result = self.client.table('evaluation_runs')\
            .select('*')\
            .order('created_at', desc=True)\
            .limit(limit)\
            .execute()

        return result.data if result.data else []

    def get_evaluation_summary(self) -> Dict:
        """Get overall evaluation summary"""
        result = self.client.table('latest_evaluation_summary')\
            .select('*')\
            .execute()

        return result.data if result.data else []

    # ==================== Detailed Metrics ====================

    def save_evaluation_metrics(
        self,
        evaluation_id: str,
        metrics: Dict[str, float]
    ) -> Dict:
        """Save detailed metrics for an evaluation"""
        data = {'evaluation_id': evaluation_id}
        data.update(metrics)

        result = self.client.table('evaluation_metrics')\
            .insert(data)\
            .execute()

        return result.data[0] if result.data else None

    def get_evaluation_metrics(self, evaluation_id: str) -> Dict:
        """Get detailed metrics for an evaluation"""
        result = self.client.table('evaluation_metrics')\
            .select('*')\
            .eq('evaluation_id', evaluation_id)\
            .single()\
            .execute()

        return result.data if result.data else None

    # ==================== Baseline Comparisons ====================

    def save_baseline_comparison(
        self,
        evaluation_id: str,
        baseline_name: str,
        baseline_score: float,
        main_system_score: float,
        metrics: Dict = None
    ) -> Dict:
        """Save baseline comparison results"""
        performance_gap = main_system_score - baseline_score
        relative_improvement = (performance_gap / baseline_score * 100) if baseline_score > 0 else 0

        data = {
            'evaluation_id': evaluation_id,
            'baseline_name': baseline_name,
            'baseline_score': baseline_score,
            'performance_gap': performance_gap,
            'relative_improvement': relative_improvement,
            'metrics': metrics or {}
        }

        result = self.client.table('baseline_comparisons')\
            .insert(data)\
            .execute()

        return result.data[0] if result.data else None

    def get_baseline_comparisons(self, evaluation_id: str) -> List[Dict]:
        """Get all baseline comparisons for an evaluation"""
        result = self.client.table('baseline_comparisons')\
            .select('*')\
            .eq('evaluation_id', evaluation_id)\
            .order('performance_gap', desc=True)\
            .execute()

        return result.data if result.data else []

    # ==================== Ablation Studies ====================

    def save_ablation_result(
        self,
        evaluation_id: str,
        configuration_name: str,
        components_removed: List[str],
        score: float,
        full_system_score: float,
        metrics: Dict = None
    ) -> Dict:
        """Save ablation study results"""
        performance_drop = full_system_score - score
        relative_drop = (performance_drop / full_system_score * 100) if full_system_score > 0 else 0

        data = {
            'evaluation_id': evaluation_id,
            'configuration_name': configuration_name,
            'components_removed': components_removed,
            'score': score,
            'performance_drop': performance_drop,
            'relative_drop_percent': relative_drop,
            'metrics': metrics or {}
        }

        result = self.client.table('ablation_studies')\
            .insert(data)\
            .execute()

        return result.data[0] if result.data else None

    def get_ablation_results(self, evaluation_id: str) -> List[Dict]:
        """Get all ablation results for an evaluation"""
        result = self.client.table('ablation_studies')\
            .select('*')\
            .eq('evaluation_id', evaluation_id)\
            .order('performance_drop', desc=True)\
            .execute()

        return result.data if result.data else []

    # ==================== Statistical Tests ====================

    def save_statistical_test(
        self,
        evaluation_id: str,
        system_a: str,
        system_b: str,
        test_name: str,
        statistic: float,
        p_value: float,
        is_significant: bool,
        effect_size: float = None,
        ci_lower: float = None,
        ci_upper: float = None,
        alpha: float = 0.05
    ) -> Dict:
        """Save statistical test results"""
        # Interpret effect size
        effect_interpretation = None
        if effect_size is not None:
            abs_effect = abs(effect_size)
            if abs_effect < 0.2:
                effect_interpretation = 'negligible'
            elif abs_effect < 0.5:
                effect_interpretation = 'small'
            elif abs_effect < 0.8:
                effect_interpretation = 'medium'
            else:
                effect_interpretation = 'large'

        data = {
            'evaluation_id': evaluation_id,
            'system_a': system_a,
            'system_b': system_b,
            'test_name': test_name,
            'statistic': statistic,
            'p_value': p_value,
            'is_significant': is_significant,
            'effect_size': effect_size,
            'effect_size_interpretation': effect_interpretation,
            'ci_lower': ci_lower,
            'ci_upper': ci_upper,
            'alpha': alpha
        }

        result = self.client.table('statistical_tests')\
            .insert(data)\
            .execute()

        return result.data[0] if result.data else None

    def get_statistical_tests(self, evaluation_id: str) -> List[Dict]:
        """Get all statistical tests for an evaluation"""
        result = self.client.table('statistical_tests')\
            .select('*')\
            .eq('evaluation_id', evaluation_id)\
            .execute()

        return result.data if result.data else []

    # ==================== Error Analysis ====================

    def save_error_case(
        self,
        evaluation_id: str,
        query_id: str,
        question: str,
        ground_truth: str,
        predicted_answer: str,
        error_type: str,
        error_severity: str,
        score: float,
        retrieved_contexts: List[str] = None,
        scores: Dict = None,
        metadata: Dict = None
    ) -> Dict:
        """Save error case"""
        data = {
            'evaluation_id': evaluation_id,
            'query_id': query_id,
            'question': question,
            'ground_truth': ground_truth,
            'predicted_answer': predicted_answer,
            'error_type': error_type,
            'error_severity': error_severity,
            'score': score,
            'retrieved_contexts': retrieved_contexts or [],
            'scores': scores or {},
            'metadata': metadata or {}
        }

        result = self.client.table('error_analysis')\
            .insert(data)\
            .execute()

        return result.data[0] if result.data else None

    def get_error_cases(
        self,
        evaluation_id: str,
        error_type: str = None,
        error_severity: str = None
    ) -> List[Dict]:
        """Get error cases with optional filtering"""
        query = self.client.table('error_analysis')\
            .select('*')\
            .eq('evaluation_id', evaluation_id)

        if error_type:
            query = query.eq('error_type', error_type)
        if error_severity:
            query = query.eq('error_severity', error_severity)

        result = query.execute()
        return result.data if result.data else []

    def get_error_summary(self, evaluation_id: str) -> Dict:
        """Get error summary statistics"""
        errors = self.get_error_cases(evaluation_id)

        summary = {
            'total_errors': len(errors),
            'by_type': {},
            'by_severity': {}
        }

        for error in errors:
            # Count by type
            error_type = error.get('error_type', 'unknown')
            summary['by_type'][error_type] = summary['by_type'].get(error_type, 0) + 1

            # Count by severity
            severity = error.get('error_severity', 'unknown')
            summary['by_severity'][severity] = summary['by_severity'].get(severity, 0) + 1

        return summary

    # ==================== Query Type Performance ====================

    def save_query_type_performance(
        self,
        evaluation_id: str,
        query_type: str,
        total_queries: int,
        avg_score: float,
        metrics: Dict = None
    ) -> Dict:
        """Save query type performance"""
        data = {
            'evaluation_id': evaluation_id,
            'query_type': query_type,
            'total_queries': total_queries,
            'avg_score': avg_score,
            'metrics': metrics or {}
        }

        result = self.client.table('query_type_performance')\
            .insert(data)\
            .execute()

        return result.data[0] if result.data else None

    def get_query_type_performance(self, evaluation_id: str) -> List[Dict]:
        """Get query type performance breakdown"""
        result = self.client.table('query_type_performance')\
            .select('*')\
            .eq('evaluation_id', evaluation_id)\
            .order('avg_score', desc=True)\
            .execute()

        return result.data if result.data else []

    # ==================== Efficiency Metrics ====================

    def save_efficiency_metrics(
        self,
        evaluation_id: str,
        avg_latency_ms: float,
        median_latency_ms: float = None,
        p95_latency_ms: float = None,
        p99_latency_ms: float = None,
        avg_tokens_used: int = None,
        total_tokens_used: int = None,
        estimated_cost_usd: float = None,
        latency_distribution: Dict = None
    ) -> Dict:
        """Save efficiency metrics"""
        data = {
            'evaluation_id': evaluation_id,
            'avg_latency_ms': avg_latency_ms,
            'median_latency_ms': median_latency_ms,
            'p95_latency_ms': p95_latency_ms,
            'p99_latency_ms': p99_latency_ms,
            'avg_tokens_used': avg_tokens_used,
            'total_tokens_used': total_tokens_used,
            'estimated_cost_usd': estimated_cost_usd,
            'latency_distribution': latency_distribution or {}
        }

        result = self.client.table('efficiency_metrics')\
            .insert(data)\
            .execute()

        return result.data[0] if result.data else None

    def get_efficiency_metrics(self, evaluation_id: str) -> Dict:
        """Get efficiency metrics"""
        result = self.client.table('efficiency_metrics')\
            .select('*')\
            .eq('evaluation_id', evaluation_id)\
            .single()\
            .execute()

        return result.data if result.data else None

    # ==================== Performance Trends ====================

    def get_performance_trends(self, days: int = 30) -> List[Dict]:
        """Get performance trends over time"""
        result = self.client.table('performance_trends')\
            .select('*')\
            .limit(days)\
            .execute()

        return result.data if result.data else []

    def get_performance_improvement(self, days: int = 30) -> List[Dict]:
        """Calculate performance improvement"""
        result = self.client.rpc('calculate_performance_improvement', {'days': days}).execute()
        return result.data if result.data else []

    # ==================== Exports ====================

    def save_export(
        self,
        evaluation_id: str,
        export_type: str,
        export_name: str,
        file_path: str,
        file_size: int,
        exported_by: str
    ) -> Dict:
        """Save export history"""
        data = {
            'evaluation_id': evaluation_id,
            'export_type': export_type,
            'export_name': export_name,
            'file_path': file_path,
            'file_size': file_size,
            'exported_by': exported_by
        }

        result = self.client.table('evaluation_exports')\
            .insert(data)\
            .execute()

        return result.data[0] if result.data else None

    def get_exports(self, evaluation_id: str) -> List[Dict]:
        """Get export history for evaluation"""
        result = self.client.table('evaluation_exports')\
            .select('*')\
            .eq('evaluation_id', evaluation_id)\
            .order('exported_at', desc=True)\
            .execute()

        return result.data if result.data else []

    # ==================== Dashboard Analytics ====================

    def get_dashboard_stats(self) -> Dict:
        """Get overall dashboard statistics"""
        # Get total evaluations
        total_evals = self.client.table('evaluation_runs')\
            .select('id', count='exact')\
            .execute()

        # Get latest evaluation
        latest_eval = self.client.table('evaluation_runs')\
            .select('*')\
            .order('created_at', desc=True)\
            .limit(1)\
            .execute()

        # Get average scores (last 30 days)
        recent_evals = self.client.table('evaluation_runs')\
            .select('overall_score, ragas_score, ir_score, semantic_score')\
            .gte('created_at', datetime.now().isoformat())\
            .eq('status', 'completed')\
            .execute()

        stats = {
            'total_evaluations': total_evals.count if hasattr(total_evals, 'count') else 0,
            'latest_evaluation': latest_eval.data[0] if latest_eval.data else None,
            'recent_evaluations': recent_evals.data if recent_evals.data else []
        }

        # Calculate averages
        if stats['recent_evaluations']:
            scores = stats['recent_evaluations']
            stats['avg_overall_score'] = sum(s.get('overall_score', 0) or 0 for s in scores) / len(scores)
            stats['avg_ragas_score'] = sum(s.get('ragas_score', 0) or 0 for s in scores) / len(scores)
            stats['avg_ir_score'] = sum(s.get('ir_score', 0) or 0 for s in scores) / len(scores)
            stats['avg_semantic_score'] = sum(s.get('semantic_score', 0) or 0 for s in scores) / len(scores)

        return stats


if __name__ == "__main__":
    print("Evaluation Database Interface")
    print("=" * 60)
    print("\nFeatures:")
    print("- Create and manage evaluation runs")
    print("- Store detailed metrics (RAGAS, IR, Semantic)")
    print("- Save baseline comparisons")
    print("- Record ablation study results")
    print("- Store statistical test results")
    print("- Track error cases and analysis")
    print("- Monitor query type performance")
    print("- Record efficiency metrics")
    print("- Export history tracking")
    print("\nUsage:")
    print("  eval_db = EvaluationDB(supabase_client)")
    print("  run = eval_db.create_evaluation_run('experiment_1', user_id)")
    print("  eval_db.save_evaluation_metrics(run['id'], metrics)")
