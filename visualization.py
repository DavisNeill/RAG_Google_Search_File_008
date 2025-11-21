"""
Visualization Tools for Research Publications
==============================================

Generates publication-quality plots and figures for research papers:
- System comparison plots
- Ablation study visualizations
- Performance analysis
- Statistical significance plots
- Error analysis visualizations

Uses matplotlib and seaborn for clean, professional figures suitable for
journal and conference publications.
"""

import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from typing import Dict, List, Any, Tuple, Optional
import pandas as pd
from pathlib import Path


# Set publication-quality defaults
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.size'] = 10
plt.rcParams['axes.labelsize'] = 11
plt.rcParams['axes.titlesize'] = 12
plt.rcParams['xtick.labelsize'] = 9
plt.rcParams['ytick.labelsize'] = 9
plt.rcParams['legend.fontsize'] = 9
plt.rcParams['figure.titlesize'] = 13

# Color scheme for consistency
COLORS = {
    'primary': '#2E86AB',
    'secondary': '#A23B72',
    'tertiary': '#F18F01',
    'quaternary': '#C73E1D',
    'success': '#06A77D',
    'neutral': '#5C6B73'
}


class PaperVisualizer:
    """
    Visualizer for creating publication-quality figures

    All plots are designed to meet journal standards (Nature, IEEE, ACM, etc.)
    """

    def __init__(self, output_dir: str = "./figures", style: str = "seaborn-v0_8-paper"):
        """
        Initialize visualizer

        Args:
            output_dir: Directory to save figures
            style: Matplotlib style to use
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Set style
        try:
            plt.style.use(style)
        except:
            plt.style.use('seaborn-v0_8')

        print(f"[Paper Visualizer] Initialized (output_dir={output_dir})")

    def plot_system_comparison(
        self,
        results: Dict[str, Dict[str, float]],
        metric_name: str = "F1 Score",
        title: str = "System Performance Comparison",
        filename: str = "system_comparison.pdf"
    ):
        """
        Create bar chart comparing multiple systems

        Args:
            results: Dictionary mapping system names to metrics
            metric_name: Name of metric to visualize
            title: Plot title
            filename: Output filename
        """
        # Prepare data
        systems = list(results.keys())
        scores = [results[sys].get(metric_name, 0.0) for sys in systems]

        # Create figure
        fig, ax = plt.subplots(figsize=(8, 5))

        # Create bar chart
        bars = ax.bar(range(len(systems)), scores, color=COLORS['primary'], alpha=0.8)

        # Highlight best system
        best_idx = np.argmax(scores)
        bars[best_idx].set_color(COLORS['success'])

        # Customize
        ax.set_xlabel('System')
        ax.set_ylabel(metric_name)
        ax.set_title(title)
        ax.set_xticks(range(len(systems)))
        ax.set_xticklabels(systems, rotation=45, ha='right')

        # Add value labels on bars
        for i, (bar, score) in enumerate(zip(bars, scores)):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{score:.3f}',
                   ha='center', va='bottom', fontsize=8)

        # Add grid
        ax.yaxis.grid(True, alpha=0.3)
        ax.set_axisbelow(True)

        plt.tight_layout()

        # Save
        output_path = self.output_dir / filename
        plt.savefig(output_path, bbox_inches='tight')
        print(f"[Paper Visualizer] Saved: {output_path}")

        plt.close()

    def plot_metric_comparison(
        self,
        results: Dict[str, Dict[str, float]],
        metrics: List[str],
        title: str = "Multi-Metric Comparison",
        filename: str = "metric_comparison.pdf"
    ):
        """
        Create grouped bar chart comparing systems across multiple metrics

        Args:
            results: Dictionary mapping system names to metrics
            metrics: List of metric names to compare
            title: Plot title
            filename: Output filename
        """
        # Prepare data
        systems = list(results.keys())
        data = []

        for metric in metrics:
            for system in systems:
                data.append({
                    'System': system,
                    'Metric': metric,
                    'Score': results[system].get(metric, 0.0)
                })

        df = pd.DataFrame(data)

        # Create figure
        fig, ax = plt.subplots(figsize=(10, 6))

        # Create grouped bar chart
        x = np.arange(len(systems))
        width = 0.8 / len(metrics)

        for i, metric in enumerate(metrics):
            metric_data = df[df['Metric'] == metric]
            offset = (i - len(metrics)/2 + 0.5) * width
            ax.bar(x + offset, metric_data['Score'], width,
                  label=metric, alpha=0.8)

        # Customize
        ax.set_xlabel('System')
        ax.set_ylabel('Score')
        ax.set_title(title)
        ax.set_xticks(x)
        ax.set_xticklabels(systems, rotation=45, ha='right')
        ax.legend(loc='upper left', bbox_to_anchor=(1, 1))
        ax.yaxis.grid(True, alpha=0.3)
        ax.set_axisbelow(True)

        plt.tight_layout()

        # Save
        output_path = self.output_dir / filename
        plt.savefig(output_path, bbox_inches='tight')
        print(f"[Paper Visualizer] Saved: {output_path}")

        plt.close()

    def plot_ablation_study(
        self,
        ablation_results: Dict[str, float],
        baseline_score: float,
        title: str = "Ablation Study Results",
        filename: str = "ablation_study.pdf"
    ):
        """
        Visualize ablation study results showing component contributions

        Args:
            ablation_results: Dictionary mapping ablation names to scores
            baseline_score: Score of full system
            title: Plot title
            filename: Output filename
        """
        # Prepare data
        configs = list(ablation_results.keys())
        scores = list(ablation_results.values())
        drops = [baseline_score - score for score in scores]

        # Sort by drop (highest impact first)
        sorted_indices = np.argsort(drops)[::-1]
        configs = [configs[i] for i in sorted_indices]
        scores = [scores[i] for i in sorted_indices]
        drops = [drops[i] for i in sorted_indices]

        # Create figure with two subplots
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

        # Plot 1: Scores
        bars1 = ax1.barh(range(len(configs)), scores, color=COLORS['primary'], alpha=0.8)
        ax1.axvline(baseline_score, color=COLORS['success'], linestyle='--',
                   linewidth=2, label='Full System', alpha=0.7)

        ax1.set_xlabel('Score')
        ax1.set_ylabel('Configuration')
        ax1.set_title('Performance After Ablation')
        ax1.set_yticks(range(len(configs)))
        ax1.set_yticklabels(configs)
        ax1.legend()
        ax1.xaxis.grid(True, alpha=0.3)

        # Plot 2: Performance drop
        colors = [COLORS['quaternary'] if d > 0.05 else COLORS['secondary'] for d in drops]
        bars2 = ax2.barh(range(len(configs)), drops, color=colors, alpha=0.8)

        ax2.set_xlabel('Performance Drop')
        ax2.set_ylabel('')
        ax2.set_title('Component Contribution')
        ax2.set_yticks(range(len(configs)))
        ax2.set_yticklabels([''] * len(configs))  # No labels (shared with left plot)
        ax2.xaxis.grid(True, alpha=0.3)

        # Add value labels
        for i, (bar, drop) in enumerate(zip(bars2, drops)):
            width = bar.get_width()
            ax2.text(width, bar.get_y() + bar.get_height()/2.,
                    f'{drop:.3f}',
                    ha='left', va='center', fontsize=8)

        plt.suptitle(title, fontsize=13, y=1.02)
        plt.tight_layout()

        # Save
        output_path = self.output_dir / filename
        plt.savefig(output_path, bbox_inches='tight')
        print(f"[Paper Visualizer] Saved: {output_path}")

        plt.close()

    def plot_performance_vs_latency(
        self,
        systems_data: Dict[str, Tuple[float, float]],
        title: str = "Performance vs Latency Trade-off",
        filename: str = "performance_latency.pdf"
    ):
        """
        Create scatter plot showing performance vs latency trade-off

        Args:
            systems_data: Dictionary mapping system names to (score, latency_ms)
            title: Plot title
            filename: Output filename
        """
        # Prepare data
        systems = list(systems_data.keys())
        scores = [systems_data[sys][0] for sys in systems]
        latencies = [systems_data[sys][1] for sys in systems]

        # Create figure
        fig, ax = plt.subplots(figsize=(8, 6))

        # Create scatter plot
        scatter = ax.scatter(latencies, scores, s=200, alpha=0.6,
                           c=range(len(systems)), cmap='viridis')

        # Add labels for each point
        for i, system in enumerate(systems):
            ax.annotate(system, (latencies[i], scores[i]),
                       xytext=(5, 5), textcoords='offset points',
                       fontsize=8, alpha=0.8)

        # Customize
        ax.set_xlabel('Latency (ms)')
        ax.set_ylabel('Performance Score')
        ax.set_title(title)
        ax.grid(True, alpha=0.3)

        # Add quadrant lines
        median_score = np.median(scores)
        median_latency = np.median(latencies)
        ax.axhline(median_score, color='gray', linestyle='--', alpha=0.3)
        ax.axvline(median_latency, color='gray', linestyle='--', alpha=0.3)

        # Annotate best region (high score, low latency)
        ax.text(0.05, 0.95, 'Ideal Region\n(High Score, Low Latency)',
               transform=ax.transAxes, fontsize=8, va='top',
               bbox=dict(boxstyle='round', facecolor='green', alpha=0.1))

        plt.tight_layout()

        # Save
        output_path = self.output_dir / filename
        plt.savefig(output_path, bbox_inches='tight')
        print(f"[Paper Visualizer] Saved: {output_path}")

        plt.close()

    def plot_query_type_analysis(
        self,
        query_type_results: Dict[str, Dict[str, float]],
        title: str = "Performance by Query Type",
        filename: str = "query_type_analysis.pdf"
    ):
        """
        Visualize performance breakdown by query type

        Args:
            query_type_results: Dictionary mapping query types to system scores
            title: Plot title
            filename: Output filename
        """
        # Prepare data
        query_types = list(query_type_results.keys())
        systems = list(query_type_results[query_types[0]].keys())

        data = []
        for qtype in query_types:
            for system in systems:
                data.append({
                    'Query Type': qtype,
                    'System': system,
                    'Score': query_type_results[qtype].get(system, 0.0)
                })

        df = pd.DataFrame(data)

        # Create figure
        fig, ax = plt.subplots(figsize=(10, 6))

        # Create grouped bar chart
        x = np.arange(len(query_types))
        width = 0.8 / len(systems)

        for i, system in enumerate(systems):
            system_data = df[df['System'] == system]
            offset = (i - len(systems)/2 + 0.5) * width
            ax.bar(x + offset, system_data['Score'], width,
                  label=system, alpha=0.8)

        # Customize
        ax.set_xlabel('Query Type')
        ax.set_ylabel('Score')
        ax.set_title(title)
        ax.set_xticks(x)
        ax.set_xticklabels(query_types, rotation=45, ha='right')
        ax.legend(loc='best')
        ax.yaxis.grid(True, alpha=0.3)
        ax.set_axisbelow(True)

        plt.tight_layout()

        # Save
        output_path = self.output_dir / filename
        plt.savefig(output_path, bbox_inches='tight')
        print(f"[Paper Visualizer] Saved: {output_path}")

        plt.close()

    def plot_statistical_significance(
        self,
        comparisons: List[Tuple[str, str, float, bool]],
        title: str = "Statistical Significance Tests",
        filename: str = "statistical_significance.pdf"
    ):
        """
        Visualize statistical significance of pairwise comparisons

        Args:
            comparisons: List of (system_a, system_b, p_value, is_significant)
            title: Plot title
            filename: Output filename
        """
        # Prepare data
        comparison_labels = [f"{a} vs {b}" for a, b, _, _ in comparisons]
        p_values = [p for _, _, p, _ in comparisons]
        significant = [sig for _, _, _, sig in comparisons]

        # Create figure
        fig, ax = plt.subplots(figsize=(10, 6))

        # Create bar chart
        colors = [COLORS['success'] if sig else COLORS['neutral']
                 for sig in significant]
        bars = ax.barh(range(len(comparison_labels)), p_values,
                      color=colors, alpha=0.8)

        # Add significance threshold line
        ax.axvline(0.05, color=COLORS['quaternary'], linestyle='--',
                  linewidth=2, label='α = 0.05', alpha=0.7)
        ax.axvline(0.01, color=COLORS['quaternary'], linestyle=':',
                  linewidth=2, label='α = 0.01', alpha=0.7)

        # Customize
        ax.set_xlabel('p-value')
        ax.set_ylabel('Comparison')
        ax.set_title(title)
        ax.set_yticks(range(len(comparison_labels)))
        ax.set_yticklabels(comparison_labels)
        ax.legend()
        ax.set_xlim(0, max(0.1, max(p_values) * 1.1))
        ax.xaxis.grid(True, alpha=0.3)

        # Add significance markers
        for i, (bar, sig) in enumerate(zip(bars, significant)):
            marker = '***' if sig else 'ns'
            ax.text(bar.get_width(), bar.get_y() + bar.get_height()/2.,
                   f' {marker}',
                   ha='left', va='center', fontsize=8,
                   fontweight='bold' if sig else 'normal')

        plt.tight_layout()

        # Save
        output_path = self.output_dir / filename
        plt.savefig(output_path, bbox_inches='tight')
        print(f"[Paper Visualizer] Saved: {output_path}")

        plt.close()

    def plot_score_distribution(
        self,
        system_scores: Dict[str, List[float]],
        title: str = "Score Distribution Across Systems",
        filename: str = "score_distribution.pdf"
    ):
        """
        Create violin plot showing score distributions

        Args:
            system_scores: Dictionary mapping system names to list of scores
            title: Plot title
            filename: Output filename
        """
        # Prepare data
        data = []
        for system, scores in system_scores.items():
            for score in scores:
                data.append({'System': system, 'Score': score})

        df = pd.DataFrame(data)

        # Create figure
        fig, ax = plt.subplots(figsize=(10, 6))

        # Create violin plot
        sns.violinplot(data=df, x='System', y='Score', ax=ax, palette='Set2')

        # Add box plot overlay
        sns.boxplot(data=df, x='System', y='Score', ax=ax,
                   width=0.3, palette='Set2', showcaps=False,
                   boxprops={'alpha': 0.5}, showfliers=False)

        # Customize
        ax.set_xlabel('System')
        ax.set_ylabel('Score')
        ax.set_title(title)
        ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right')
        ax.yaxis.grid(True, alpha=0.3)
        ax.set_axisbelow(True)

        plt.tight_layout()

        # Save
        output_path = self.output_dir / filename
        plt.savefig(output_path, bbox_inches='tight')
        print(f"[Paper Visualizer] Saved: {output_path}")

        plt.close()

    def plot_confusion_matrix(
        self,
        confusion_matrix: np.ndarray,
        labels: List[str],
        title: str = "Confusion Matrix",
        filename: str = "confusion_matrix.pdf"
    ):
        """
        Plot confusion matrix heatmap

        Args:
            confusion_matrix: Confusion matrix as numpy array
            labels: Class labels
            title: Plot title
            filename: Output filename
        """
        # Create figure
        fig, ax = plt.subplots(figsize=(8, 7))

        # Create heatmap
        sns.heatmap(confusion_matrix, annot=True, fmt='d', cmap='Blues',
                   xticklabels=labels, yticklabels=labels, ax=ax,
                   cbar_kws={'label': 'Count'})

        # Customize
        ax.set_xlabel('Predicted')
        ax.set_ylabel('Actual')
        ax.set_title(title)

        plt.tight_layout()

        # Save
        output_path = self.output_dir / filename
        plt.savefig(output_path, bbox_inches='tight')
        print(f"[Paper Visualizer] Saved: {output_path}")

        plt.close()

    def create_paper_figure(
        self,
        subplots_data: List[Dict[str, Any]],
        layout: Tuple[int, int],
        title: str = "Multi-Panel Figure",
        filename: str = "paper_figure.pdf",
        figsize: Tuple[int, int] = (12, 8)
    ):
        """
        Create multi-panel figure for paper (e.g., Figure 1 with a, b, c panels)

        Args:
            subplots_data: List of subplot specifications
            layout: (rows, cols) for subplot layout
            title: Overall figure title
            filename: Output filename
            figsize: Figure size
        """
        fig, axes = plt.subplots(layout[0], layout[1], figsize=figsize)
        axes = axes.flatten() if isinstance(axes, np.ndarray) else [axes]

        for i, (ax, subplot_spec) in enumerate(zip(axes, subplots_data)):
            plot_type = subplot_spec.get('type', 'bar')
            data = subplot_spec.get('data', {})
            subplot_title = subplot_spec.get('title', f'Panel {chr(97+i)}')

            # Add panel label
            ax.text(-0.1, 1.05, f'({chr(97+i)})', transform=ax.transAxes,
                   fontsize=12, fontweight='bold')

            # Create subplot based on type
            if plot_type == 'bar':
                self._create_bar_subplot(ax, data, subplot_title)
            elif plot_type == 'line':
                self._create_line_subplot(ax, data, subplot_title)
            elif plot_type == 'scatter':
                self._create_scatter_subplot(ax, data, subplot_title)

        plt.suptitle(title, fontsize=14, y=0.98)
        plt.tight_layout()

        # Save
        output_path = self.output_dir / filename
        plt.savefig(output_path, bbox_inches='tight')
        print(f"[Paper Visualizer] Saved multi-panel figure: {output_path}")

        plt.close()

    def _create_bar_subplot(self, ax, data, title):
        """Helper to create bar subplot"""
        x = data.get('x', [])
        y = data.get('y', [])
        ax.bar(range(len(x)), y, color=COLORS['primary'], alpha=0.8)
        ax.set_xticks(range(len(x)))
        ax.set_xticklabels(x, rotation=45, ha='right')
        ax.set_title(title)
        ax.yaxis.grid(True, alpha=0.3)

    def _create_line_subplot(self, ax, data, title):
        """Helper to create line subplot"""
        x = data.get('x', [])
        y = data.get('y', [])
        ax.plot(x, y, marker='o', color=COLORS['primary'], linewidth=2)
        ax.set_title(title)
        ax.grid(True, alpha=0.3)

    def _create_scatter_subplot(self, ax, data, title):
        """Helper to create scatter subplot"""
        x = data.get('x', [])
        y = data.get('y', [])
        ax.scatter(x, y, s=100, alpha=0.6, color=COLORS['primary'])
        ax.set_title(title)
        ax.grid(True, alpha=0.3)


if __name__ == "__main__":
    print("Paper Visualization Tools")
    print("=" * 60)
    print("\nAvailable Visualizations:")
    print("1. System Comparison - Bar charts comparing systems")
    print("2. Ablation Study - Component contribution analysis")
    print("3. Performance vs Latency - Trade-off scatter plots")
    print("4. Query Type Analysis - Performance by query type")
    print("5. Statistical Significance - p-value visualizations")
    print("6. Score Distributions - Violin plots")
    print("7. Multi-Panel Figures - Combined visualizations")
    print("\nAll figures are publication-quality (300 DPI, PDF format)")
