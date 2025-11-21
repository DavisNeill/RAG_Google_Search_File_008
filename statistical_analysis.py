"""
Statistical Analysis Module
============================

Implements statistical tests for research publications:
- Paired t-tests for comparing systems
- Confidence intervals (95%, 99%)
- Effect size (Cohen's d)
- Statistical significance testing
- Bonferroni correction for multiple comparisons

Essential for proving your improvements are statistically significant.
"""

from typing import Dict, List, Tuple, Any
import numpy as np
from scipy import stats
from dataclasses import dataclass


@dataclass
class StatisticalTest:
    """Results from a statistical significance test"""
    test_name: str
    statistic: float
    p_value: float
    is_significant: bool
    alpha: float
    effect_size: float = None
    confidence_interval: Tuple[float, float] = None

    def to_dict(self) -> Dict:
        return {
            'test_name': self.test_name,
            'statistic': self.statistic,
            'p_value': self.p_value,
            'is_significant': self.is_significant,
            'alpha': self.alpha,
            'effect_size': self.effect_size,
            'confidence_interval': self.confidence_interval
        }


class StatisticalAnalyzer:
    """
    Statistical analyzer for research evaluation

    Provides rigorous statistical tests required for journal publication.
    """

    def __init__(self, alpha: float = 0.05):
        """
        Initialize statistical analyzer

        Args:
            alpha: Significance level (default: 0.05 for p < 0.05)
        """
        self.alpha = alpha
        print(f"[Statistical Analyzer] Initialized with α = {alpha}")

    def compare_systems(
        self,
        system_metrics: Dict[str, Dict[str, float]],
        alpha: float = None
    ) -> Dict[str, Any]:
        """
        Compare multiple systems with statistical tests

        Args:
            system_metrics: Dictionary mapping system names to their metrics
            alpha: Significance level (uses self.alpha if None)

        Returns:
            Dictionary of statistical test results
        """
        if alpha is None:
            alpha = self.alpha

        results = {}

        # Get system names
        system_names = list(system_metrics.keys())

        if len(system_names) < 2:
            print("Warning: Need at least 2 systems for comparison")
            return results

        # Pairwise comparisons
        results['pairwise_tests'] = {}

        for i in range(len(system_names)):
            for j in range(i + 1, len(system_names)):
                system_a = system_names[i]
                system_b = system_names[j]

                comparison_key = f"{system_a}_vs_{system_b}"
                results['pairwise_tests'][comparison_key] = self._compare_two_systems(
                    system_a,
                    system_b,
                    system_metrics[system_a],
                    system_metrics[system_b],
                    alpha
                )

        # Bonferroni correction for multiple comparisons
        num_comparisons = len(results['pairwise_tests'])
        results['bonferroni_corrected_alpha'] = alpha / num_comparisons

        print(f"[Statistical Analyzer] Performed {num_comparisons} pairwise comparisons")
        print(f"[Statistical Analyzer] Bonferroni-corrected α = {results['bonferroni_corrected_alpha']:.4f}")

        return results

    def _compare_two_systems(
        self,
        system_a_name: str,
        system_b_name: str,
        metrics_a: Dict[str, float],
        metrics_b: Dict[str, float],
        alpha: float
    ) -> Dict[str, Any]:
        """
        Compare two systems across all metrics

        Args:
            system_a_name: Name of system A
            system_b_name: Name of system B
            metrics_a: Metrics for system A
            metrics_b: Metrics for system B
            alpha: Significance level

        Returns:
            Dictionary of comparison results
        """
        comparison = {
            'system_a': system_a_name,
            'system_b': system_b_name,
            'metric_tests': {}
        }

        # Compare each metric
        for metric_name in metrics_a.keys():
            if metric_name in metrics_b:
                # For simplicity, we treat each metric as a single observation
                # In real scenario, you'd have per-query scores
                value_a = metrics_a[metric_name]
                value_b = metrics_b[metric_name]

                # Simple difference test
                difference = value_a - value_b
                percent_change = (difference / value_b * 100) if value_b != 0 else 0

                comparison['metric_tests'][metric_name] = {
                    'value_a': value_a,
                    'value_b': value_b,
                    'difference': difference,
                    'percent_change': percent_change,
                    'winner': system_a_name if difference > 0 else system_b_name
                }

        return comparison

    def paired_t_test(
        self,
        scores_a: List[float],
        scores_b: List[float],
        alpha: float = None
    ) -> StatisticalTest:
        """
        Perform paired t-test

        Used when you have per-query scores for both systems.

        Args:
            scores_a: Scores from system A
            scores_b: Scores from system B (same queries)
            alpha: Significance level

        Returns:
            StatisticalTest object
        """
        if alpha is None:
            alpha = self.alpha

        # Paired t-test
        statistic, p_value = stats.ttest_rel(scores_a, scores_b)

        # Effect size (Cohen's d for paired samples)
        differences = np.array(scores_a) - np.array(scores_b)
        effect_size = np.mean(differences) / np.std(differences)

        # Confidence interval for mean difference
        ci = stats.t.interval(
            1 - alpha,
            len(differences) - 1,
            loc=np.mean(differences),
            scale=stats.sem(differences)
        )

        return StatisticalTest(
            test_name='Paired t-test',
            statistic=float(statistic),
            p_value=float(p_value),
            is_significant=p_value < alpha,
            alpha=alpha,
            effect_size=float(effect_size),
            confidence_interval=(float(ci[0]), float(ci[1]))
        )

    def independent_t_test(
        self,
        scores_a: List[float],
        scores_b: List[float],
        alpha: float = None
    ) -> StatisticalTest:
        """
        Perform independent t-test

        Used when systems are evaluated on different samples.

        Args:
            scores_a: Scores from system A
            scores_b: Scores from system B
            alpha: Significance level

        Returns:
            StatisticalTest object
        """
        if alpha is None:
            alpha = self.alpha

        # Independent t-test
        statistic, p_value = stats.ttest_ind(scores_a, scores_b)

        # Effect size (Cohen's d)
        pooled_std = np.sqrt(
            (np.std(scores_a) ** 2 + np.std(scores_b) ** 2) / 2
        )
        effect_size = (np.mean(scores_a) - np.mean(scores_b)) / pooled_std

        return StatisticalTest(
            test_name='Independent t-test',
            statistic=float(statistic),
            p_value=float(p_value),
            is_significant=p_value < alpha,
            alpha=alpha,
            effect_size=float(effect_size)
        )

    def confidence_interval(
        self,
        scores: List[float],
        confidence: float = 0.95
    ) -> Tuple[float, float]:
        """
        Compute confidence interval for mean

        Args:
            scores: List of scores
            confidence: Confidence level (0.95 = 95% CI)

        Returns:
            Tuple of (lower_bound, upper_bound)
        """
        mean = np.mean(scores)
        sem = stats.sem(scores)
        ci = stats.t.interval(
            confidence,
            len(scores) - 1,
            loc=mean,
            scale=sem
        )

        return (float(ci[0]), float(ci[1]))

    def cohens_d(
        self,
        scores_a: List[float],
        scores_b: List[float]
    ) -> float:
        """
        Compute Cohen's d effect size

        Interpretation:
        - Small effect: |d| ≈ 0.2
        - Medium effect: |d| ≈ 0.5
        - Large effect: |d| ≈ 0.8

        Args:
            scores_a: Scores from system A
            scores_b: Scores from system B

        Returns:
            Cohen's d effect size
        """
        pooled_std = np.sqrt(
            (np.std(scores_a) ** 2 + np.std(scores_b) ** 2) / 2
        )

        if pooled_std == 0:
            return 0.0

        d = (np.mean(scores_a) - np.mean(scores_b)) / pooled_std
        return float(d)

    def interpret_effect_size(self, d: float) -> str:
        """
        Interpret Cohen's d effect size

        Args:
            d: Cohen's d value

        Returns:
            Interpretation string
        """
        abs_d = abs(d)

        if abs_d < 0.2:
            return "negligible"
        elif abs_d < 0.5:
            return "small"
        elif abs_d < 0.8:
            return "medium"
        else:
            return "large"

    def wilcoxon_test(
        self,
        scores_a: List[float],
        scores_b: List[float],
        alpha: float = None
    ) -> StatisticalTest:
        """
        Perform Wilcoxon signed-rank test (non-parametric alternative to t-test)

        Use this when data is not normally distributed.

        Args:
            scores_a: Scores from system A
            scores_b: Scores from system B
            alpha: Significance level

        Returns:
            StatisticalTest object
        """
        if alpha is None:
            alpha = self.alpha

        # Wilcoxon test
        statistic, p_value = stats.wilcoxon(scores_a, scores_b)

        return StatisticalTest(
            test_name='Wilcoxon signed-rank test',
            statistic=float(statistic),
            p_value=float(p_value),
            is_significant=p_value < alpha,
            alpha=alpha
        )

    def bootstrap_confidence_interval(
        self,
        scores: List[float],
        n_bootstrap: int = 10000,
        confidence: float = 0.95
    ) -> Tuple[float, float]:
        """
        Compute bootstrap confidence interval

        More robust than parametric CI, especially for small samples.

        Args:
            scores: List of scores
            n_bootstrap: Number of bootstrap samples
            confidence: Confidence level

        Returns:
            Tuple of (lower_bound, upper_bound)
        """
        bootstrap_means = []

        for _ in range(n_bootstrap):
            sample = np.random.choice(scores, size=len(scores), replace=True)
            bootstrap_means.append(np.mean(sample))

        lower_percentile = (1 - confidence) / 2 * 100
        upper_percentile = (1 + confidence) / 2 * 100

        ci_lower = np.percentile(bootstrap_means, lower_percentile)
        ci_upper = np.percentile(bootstrap_means, upper_percentile)

        return (float(ci_lower), float(ci_upper))


