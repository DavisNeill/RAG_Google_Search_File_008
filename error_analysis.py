"""
Error Analysis Tools
====================

Analyzes failure cases and system errors to understand:
- Where the system fails
- Why it fails
- What types of queries are problematic
- Common error patterns

Essential for journal publication to demonstrate deep understanding
of system limitations and opportunities for improvement.
"""

from typing import List, Dict, Any, Tuple
from dataclasses import dataclass, field
from collections import Counter, defaultdict
import numpy as np


@dataclass
class ErrorCase:
    """Represents a single error/failure case"""
    query_id: str
    question: str
    ground_truth: str
    predicted_answer: str
    retrieved_contexts: List[str]
    scores: Dict[str, float]
    error_type: str = ""
    error_severity: str = ""  # low, medium, high
    notes: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ErrorCategory:
    """Category of errors with examples"""
    name: str
    description: str
    count: int
    examples: List[ErrorCase]
    severity_distribution: Dict[str, int] = field(default_factory=dict)


class ErrorAnalyzer:
    """
    Analyzes system errors and failure cases

    Provides insights into:
    - Error distribution
    - Common failure patterns
    - Query characteristics that lead to errors
    - Retrieval vs generation errors
    """

    def __init__(self, score_threshold: float = 0.7):
        """
        Initialize error analyzer

        Args:
            score_threshold: Threshold below which a result is considered an error
        """
        self.score_threshold = score_threshold
        self.error_cases = []
        self.error_categories = {}

        print(f"[Error Analyzer] Initialized (threshold={score_threshold})")

    def identify_errors(
        self,
        results: List[Any],
        score_metric: str = 'overall'
    ) -> List[ErrorCase]:
        """
        Identify error cases from results

        Args:
            results: List of evaluation results
            score_metric: Metric to use for error identification

        Returns:
            List of ErrorCase objects
        """
        errors = []

        for result in results:
            score = result.scores.get(score_metric, 0.0)

            if score < self.score_threshold:
                error = ErrorCase(
                    query_id=result.query_id,
                    question=result.question,
                    ground_truth=result.ground_truth,
                    predicted_answer=result.predicted_answer,
                    retrieved_contexts=result.retrieved_contexts,
                    scores=result.scores,
                    metadata={
                        'query_type': result.metadata.get('query_type', 'UNKNOWN'),
                        'latency_ms': result.metadata.get('latency_ms', 0),
                        'score': score
                    }
                )

                # Classify error severity
                if score < 0.3:
                    error.error_severity = "high"
                elif score < 0.5:
                    error.error_severity = "medium"
                else:
                    error.error_severity = "low"

                errors.append(error)

        self.error_cases = errors
        print(f"[Error Analyzer] Found {len(errors)} error cases")

        return errors

    def categorize_errors(self, errors: List[ErrorCase]) -> Dict[str, ErrorCategory]:
        """
        Categorize errors into different types

        Args:
            errors: List of error cases

        Returns:
            Dictionary mapping category names to ErrorCategory objects
        """
        categories = defaultdict(list)

        for error in errors:
            # Determine error type
            error_type = self._classify_error_type(error)
            error.error_type = error_type
            categories[error_type].append(error)

        # Create ErrorCategory objects
        error_categories = {}
        for category_name, category_errors in categories.items():
            severity_dist = Counter([e.error_severity for e in category_errors])

            error_categories[category_name] = ErrorCategory(
                name=category_name,
                description=self._get_category_description(category_name),
                count=len(category_errors),
                examples=category_errors[:5],  # Keep top 5 examples
                severity_distribution=dict(severity_dist)
            )

        self.error_categories = error_categories
        print(f"[Error Analyzer] Categorized into {len(error_categories)} types")

        return error_categories

    def _classify_error_type(self, error: ErrorCase) -> str:
        """
        Classify error into a specific type

        Args:
            error: ErrorCase object

        Returns:
            Error type string
        """
        # Check for different error patterns

        # 1. Retrieval failure (no relevant contexts)
        if not error.retrieved_contexts or len(error.retrieved_contexts) == 0:
            return "retrieval_empty"

        # 2. Hallucination (answer not grounded in contexts)
        faithfulness = error.scores.get('ragas_faithfulness', 1.0)
        if faithfulness < 0.5:
            return "hallucination"

        # 3. Incomplete answer
        if len(error.predicted_answer.split()) < 10:
            return "incomplete_answer"

        # 4. Irrelevant answer
        answer_relevancy = error.scores.get('ragas_answer_relevancy', 1.0)
        if answer_relevancy < 0.5:
            return "irrelevant_answer"

        # 5. Context precision issue (retrieved irrelevant docs)
        context_precision = error.scores.get('ragas_context_precision', 1.0)
        if context_precision < 0.5:
            return "poor_retrieval"

        # 6. Context recall issue (missed relevant info)
        context_recall = error.scores.get('ragas_context_recall', 1.0)
        if context_recall < 0.5:
            return "missing_information"

        # 7. General low quality
        return "low_quality"

    def _get_category_description(self, category_name: str) -> str:
        """Get description for error category"""
        descriptions = {
            'retrieval_empty': 'No documents retrieved',
            'hallucination': 'Answer not grounded in retrieved context',
            'incomplete_answer': 'Answer is too short or incomplete',
            'irrelevant_answer': 'Answer does not address the question',
            'poor_retrieval': 'Retrieved contexts are not relevant',
            'missing_information': 'Failed to retrieve all necessary information',
            'low_quality': 'General quality issues'
        }
        return descriptions.get(category_name, 'Unknown error type')

    def analyze_query_characteristics(
        self,
        errors: List[ErrorCase]
    ) -> Dict[str, Any]:
        """
        Analyze characteristics of queries that lead to errors

        Args:
            errors: List of error cases

        Returns:
            Analysis of query characteristics
        """
        analysis = {
            'total_errors': len(errors),
            'by_query_type': {},
            'by_severity': {},
            'by_error_type': {},
            'question_length_stats': {},
            'common_patterns': []
        }

        # Query type distribution
        query_types = [e.metadata.get('query_type', 'UNKNOWN') for e in errors]
        analysis['by_query_type'] = dict(Counter(query_types))

        # Severity distribution
        severities = [e.error_severity for e in errors]
        analysis['by_severity'] = dict(Counter(severities))

        # Error type distribution
        error_types = [e.error_type for e in errors]
        analysis['by_error_type'] = dict(Counter(error_types))

        # Question length statistics
        question_lengths = [len(e.question.split()) for e in errors]
        analysis['question_length_stats'] = {
            'mean': float(np.mean(question_lengths)),
            'median': float(np.median(question_lengths)),
            'min': int(np.min(question_lengths)),
            'max': int(np.max(question_lengths))
        }

        # Common patterns
        analysis['common_patterns'] = self._identify_common_patterns(errors)

        return analysis

    def _identify_common_patterns(self, errors: List[ErrorCase]) -> List[str]:
        """Identify common patterns in error cases"""
        patterns = []

        # Check for common words in failed queries
        all_questions = " ".join([e.question.lower() for e in errors])
        words = all_questions.split()
        common_words = [word for word, count in Counter(words).most_common(10)
                       if len(word) > 3]  # Ignore short words

        if common_words:
            patterns.append(f"Common words in failed queries: {', '.join(common_words[:5])}")

        # Check for query complexity
        complex_queries = [e for e in errors if len(e.question.split()) > 20]
        if len(complex_queries) > len(errors) * 0.5:
            patterns.append("Many errors occur on complex, long questions")

        # Check for retrieval issues
        poor_retrieval = [e for e in errors
                         if e.scores.get('ragas_context_precision', 1.0) < 0.5]
        if len(poor_retrieval) > len(errors) * 0.5:
            patterns.append("Retrieval quality is a major issue")

        # Check for hallucination
        hallucinations = [e for e in errors
                         if e.scores.get('ragas_faithfulness', 1.0) < 0.5]
        if len(hallucinations) > len(errors) * 0.3:
            patterns.append("Hallucination is a significant problem")

        return patterns

    def compare_error_rates(
        self,
        system_results: Dict[str, List[Any]]
    ) -> Dict[str, Dict[str, float]]:
        """
        Compare error rates across different systems

        Args:
            system_results: Dictionary mapping system names to results

        Returns:
            Error rate comparison
        """
        comparison = {}

        for system_name, results in system_results.items():
            errors = self.identify_errors(results)
            total = len(results)

            error_rate = len(errors) / total if total > 0 else 0

            # Break down by severity
            severity_counts = Counter([e.error_severity for e in errors])

            comparison[system_name] = {
                'total_queries': total,
                'total_errors': len(errors),
                'error_rate': error_rate,
                'high_severity_rate': severity_counts.get('high', 0) / total if total > 0 else 0,
                'medium_severity_rate': severity_counts.get('medium', 0) / total if total > 0 else 0,
                'low_severity_rate': severity_counts.get('low', 0) / total if total > 0 else 0
            }

        return comparison

    def generate_error_report(
        self,
        output_file: str = "error_analysis_report.txt"
    ):
        """
        Generate comprehensive error analysis report

        Args:
            output_file: Output filename
        """
        report = []
        report.append("=" * 80)
        report.append("ERROR ANALYSIS REPORT")
        report.append("=" * 80)
        report.append("")

        # Summary
        report.append("SUMMARY")
        report.append("-" * 80)
        report.append(f"Total error cases analyzed: {len(self.error_cases)}")
        report.append(f"Error categories identified: {len(self.error_categories)}")
        report.append("")

        # Error categories
        report.append("ERROR CATEGORIES")
        report.append("-" * 80)
        for category_name, category in self.error_categories.items():
            report.append(f"\n{category_name.upper()} ({category.count} cases)")
            report.append(f"Description: {category.description}")
            report.append(f"Severity distribution: {category.severity_distribution}")
            report.append("\nExample cases:")
            for i, example in enumerate(category.examples[:3], 1):
                report.append(f"  {i}. Q: {example.question[:100]}...")
                report.append(f"     A: {example.predicted_answer[:100]}...")
                report.append(f"     Score: {example.metadata.get('score', 0):.3f}")
                report.append("")

        # Query characteristics
        if self.error_cases:
            analysis = self.analyze_query_characteristics(self.error_cases)
            report.append("\nQUERY CHARACTERISTICS")
            report.append("-" * 80)
            report.append(f"Error distribution by query type:")
            for qtype, count in analysis['by_query_type'].items():
                report.append(f"  {qtype}: {count}")
            report.append(f"\nError distribution by severity:")
            for severity, count in analysis['by_severity'].items():
                report.append(f"  {severity}: {count}")
            report.append(f"\nQuestion length statistics:")
            report.append(f"  Mean: {analysis['question_length_stats']['mean']:.1f} words")
            report.append(f"  Median: {analysis['question_length_stats']['median']:.1f} words")
            report.append(f"\nCommon patterns:")
            for pattern in analysis['common_patterns']:
                report.append(f"  - {pattern}")

        # Recommendations
        report.append("\n\nRECOMMENDATIONS")
        report.append("-" * 80)
        recommendations = self._generate_recommendations()
        for rec in recommendations:
            report.append(f"- {rec}")

        # Save report
        with open(output_file, 'w') as f:
            f.write("\n".join(report))

        print(f"[Error Analyzer] Report saved to {output_file}")

        return "\n".join(report)

    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on error analysis"""
        recommendations = []

        if not self.error_categories:
            return recommendations

        # Check for retrieval issues
        retrieval_errors = sum([
            self.error_categories.get('retrieval_empty', ErrorCategory('', '', 0, [])).count,
            self.error_categories.get('poor_retrieval', ErrorCategory('', '', 0, [])).count,
            self.error_categories.get('missing_information', ErrorCategory('', '', 0, [])).count
        ])

        if retrieval_errors > len(self.error_cases) * 0.3:
            recommendations.append(
                "Improve retrieval quality: Consider using hybrid search (BM25 + dense retrieval), "
                "query expansion, or better embedding models"
            )

        # Check for hallucination
        hallucination_count = self.error_categories.get(
            'hallucination',
            ErrorCategory('', '', 0, [])
        ).count

        if hallucination_count > len(self.error_cases) * 0.2:
            recommendations.append(
                "Reduce hallucination: Use stronger prompting to enforce grounding in context, "
                "or implement attribution mechanisms"
            )

        # Check for relevancy issues
        irrelevant_count = self.error_categories.get(
            'irrelevant_answer',
            ErrorCategory('', '', 0, [])
        ).count

        if irrelevant_count > len(self.error_cases) * 0.2:
            recommendations.append(
                "Improve answer relevancy: Enhance query understanding and decomposition, "
                "or use better response synthesis"
            )

        # General recommendation
        recommendations.append(
            "Collect more training data for query types with high error rates"
        )

        return recommendations

    def export_error_examples_for_annotation(
        self,
        output_file: str = "error_cases_for_annotation.jsonl",
        max_examples: int = 100
    ):
        """
        Export error cases for human annotation

        Args:
            output_file: Output filename
            max_examples: Maximum number of examples to export
        """
        import json

        examples = []
        for error in self.error_cases[:max_examples]:
            example = {
                'query_id': error.query_id,
                'question': error.question,
                'ground_truth': error.ground_truth,
                'predicted_answer': error.predicted_answer,
                'retrieved_contexts': error.retrieved_contexts,
                'error_type': error.error_type,
                'error_severity': error.error_severity,
                'scores': error.scores,
                'annotation': {
                    'error_confirmed': None,
                    'actual_error_type': None,
                    'notes': None
                }
            }
            examples.append(example)

        with open(output_file, 'w') as f:
            for example in examples:
                f.write(json.dumps(example) + '\n')

        print(f"[Error Analyzer] Exported {len(examples)} cases to {output_file}")


if __name__ == "__main__":
    print("Error Analysis Tools")
    print("=" * 60)
    print("\nError Analysis Capabilities:")
    print("1. Error identification and classification")
    print("2. Error categorization by type")
    print("3. Query characteristic analysis")
    print("4. Error rate comparison across systems")
    print("5. Detailed error reports")
    print("6. Recommendations for improvement")
    print("\nUsage:")
    print("  analyzer = ErrorAnalyzer(score_threshold=0.7)")
    print("  errors = analyzer.identify_errors(results)")
    print("  categories = analyzer.categorize_errors(errors)")
    print("  report = analyzer.generate_error_report()")
