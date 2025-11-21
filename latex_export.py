"""
LaTeX Table Export for Research Papers
=======================================

Generates publication-ready LaTeX tables for direct inclusion in papers:
- System comparison tables
- Ablation study tables
- Statistical significance tables
- Detailed results tables

All tables formatted according to journal standards (ACL, ACM, IEEE, etc.)
"""

from typing import Dict, List, Any, Optional
from pathlib import Path
import numpy as np


class LaTeXExporter:
    """
    Exporter for creating LaTeX tables from evaluation results

    Generates camera-ready tables following journal formatting standards.
    """

    def __init__(self, output_dir: str = "./latex_tables"):
        """
        Initialize LaTeX exporter

        Args:
            output_dir: Directory to save LaTeX tables
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        print(f"[LaTeX Exporter] Initialized (output_dir={output_dir})")

    def export_system_comparison(
        self,
        results: Dict[str, Dict[str, float]],
        metrics: List[str],
        caption: str = "System Performance Comparison",
        label: str = "tab:system_comparison",
        filename: str = "system_comparison.tex"
    ):
        """
        Export system comparison table

        Args:
            results: Dictionary mapping system names to metrics
            metrics: List of metric names to include
            caption: Table caption
            label: LaTeX label for referencing
            filename: Output filename
        """
        systems = list(results.keys())

        # Start table
        latex = []
        latex.append("\\begin{table}[t]")
        latex.append("\\centering")
        latex.append("\\small")

        # Column specification
        n_cols = len(metrics) + 1
        col_spec = "l" + "c" * len(metrics)
        latex.append(f"\\begin{{tabular}}{{{col_spec}}}")
        latex.append("\\toprule")

        # Header row
        header = "System & " + " & ".join(metrics) + " \\\\"
        latex.append(header)
        latex.append("\\midrule")

        # Data rows
        for system in systems:
            row_data = [system]
            for metric in metrics:
                value = results[system].get(metric, 0.0)
                row_data.append(f"{value:.3f}")

            row = " & ".join(row_data) + " \\\\"
            latex.append(row)

        # Find and bold best scores
        latex = self._bold_best_scores(latex, results, metrics, systems)

        latex.append("\\bottomrule")
        latex.append("\\end{tabular}")
        latex.append(f"\\caption{{{caption}}}")
        latex.append(f"\\label{{{label}}}")
        latex.append("\\end{table}")

        # Save
        self._save_latex(latex, filename)

    def export_ablation_table(
        self,
        ablation_results: Dict[str, float],
        baseline_score: float,
        caption: str = "Ablation Study Results",
        label: str = "tab:ablation",
        filename: str = "ablation_table.tex"
    ):
        """
        Export ablation study table

        Args:
            ablation_results: Dictionary mapping configuration names to scores
            baseline_score: Score of full system
            caption: Table caption
            label: LaTeX label
            filename: Output filename
        """
        # Sort by performance drop
        configs = list(ablation_results.keys())
        scores = [ablation_results[c] for c in configs]
        drops = [baseline_score - s for s in scores]

        # Sort by drop (highest first)
        sorted_indices = np.argsort(drops)[::-1]
        configs = [configs[i] for i in sorted_indices]
        scores = [scores[i] for i in sorted_indices]
        drops = [drops[i] for i in sorted_indices]

        # Start table
        latex = []
        latex.append("\\begin{table}[t]")
        latex.append("\\centering")
        latex.append("\\small")
        latex.append("\\begin{tabular}{lccr}")
        latex.append("\\toprule")
        latex.append("Configuration & Score & Drop & \\% Drop \\\\")
        latex.append("\\midrule")

        # Full system row
        latex.append(f"Full System & {baseline_score:.3f} & -- & -- \\\\")
        latex.append("\\midrule")

        # Ablation rows
        for config, score, drop in zip(configs, scores, drops):
            pct_drop = (drop / baseline_score * 100) if baseline_score > 0 else 0
            latex.append(f"{config} & {score:.3f} & {drop:.3f} & {pct_drop:.1f}\\% \\\\")

        latex.append("\\bottomrule")
        latex.append("\\end{tabular}")
        latex.append(f"\\caption{{{caption}}}")
        latex.append(f"\\label{{{label}}}")
        latex.append("\\end{table}")

        # Save
        self._save_latex(latex, filename)

    def export_significance_table(
        self,
        comparisons: List[tuple],
        caption: str = "Statistical Significance Tests",
        label: str = "tab:significance",
        filename: str = "significance_table.tex"
    ):
        """
        Export statistical significance table

        Args:
            comparisons: List of (system_a, system_b, p_value, statistic, effect_size)
            caption: Table caption
            label: LaTeX label
            filename: Output filename
        """
        latex = []
        latex.append("\\begin{table}[t]")
        latex.append("\\centering")
        latex.append("\\small")
        latex.append("\\begin{tabular}{llccl}")
        latex.append("\\toprule")
        latex.append("System A & System B & $t$-statistic & $p$-value & Sig. \\\\")
        latex.append("\\midrule")

        for comparison in comparisons:
            sys_a, sys_b, p_value, statistic, effect_size = comparison

            # Format p-value
            if p_value < 0.001:
                p_str = "$<$ 0.001"
                sig = "***"
            elif p_value < 0.01:
                p_str = f"{p_value:.3f}"
                sig = "**"
            elif p_value < 0.05:
                p_str = f"{p_value:.3f}"
                sig = "*"
            else:
                p_str = f"{p_value:.3f}"
                sig = "ns"

            latex.append(f"{sys_a} & {sys_b} & {statistic:.2f} & {p_str} & {sig} \\\\")

        latex.append("\\bottomrule")
        latex.append("\\end{tabular}")
        latex.append(f"\\caption{{{caption}}}")
        latex.append(f"\\label{{{label}}}")
        latex.append("\\end{table}")

        # Add footnote explaining significance markers
        latex.append("\\begin{tablenotes}")
        latex.append("\\small")
        latex.append("\\item Note: *** $p < 0.001$, ** $p < 0.01$, * $p < 0.05$, ns = not significant")
        latex.append("\\end{tablenotes}")

        # Save
        self._save_latex(latex, filename)

    def export_detailed_results(
        self,
        results: Dict[str, Dict[str, float]],
        metric_groups: Dict[str, List[str]],
        caption: str = "Detailed Evaluation Results",
        label: str = "tab:detailed_results",
        filename: str = "detailed_results.tex"
    ):
        """
        Export detailed results table with metric groups

        Args:
            results: Dictionary mapping system names to metrics
            metric_groups: Dictionary grouping metrics by category
            caption: Table caption
            label: LaTeX label
            filename: Output filename
        """
        systems = list(results.keys())

        latex = []
        latex.append("\\begin{table*}[t]")  # Two-column table
        latex.append("\\centering")
        latex.append("\\small")

        # Build column specification
        all_metrics = []
        for metrics in metric_groups.values():
            all_metrics.extend(metrics)

        col_spec = "l" + "c" * len(all_metrics)
        latex.append(f"\\begin{{tabular}}{{{col_spec}}}")
        latex.append("\\toprule")

        # Multi-row header
        # First row: metric groups
        header1_parts = ["\\multirow{2}{*}{System}"]
        for group_name, metrics in metric_groups.items():
            header1_parts.append(f"\\multicolumn{{{len(metrics)}}}{{c}}{{{group_name}}}")
        latex.append(" & ".join(header1_parts) + " \\\\")

        # Second row: individual metrics
        latex.append("\\cmidrule(lr){2-" + str(len(all_metrics) + 1) + "}")
        header2_parts = [""]
        for metrics in metric_groups.values():
            header2_parts.extend(metrics)
        latex.append(" & ".join(header2_parts) + " \\\\")

        latex.append("\\midrule")

        # Data rows
        for system in systems:
            row_data = [system]
            for metric in all_metrics:
                value = results[system].get(metric, 0.0)
                row_data.append(f"{value:.3f}")

            latex.append(" & ".join(row_data) + " \\\\")

        latex.append("\\bottomrule")
        latex.append("\\end{tabular}")
        latex.append(f"\\caption{{{caption}}}")
        latex.append(f"\\label{{{label}}}")
        latex.append("\\end{table*}")

        # Save
        self._save_latex(latex, filename)

    def export_query_type_breakdown(
        self,
        results: Dict[str, Dict[str, Dict[str, float]]],
        query_types: List[str],
        metric: str = "F1",
        caption: str = "Performance by Query Type",
        label: str = "tab:query_types",
        filename: str = "query_type_table.tex"
    ):
        """
        Export query type breakdown table

        Args:
            results: Dictionary mapping systems to query types to metrics
            query_types: List of query type names
            metric: Metric to display
            caption: Table caption
            label: LaTeX label
            filename: Output filename
        """
        systems = list(results.keys())

        latex = []
        latex.append("\\begin{table}[t]")
        latex.append("\\centering")
        latex.append("\\small")

        col_spec = "l" + "c" * len(query_types) + "c"
        latex.append(f"\\begin{{tabular}}{{{col_spec}}}")
        latex.append("\\toprule")

        # Header
        header = "System & " + " & ".join(query_types) + " & Avg \\\\"
        latex.append(header)
        latex.append("\\midrule")

        # Data rows
        for system in systems:
            row_data = [system]

            scores = []
            for qtype in query_types:
                score = results[system].get(qtype, {}).get(metric, 0.0)
                scores.append(score)
                row_data.append(f"{score:.3f}")

            # Average
            avg_score = np.mean(scores) if scores else 0.0
            row_data.append(f"\\textbf{{{avg_score:.3f}}}")

            latex.append(" & ".join(row_data) + " \\\\")

        latex.append("\\bottomrule")
        latex.append("\\end{tabular}")
        latex.append(f"\\caption{{{caption}}}")
        latex.append(f"\\label{{{label}}}")
        latex.append("\\end{table}")

        # Save
        self._save_latex(latex, filename)

    def export_efficiency_table(
        self,
        systems_data: Dict[str, Dict[str, Any]],
        caption: str = "Efficiency Comparison",
        label: str = "tab:efficiency",
        filename: str = "efficiency_table.tex"
    ):
        """
        Export efficiency comparison table

        Args:
            systems_data: Dictionary with latency, tokens, cost per system
            caption: Table caption
            label: LaTeX label
            filename: Output filename
        """
        systems = list(systems_data.keys())

        latex = []
        latex.append("\\begin{table}[t]")
        latex.append("\\centering")
        latex.append("\\small")
        latex.append("\\begin{tabular}{lcccc}")
        latex.append("\\toprule")
        latex.append("System & Latency (ms) & Tokens & Cost (\\$) & Score \\\\")
        latex.append("\\midrule")

        for system in systems:
            data = systems_data[system]
            latency = data.get('latency_ms', 0)
            tokens = data.get('tokens_used', 0)
            cost = data.get('cost_usd', 0)
            score = data.get('score', 0)

            latex.append(f"{system} & {latency:.0f} & {tokens:,} & {cost:.4f} & {score:.3f} \\\\")

        latex.append("\\bottomrule")
        latex.append("\\end{tabular}")
        latex.append(f"\\caption{{{caption}}}")
        latex.append(f"\\label{{{label}}}")
        latex.append("\\end{table}")

        # Save
        self._save_latex(latex, filename)

    def export_complete_results_appendix(
        self,
        all_results: Dict[str, Any],
        filename: str = "appendix_results.tex"
    ):
        """
        Export comprehensive results for appendix

        Args:
            all_results: Complete results dictionary
            filename: Output filename
        """
        latex = []
        latex.append("\\section{Complete Evaluation Results}")
        latex.append("\\label{sec:appendix_results}")
        latex.append("")

        # Add all tables
        latex.append("This appendix contains complete evaluation results including:")
        latex.append("\\begin{itemize}")
        latex.append("\\item System comparison across all metrics")
        latex.append("\\item Ablation study results")
        latex.append("\\item Statistical significance tests")
        latex.append("\\item Performance breakdown by query type")
        latex.append("\\item Efficiency analysis")
        latex.append("\\end{itemize}")

        # Save
        self._save_latex(latex, filename)

    def _bold_best_scores(
        self,
        latex: List[str],
        results: Dict[str, Dict[str, float]],
        metrics: List[str],
        systems: List[str]
    ) -> List[str]:
        """
        Bold the best score in each column

        Args:
            latex: LaTeX lines
            results: Results dictionary
            metrics: List of metrics
            systems: List of systems

        Returns:
            Modified LaTeX lines with bolded best scores
        """
        # Find best scores for each metric
        best_scores = {}
        for metric in metrics:
            scores = [results[sys].get(metric, 0.0) for sys in systems]
            best_scores[metric] = max(scores)

        # Update LaTeX lines
        modified_latex = []
        for line in latex:
            if any(sys in line for sys in systems):
                # This is a data row
                for metric in metrics:
                    best = best_scores[metric]
                    # Replace best score with bolded version
                    line = line.replace(f"{best:.3f}", f"\\textbf{{{best:.3f}}}")

            modified_latex.append(line)

        return modified_latex

    def _save_latex(self, latex: List[str], filename: str):
        """
        Save LaTeX content to file

        Args:
            latex: List of LaTeX lines
            filename: Output filename
        """
        output_path = self.output_dir / filename
        content = "\n".join(latex)

        with open(output_path, 'w') as f:
            f.write(content)

        print(f"[LaTeX Exporter] Saved: {output_path}")

    def generate_all_tables(
        self,
        evaluation_results: Dict[str, Any],
        prefix: str = ""
    ):
        """
        Generate all standard tables from evaluation results

        Args:
            evaluation_results: Complete evaluation results
            prefix: Optional prefix for filenames
        """
        print(f"\n[LaTeX Exporter] Generating all tables...")

        # Extract data
        system_results = evaluation_results.get('system_results', {})
        ablation_results = evaluation_results.get('ablation_results', {})
        significance_tests = evaluation_results.get('significance_tests', [])
        query_type_results = evaluation_results.get('query_type_results', {})
        efficiency_data = evaluation_results.get('efficiency', {})

        # Generate tables
        if system_results:
            metrics = ['precision', 'recall', 'f1', 'ndcg']
            self.export_system_comparison(
                system_results,
                metrics,
                filename=f"{prefix}system_comparison.tex"
            )

        if ablation_results:
            baseline_score = ablation_results.get('Full System', 0.0)
            self.export_ablation_table(
                ablation_results,
                baseline_score,
                filename=f"{prefix}ablation_table.tex"
            )

        if significance_tests:
            self.export_significance_table(
                significance_tests,
                filename=f"{prefix}significance_table.tex"
            )

        if query_type_results:
            query_types = list(next(iter(query_type_results.values())).keys())
            self.export_query_type_breakdown(
                query_type_results,
                query_types,
                filename=f"{prefix}query_type_table.tex"
            )

        if efficiency_data:
            self.export_efficiency_table(
                efficiency_data,
                filename=f"{prefix}efficiency_table.tex"
            )

        print(f"[LaTeX Exporter] All tables generated!")


if __name__ == "__main__":
    print("LaTeX Table Exporter")
    print("=" * 60)
    print("\nGenerates publication-ready LaTeX tables:")
    print("1. System Comparison Table")
    print("2. Ablation Study Table")
    print("3. Statistical Significance Table")
    print("4. Query Type Breakdown Table")
    print("5. Efficiency Comparison Table")
    print("6. Detailed Results Table")
    print("\nUsage:")
    print("  exporter = LaTeXExporter(output_dir='./latex_tables')")
    print("  exporter.generate_all_tables(evaluation_results)")
    print("\nAll tables use standard journal formatting (booktabs style)")
