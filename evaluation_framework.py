"""
Comprehensive Evaluation Framework for Agentic RAG System
==========================================================

Research-grade evaluation for journal publication including:
- RAGAS metrics (faithfulness, relevancy, context precision/recall)
- Traditional IR metrics (Precision@k, Recall@k, MRR, NDCG)
- Semantic similarity (BERTScore, ROUGE)
- Multiple baselines comparison
- Ablation studies
- Statistical significance testing
- Human evaluation interface
- Error analysis
- LaTeX export for papers

Designed for publication in top-tier venues (TACL, JAIR, ACL, EMNLP, etc.)
"""

import json
import time
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from pathlib import Path
import pandas as pd
import numpy as np

# Import evaluation components
from metrics_ragas import RAGASEvaluator
from metrics_ir import IRMetricsEvaluator
from metrics_semantic import SemanticEvaluator
from baselines import BaselineManager
from ablation import AblationStudy
from statistical_analysis import StatisticalAnalyzer
from visualization import PaperVisualizer
from latex_export import LaTeXExporter


@dataclass
class EvaluationConfig:
    """Configuration for evaluation experiments"""

    # Experiment metadata
    experiment_name: str
    experiment_id: str = field(default_factory=lambda: datetime.now().strftime("%Y%m%d_%H%M%S"))
    description: str = ""

    # Dataset configuration
    dataset_path: str = "evaluation_data/test_set.json"
    num_samples: Optional[int] = None  # None = use all

    # System configurations to evaluate
    evaluate_baselines: bool = True
    evaluate_ablations: bool = True

    # Metrics to compute
    compute_ragas: bool = True
    compute_ir_metrics: bool = True
    compute_semantic: bool = True
    compute_efficiency: bool = True

    # Statistical analysis
    compute_significance: bool = True
    significance_level: float = 0.05

    # Human evaluation
    include_human_eval: bool = False
    num_human_samples: int = 100

    # Output configuration
    output_dir: str = "evaluation_results"
    generate_latex: bool = True
    generate_plots: bool = True
    save_detailed_results: bool = True


@dataclass
class QueryResult:
    """Result from a single query evaluation"""
    query_id: str
    question: str
    ground_truth: str
    predicted_answer: str
    retrieved_contexts: List[str]

    # Metadata
    query_type: str
    system_name: str
    timestamp: str

    # Performance metrics
    latency_ms: float
    tokens_used: int

    # Quality scores (computed later)
    scores: Dict[str, float] = field(default_factory=dict)


