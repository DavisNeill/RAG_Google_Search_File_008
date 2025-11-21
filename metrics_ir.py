"""
Information Retrieval Metrics Module
=====================================

Implements traditional IR metrics for RAG evaluation:
- Precision@k: Fraction of top-k results that are relevant
- Recall@k: Fraction of relevant docs in top-k results
- Mean Reciprocal Rank (MRR): Position of first relevant result
- Normalized Discounted Cumulative Gain (NDCG@k): Ranking quality
- Mean Average Precision (MAP): Overall retrieval quality
- F1@k: Harmonic mean of Precision and Recall

These are standard metrics accepted in all IR, NLP, and ML publications.
"""

from typing import List, Dict, Any, Set
import numpy as np
from collections import defaultdict


class IRMetricsEvaluator:
    """
    Evaluator for Information Retrieval metrics

    All metrics are computed based on binary relevance judgments.
    For graded relevance, NDCG provides ranking quality assessment.
    """

    def __init__(self, k_values: List[int] = [1, 3, 5, 10, 20]):
        """
        Initialize IR metrics evaluator

        Args:
            k_values: List of k values to compute metrics at (e.g., Precision@5, Recall@10)
        """
        self.k_values = k_values
        print(f"[IR Metrics] Initialized with k_values: {k_values}")

    def evaluate_batch(self, results: List[Any]) -> Dict[str, float]:
        """
        Evaluate IR metrics on a batch of results

        Args:
            results: List of QueryResult objects

        Returns:
            Dictionary of aggregated IR metrics
        """
        all_metrics = defaultdict(list)

        for result in results:
            # Get retrieved and relevant docs
            retrieved = result.retrieved_contexts
            # In real scenario, you'd have relevance judgments
            # For now, we use a simple check if ground truth appears in context
            relevant = self._get_relevant_contexts(result)

            # Compute metrics for this query
            query_metrics = self.evaluate_single(retrieved, relevant)

            # Aggregate
            for metric_name, value in query_metrics.items():
                all_metrics[metric_name].append(value)

        # Average across all queries
        aggregated = {}
        for metric_name, values in all_metrics.items():
            aggregated[f'ir_{metric_name}'] = float(np.mean(values))

        return aggregated

    def evaluate_single(
        self,
        retrieved: List[str],
        relevant: Set[str]
    ) -> Dict[str, float]:
        """
        Compute IR metrics for a single query

        Args:
            retrieved: List of retrieved documents (in rank order)
            relevant: Set of relevant document IDs

        Returns:
            Dictionary of IR metrics
        """
        metrics = {}

        # Compute metrics at different k values
        for k in self.k_values:
            metrics[f'precision_at_{k}'] = self.precision_at_k(retrieved, relevant, k)
            metrics[f'recall_at_{k}'] = self.recall_at_k(retrieved, relevant, k)
            metrics[f'f1_at_{k}'] = self.f1_at_k(retrieved, relevant, k)
            metrics[f'ndcg_at_{k}'] = self.ndcg_at_k(retrieved, relevant, k)

        # Compute overall metrics
        metrics['mrr'] = self.mean_reciprocal_rank(retrieved, relevant)
        metrics['map'] = self.mean_average_precision(retrieved, relevant)

        return metrics

    def precision_at_k(
        self,
        retrieved: List[str],
        relevant: Set[str],
        k: int
    ) -> float:
        """
        Compute Precision@k

        Precision@k = (# relevant docs in top-k) / k

        Args:
            retrieved: List of retrieved documents (ranked)
            relevant: Set of relevant documents
            k: Cut-off rank

        Returns:
            Precision@k score (0-1)
        """
        if k <= 0 or len(retrieved) == 0:
            return 0.0

        retrieved_at_k = retrieved[:k]
        relevant_count = sum(1 for doc in retrieved_at_k if doc in relevant)

        return relevant_count / k

    def recall_at_k(
        self,
        retrieved: List[str],
        relevant: Set[str],
        k: int
    ) -> float:
        """
        Compute Recall@k

        Recall@k = (# relevant docs in top-k) / (total # relevant docs)

        Args:
            retrieved: List of retrieved documents (ranked)
            relevant: Set of relevant documents
            k: Cut-off rank

        Returns:
            Recall@k score (0-1)
        """
        if len(relevant) == 0:
            return 0.0

        if k <= 0 or len(retrieved) == 0:
            return 0.0

        retrieved_at_k = retrieved[:k]
        relevant_count = sum(1 for doc in retrieved_at_k if doc in relevant)

        return relevant_count / len(relevant)

    def f1_at_k(
        self,
        retrieved: List[str],
        relevant: Set[str],
        k: int
    ) -> float:
        """
        Compute F1@k (harmonic mean of Precision@k and Recall@k)

        F1@k = 2 * (P@k * R@k) / (P@k + R@k)

        Args:
            retrieved: List of retrieved documents (ranked)
            relevant: Set of relevant documents
            k: Cut-off rank

        Returns:
            F1@k score (0-1)
        """
        precision = self.precision_at_k(retrieved, relevant, k)
        recall = self.recall_at_k(retrieved, relevant, k)

        if precision + recall == 0:
            return 0.0

        return 2 * (precision * recall) / (precision + recall)

    def mean_reciprocal_rank(
        self,
        retrieved: List[str],
        relevant: Set[str]
    ) -> float:
        """
        Compute Mean Reciprocal Rank (MRR)

        MRR = 1 / (rank of first relevant document)

        Used to measure "how quickly does the system find a relevant result"

        Args:
            retrieved: List of retrieved documents (ranked)
            relevant: Set of relevant documents

        Returns:
            MRR score (0-1, higher is better)
        """
        for rank, doc in enumerate(retrieved, start=1):
            if doc in relevant:
                return 1.0 / rank

        return 0.0

    def average_precision(
        self,
        retrieved: List[str],
        relevant: Set[str]
    ) -> float:
        """
        Compute Average Precision (AP) for a single query

        AP = (sum of Precision@k for each relevant doc) / (total # relevant docs)

        Args:
            retrieved: List of retrieved documents (ranked)
            relevant: Set of relevant documents

        Returns:
            AP score (0-1)
        """
        if len(relevant) == 0:
            return 0.0

        score = 0.0
        num_relevant = 0

        for rank, doc in enumerate(retrieved, start=1):
            if doc in relevant:
                num_relevant += 1
                precision_at_rank = num_relevant / rank
                score += precision_at_rank

        return score / len(relevant)

    def mean_average_precision(
        self,
        retrieved: List[str],
        relevant: Set[str]
    ) -> float:
        """
        Compute Mean Average Precision (MAP)

        This is the same as AP for a single query.
        When averaged over multiple queries, it becomes MAP.

        Args:
            retrieved: List of retrieved documents (ranked)
            relevant: Set of relevant documents

        Returns:
            MAP score (0-1)
        """
        return self.average_precision(retrieved, relevant)

    def dcg_at_k(
        self,
        retrieved: List[str],
        relevant: Set[str],
        k: int
    ) -> float:
        """
        Compute Discounted Cumulative Gain at k (DCG@k)

        DCG@k = sum_{i=1}^{k} (relevance_i / log2(i + 1))

        Args:
            retrieved: List of retrieved documents (ranked)
            relevant: Set of relevant documents (binary relevance: 0 or 1)
            k: Cut-off rank

        Returns:
            DCG@k score
        """
        dcg = 0.0
        for i, doc in enumerate(retrieved[:k], start=1):
            relevance = 1.0 if doc in relevant else 0.0
            dcg += relevance / np.log2(i + 1)

        return dcg

    def idcg_at_k(
        self,
        relevant: Set[str],
        k: int
    ) -> float:
        """
        Compute Ideal DCG at k (IDCG@k)

        This is the DCG of the ideal ranking (all relevant docs at top).

        Args:
            relevant: Set of relevant documents
            k: Cut-off rank

        Returns:
            IDCG@k score
        """
        # Ideal ranking: all relevant docs first
        num_relevant = min(len(relevant), k)

        idcg = 0.0
        for i in range(1, num_relevant + 1):
            idcg += 1.0 / np.log2(i + 1)

        return idcg

    def ndcg_at_k(
        self,
        retrieved: List[str],
        relevant: Set[str],
        k: int
    ) -> float:
        """
        Compute Normalized Discounted Cumulative Gain at k (NDCG@k)

        NDCG@k = DCG@k / IDCG@k

        Measures ranking quality on a 0-1 scale.
        1.0 = perfect ranking, 0.0 = no relevant docs retrieved.

        Args:
            retrieved: List of retrieved documents (ranked)
            relevant: Set of relevant documents
            k: Cut-off rank

        Returns:
            NDCG@k score (0-1)
        """
        dcg = self.dcg_at_k(retrieved, relevant, k)
        idcg = self.idcg_at_k(relevant, k)

        if idcg == 0:
            return 0.0

        return dcg / idcg

    def _get_relevant_contexts(self, result: Any) -> Set[str]:
        """
        Extract relevant contexts from a QueryResult

        In a real scenario, you would have gold relevance judgments.
        Here we use a simple heuristic: contexts that contain keywords from ground truth.

        Args:
            result: QueryResult object

        Returns:
            Set of relevant context identifiers
        """
        relevant = set()

        # Simple heuristic: mark contexts as relevant if they contain ground truth keywords
        ground_truth_words = set(result.ground_truth.lower().split())

        for ctx in result.retrieved_contexts:
            ctx_words = set(ctx.lower().split())
            # If context shares significant overlap with ground truth, consider it relevant
            overlap = len(ground_truth_words & ctx_words)
            if overlap >= min(3, len(ground_truth_words) // 2):
                relevant.add(ctx)

        return relevant


def compute_ir_metrics_summary(metrics: Dict[str, float]) -> Dict[str, Any]:
    """
    Compute summary statistics for IR metrics

    Args:
        metrics: Dictionary of IR metrics

    Returns:
        Summary statistics
    """
    summary = {}

    # Group by metric type
    for metric_name, value in metrics.items():
        if 'precision' in metric_name:
            if 'precision' not in summary:
                summary['precision'] = []
            summary['precision'].append(value)
        elif 'recall' in metric_name:
            if 'recall' not in summary:
                summary['recall'] = []
            summary['recall'].append(value)
        elif 'ndcg' in metric_name:
            if 'ndcg' not in summary:
                summary['ndcg'] = []
            summary['ndcg'].append(value)

    # Compute averages
    for key in summary:
        summary[f'{key}_mean'] = np.mean(summary[key])
        summary[f'{key}_std'] = np.std(summary[key])

    return summary


if __name__ == "__main__":
    print("Information Retrieval Metrics Evaluator")
    print("=" * 60)

    # Example usage
    evaluator = IRMetricsEvaluator(k_values=[1, 3, 5, 10])

    # Example: Retrieved docs and relevant docs
    retrieved = ['doc1', 'doc2', 'doc3', 'doc4', 'doc5', 'doc6', 'doc7', 'doc8', 'doc9', 'doc10']
    relevant = {'doc1', 'doc3', 'doc7', 'doc9'}

    print("\nExample Evaluation:")
    print(f"Retrieved (top 10): {retrieved}")
    print(f"Relevant: {relevant}")

    metrics = evaluator.evaluate_single(retrieved, relevant)

    print("\nMetrics:")
    for metric_name, value in sorted(metrics.items()):
        print(f"  {metric_name}: {value:.4f}")

    # Interpretation
    print("\nInterpretation:")
    print(f"  - Precision@5: {metrics['precision_at_5']:.2%} of top-5 results are relevant")
    print(f"  - Recall@5: Found {metrics['recall_at_5']:.2%} of all relevant docs in top-5")
    print(f"  - MRR: First relevant result at position {1/metrics['mrr']:.0f}")
    print(f"  - NDCG@10: Ranking quality score of {metrics['ndcg_at_10']:.2%}")