def format_p_value(p_value: float) -> str:
    """
    Format p-value for publication

    Args:
        p_value: P-value

    Returns:
        Formatted string (e.g., "p < 0.001" or "p = 0.042")
    """
    if p_value < 0.001:
        return "p < 0.001"
    elif p_value < 0.01:
        return f"p < 0.01"
    elif p_value < 0.05:
        return f"p < 0.05"
    else:
        return f"p = {p_value:.3f}"


def format_confidence_interval(ci: Tuple[float, float], precision: int = 3) -> str:
    """
    Format confidence interval for publication

    Args:
        ci: Tuple of (lower, upper)
        precision: Decimal precision

    Returns:
        Formatted string (e.g., "95% CI: [0.823, 0.891]")
    """
    return f"[{ci[0]:.{precision}f}, {ci[1]:.{precision}f}]"


if __name__ == "__main__":
    print("Statistical Analysis Module")
    print("=" * 60)

    analyzer = StatisticalAnalyzer(alpha=0.05)

    # Example: Compare two systems
    print("\nExample: Comparing System A vs System B")

    # Simulate per-query scores
    np.random.seed(42)
    scores_a = np.random.normal(0.85, 0.05, 100)  # System A: mean=0.85
    scores_b = np.random.normal(0.78, 0.06, 100)  # System B: mean=0.78

    print(f"\nSystem A: mean = {np.mean(scores_a):.3f}, std = {np.std(scores_a):.3f}")
    print(f"System B: mean = {np.mean(scores_b):.3f}, std = {np.std(scores_b):.3f}")

    # Paired t-test
    result = analyzer.paired_t_test(scores_a, scores_b)

    print(f"\nPaired t-test:")
    print(f"  t-statistic = {result.statistic:.3f}")
    print(f"  {format_p_value(result.p_value)}")
    print(f"  Significant? {result.is_significant} (α = {result.alpha})")
    print(f"  Effect size (Cohen's d) = {result.effect_size:.3f} ({analyzer.interpret_effect_size(result.effect_size)})")
    print(f"  95% CI for difference: {format_confidence_interval(result.confidence_interval)}")

    # Confidence intervals
    ci_a = analyzer.confidence_interval(scores_a)
    ci_b = analyzer.confidence_interval(scores_b)

    print(f"\nConfidence Intervals:")
    print(f"  System A: 95% CI = {format_confidence_interval(ci_a)}")
    print(f"  System B: 95% CI = {format_confidence_interval(ci_b)}")

    print("\nInterpretation for Paper:")
    print(f"  'System A significantly outperformed System B (t=9.XX, {format_p_value(result.p_value)})'")
    print(f"  'The effect size was {analyzer.interpret_effect_size(result.effect_size)} (d={result.effect_size:.2f})'")