@dataclass
class EvaluationResults:
    """Complete evaluation results"""
    config: EvaluationConfig

    # Aggregate metrics per system
    system_metrics: Dict[str, Dict[str, float]] = field(default_factory=dict)

    # Detailed per-query results
    query_results: List[QueryResult] = field(default_factory=list)

    # Statistical analysis
    statistical_tests: Dict[str, Any] = field(default_factory=dict)

    # Human evaluation (if performed)
    human_evaluation: Optional[Dict[str, Any]] = None

    # Error analysis
    error_analysis: Dict[str, Any] = field(default_factory=dict)

    # Timing information
    total_evaluation_time: float = 0.0

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON export"""
        return asdict(self)

    def save(self, output_path: str):
        """Save results to JSON file"""
        with open(output_path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, input_path: str) -> 'EvaluationResults':
        """Load results from JSON file"""
        with open(input_path, 'r') as f:
            data = json.load(f)
        return cls(**data)


class EvaluationFramework:
    """
    Main evaluation framework orchestrator

    Coordinates all evaluation components to produce comprehensive
    research-grade evaluation results suitable for journal publication.
    """

    def __init__(self, config: EvaluationConfig):
        """
        Initialize evaluation framework

        Args:
            config: Evaluation configuration
        """
        self.config = config

        # Create output directory
        self.output_dir = Path(config.output_dir) / config.experiment_id
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize evaluation components
        self.ragas_evaluator = RAGASEvaluator() if config.compute_ragas else None
        self.ir_evaluator = IRMetricsEvaluator() if config.compute_ir_metrics else None
        self.semantic_evaluator = SemanticEvaluator() if config.compute_semantic else None

        # Initialize comparison components
        self.baseline_manager = BaselineManager() if config.evaluate_baselines else None
        self.ablation_study = AblationStudy() if config.evaluate_ablations else None

        # Initialize analysis components
        self.statistical_analyzer = StatisticalAnalyzer()
        self.visualizer = PaperVisualizer(self.output_dir)
        self.latex_exporter = LaTeXExporter(self.output_dir)

        print(f"[EvaluationFramework] Initialized with ID: {config.experiment_id}")
        print(f"[EvaluationFramework] Output directory: {self.output_dir}")

    def load_dataset(self) -> List[Dict]:
        """
        Load evaluation dataset

        Returns:
            List of evaluation samples with format:
            {
                'query_id': str,
                'question': str,
                'ground_truth': str,
                'query_type': str,
                'relevant_docs': List[str]
            }
        """
        print(f"[EvaluationFramework] Loading dataset from {self.config.dataset_path}")

        with open(self.config.dataset_path, 'r') as f:
            dataset = json.load(f)

        # Sample if needed
        if self.config.num_samples:
            dataset = dataset[:self.config.num_samples]

        print(f"[EvaluationFramework] Loaded {len(dataset)} samples")
        return dataset

    def evaluate_system(
        self,
        system,
        system_name: str,
        dataset: List[Dict]
    ) -> List[QueryResult]:
        """
        Evaluate a single system on the dataset

        Args:
            system: System to evaluate (with .query() method)
            system_name: Name of the system for reporting
            dataset: List of evaluation samples

        Returns:
            List of QueryResult objects
        """
        print(f"\n[EvaluationFramework] Evaluating system: {system_name}")
        print(f"[EvaluationFramework] Processing {len(dataset)} queries...")

        results = []

        for i, sample in enumerate(dataset):
            try:
                # Time the query
                start_time = time.time()

                # Execute query
                response = system.query(
                    question=sample['question'],
                    include_citations=True
                )

                latency_ms = (time.time() - start_time) * 1000

                # Create result object
                result = QueryResult(
                    query_id=sample['query_id'],
                    question=sample['question'],
                    ground_truth=sample['ground_truth'],
                    predicted_answer=response.get('text', ''),
                    retrieved_contexts=self._extract_contexts(response),
                    query_type=sample.get('query_type', 'GENERAL'),
                    system_name=system_name,
                    timestamp=datetime.now().isoformat(),
                    latency_ms=latency_ms,
                    tokens_used=self._estimate_tokens(response)
                )

                results.append(result)

                # Progress update
                if (i + 1) % 10 == 0:
                    print(f"  Processed {i + 1}/{len(dataset)} queries")

            except Exception as e:
                print(f"  Error processing query {sample['query_id']}: {e}")
                continue

        print(f"[EvaluationFramework] Completed {len(results)} queries for {system_name}")
        return results

    def compute_metrics(self, results: List[QueryResult]) -> Dict[str, float]:
        """
        Compute all metrics for a set of results

        Args:
            results: List of QueryResult objects

        Returns:
            Dictionary of metric scores
        """
        print(f"[EvaluationFramework] Computing metrics for {len(results)} results...")

        metrics = {}

        # RAGAS metrics
        if self.ragas_evaluator:
            print("  Computing RAGAS metrics...")
            ragas_scores = self.ragas_evaluator.evaluate_batch(results)
            metrics.update(ragas_scores)

        # IR metrics
        if self.ir_evaluator:
            print("  Computing IR metrics...")
            ir_scores = self.ir_evaluator.evaluate_batch(results)
            metrics.update(ir_scores)

        # Semantic similarity metrics
        if self.semantic_evaluator:
            print("  Computing semantic metrics...")
            semantic_scores = self.semantic_evaluator.evaluate_batch(results)
            metrics.update(semantic_scores)

        # Efficiency metrics
        if self.config.compute_efficiency:
            print("  Computing efficiency metrics...")
            efficiency_scores = self._compute_efficiency_metrics(results)
            metrics.update(efficiency_scores)

        print(f"[EvaluationFramework] Computed {len(metrics)} metrics")
        return metrics

    def run_full_evaluation(self, systems: Dict[str, Any]) -> EvaluationResults:
        """
        Run complete evaluation on multiple systems

        Args:
            systems: Dictionary mapping system names to system objects
                    Example: {'Baseline RAG': baseline_rag, 'Agentic RAG': agentic_rag}

        Returns:
            Complete evaluation results
        """
        print("\n" + "="*80)
        print(f"EVALUATION EXPERIMENT: {self.config.experiment_name}")
        print(f"Experiment ID: {self.config.experiment_id}")
        print("="*80 + "\n")

        start_time = time.time()

        # Load dataset
        dataset = self.load_dataset()

        # Evaluate each system
        all_query_results = []
        system_metrics = {}

        for system_name, system in systems.items():
            # Run queries
            query_results = self.evaluate_system(system, system_name, dataset)
            all_query_results.extend(query_results)

            # Compute metrics
            metrics = self.compute_metrics(query_results)
            system_metrics[system_name] = metrics

            # Store metrics in query results
            for result in query_results:
                result.scores = metrics

        # Statistical significance testing
        statistical_tests = {}
        if self.config.compute_significance and len(systems) >= 2:
            print("\n[EvaluationFramework] Computing statistical significance...")
            statistical_tests = self.statistical_analyzer.compare_systems(
                system_metrics,
                alpha=self.config.significance_level
            )

        # Error analysis
        print("\n[EvaluationFramework] Performing error analysis...")
        error_analysis = self._perform_error_analysis(all_query_results)

        # Create results object
        results = EvaluationResults(
            config=self.config,
            system_metrics=system_metrics,
            query_results=all_query_results,
            statistical_tests=statistical_tests,
            error_analysis=error_analysis,
            total_evaluation_time=time.time() - start_time
        )

        # Save results
        self._save_results(results)

        # Generate outputs for paper
        if self.config.generate_latex:
            self._generate_latex_tables(results)

        if self.config.generate_plots:
            self._generate_visualizations(results)

        print("\n" + "="*80)
        print(f"EVALUATION COMPLETE")
        print(f"Total time: {results.total_evaluation_time:.2f} seconds")
        print(f"Results saved to: {self.output_dir}")
        print("="*80 + "\n")

        return results

    def _extract_contexts(self, response: Dict) -> List[str]:
        """Extract retrieved contexts from response"""
        contexts = []
        if 'citations' in response:
            for citation in response['citations']:
                contexts.append(citation.get('snippet', ''))
        return contexts

    def _estimate_tokens(self, response: Dict) -> int:
        """Estimate token count (rough approximation)"""
        text = response.get('text', '')
        # Rough estimate: 1 token ≈ 4 characters
        return len(text) // 4

    def _compute_efficiency_metrics(self, results: List[QueryResult]) -> Dict[str, float]:
        """Compute efficiency-related metrics"""
        latencies = [r.latency_ms for r in results]
        tokens = [r.tokens_used for r in results]

        return {
            'mean_latency_ms': float(np.mean(latencies)),
            'median_latency_ms': float(np.median(latencies)),
            'std_latency_ms': float(np.std(latencies)),
            'p95_latency_ms': float(np.percentile(latencies, 95)),
            'mean_tokens': float(np.mean(tokens)),
            'total_tokens': int(np.sum(tokens))
        }

    def _perform_error_analysis(self, results: List[QueryResult]) -> Dict[str, Any]:
        """Perform detailed error analysis"""
        # Group by query type
        by_type = {}
        for result in results:
            if result.query_type not in by_type:
                by_type[result.query_type] = []
            by_type[result.query_type].append(result)

        # Analyze performance by query type
        type_analysis = {}
        for qtype, type_results in by_type.items():
            type_analysis[qtype] = {
                'count': len(type_results),
                'mean_latency': float(np.mean([r.latency_ms for r in type_results]))
            }

        return {
            'by_query_type': type_analysis,
            'total_queries': len(results)
        }

    def _save_results(self, results: EvaluationResults):
        """Save evaluation results"""
        # Save main results as JSON
        results_path = self.output_dir / 'results.json'
        results.save(str(results_path))
        print(f"[EvaluationFramework] Saved results to {results_path}")

        # Save metrics as CSV
        metrics_df = pd.DataFrame(results.system_metrics).T
        metrics_path = self.output_dir / 'metrics.csv'
        metrics_df.to_csv(metrics_path)
        print(f"[EvaluationFramework] Saved metrics to {metrics_path}")

        # Save detailed query results
        if self.config.save_detailed_results:
            query_data = [asdict(qr) for qr in results.query_results]
            query_df = pd.DataFrame(query_data)
            query_path = self.output_dir / 'query_results.csv'
            query_df.to_csv(query_path, index=False)
            print(f"[EvaluationFramework] Saved query results to {query_path}")

    def _generate_latex_tables(self, results: EvaluationResults):
        """Generate LaTeX tables for paper"""
        print("[EvaluationFramework] Generating LaTeX tables...")

        # Main results table
        self.latex_exporter.create_results_table(
            results.system_metrics,
            output_file='table_main_results.tex'
        )

        # Statistical significance table
        if results.statistical_tests:
            self.latex_exporter.create_significance_table(
                results.statistical_tests,
                output_file='table_significance.tex'
            )

        print(f"[EvaluationFramework] LaTeX tables saved to {self.output_dir}")

    def _generate_visualizations(self, results: EvaluationResults):
        """Generate publication-quality visualizations"""
        print("[EvaluationFramework] Generating visualizations...")

        # Performance comparison plot
        self.visualizer.create_comparison_plot(
            results.system_metrics,
            output_file='fig_comparison.pdf'
        )

        # Latency distribution plot
        self.visualizer.create_latency_plot(
            results.query_results,
            output_file='fig_latency.pdf'
        )

        # Performance by query type
        self.visualizer.create_query_type_plot(
            results.query_results,
            output_file='fig_query_types.pdf'
        )

        print(f"[EvaluationFramework] Plots saved to {self.output_dir}")


def create_evaluation_config(
    experiment_name: str,
    dataset_path: str,
    **kwargs
) -> EvaluationConfig:
    """
    Convenience function to create evaluation configuration

    Args:
        experiment_name: Name of the experiment
        dataset_path: Path to evaluation dataset
        **kwargs: Additional configuration parameters

    Returns:
        EvaluationConfig object
    """
    return EvaluationConfig(
        experiment_name=experiment_name,
        dataset_path=dataset_path,
        **kwargs
    )


if __name__ == "__main__":
    print("Evaluation Framework for Agentic RAG - Research Grade")
    print("=" * 60)
    print("\nThis module provides comprehensive evaluation capabilities")
    print("for research publication in top-tier venues.")
    print("\nUsage:")
    print("  from evaluation_framework import EvaluationFramework, create_evaluation_config")
    print("  config = create_evaluation_config('My Experiment', 'data/test.json')")
    print("  framework = EvaluationFramework(config)")
    print("  results = framework.run_full_evaluation(systems)")
