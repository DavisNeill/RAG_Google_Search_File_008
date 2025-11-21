"""
Ablation Study Framework
=========================

Systematically removes components from the Agentic RAG system to measure
the contribution of each component to overall performance.

Essential for journal publication to prove that each component adds value.

Ablation experiments:
1. Remove Memory Agent
2. Remove Query Agent
3. Remove Retrieval Agent
4. Remove Response Agent
5. Remove Query Classification
6. Remove Conversation Memory
7. Remove all agents (full ablation)
"""

from typing import List, Dict, Any, Callable
from dataclasses import dataclass, field
import time
import copy


@dataclass
class AblationConfig:
    """Configuration for an ablation experiment"""
    name: str
    description: str
    components_removed: List[str]
    enabled_components: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AblationResult:
    """Result from an ablation experiment"""
    config: AblationConfig
    question: str
    answer: str
    retrieved_contexts: List[str]
    latency_ms: float
    tokens_used: int
    scores: Dict[str, float] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            'config_name': self.config.name,
            'components_removed': self.config.components_removed,
            'enabled_components': self.config.enabled_components,
            'question': self.question,
            'answer': self.answer,
            'retrieved_contexts': self.retrieved_contexts,
            'latency_ms': self.latency_ms,
            'tokens_used': self.tokens_used,
            'scores': self.scores,
            'metadata': self.metadata
        }


class AblationStudy:
    """
    Framework for conducting ablation studies

    Systematically removes components and measures performance impact.
    """

    def __init__(self, full_system):
        """
        Initialize ablation study

        Args:
            full_system: The complete Agentic RAG system
        """
        self.full_system = full_system
        self.ablation_configs = []

        print("[Ablation Study] Initialized")

    def define_standard_ablations(self):
        """
        Define standard ablation experiments for Agentic RAG

        Creates configurations that systematically remove each component.
        """
        # Full system (baseline)
        self.add_ablation(AblationConfig(
            name="Full System",
            description="Complete Agentic RAG with all components",
            components_removed=[],
            enabled_components=[
                'query_agent',
                'memory_agent',
                'retrieval_agent',
                'response_agent',
                'query_classification',
                'conversation_memory'
            ]
        ))

        # Ablation 1: Remove Memory Agent
        self.add_ablation(AblationConfig(
            name="No Memory Agent",
            description="Remove Memory Agent - no conversation context retrieval",
            components_removed=['memory_agent'],
            enabled_components=[
                'query_agent',
                'retrieval_agent',
                'response_agent',
                'query_classification',
                'conversation_memory'
            ],
            metadata={'hypothesis': 'Memory agent helps retrieve relevant conversation context'}
        ))

        # Ablation 2: Remove Query Agent
        self.add_ablation(AblationConfig(
            name="No Query Agent",
            description="Remove Query Agent - no query analysis and decomposition",
            components_removed=['query_agent'],
            enabled_components=[
                'memory_agent',
                'retrieval_agent',
                'response_agent',
                'conversation_memory'
            ],
            metadata={'hypothesis': 'Query agent improves understanding of complex queries'}
        ))

        # Ablation 3: Remove Retrieval Agent
        self.add_ablation(AblationConfig(
            name="No Retrieval Agent",
            description="Remove Retrieval Agent - use vanilla retrieval",
            components_removed=['retrieval_agent'],
            enabled_components=[
                'query_agent',
                'memory_agent',
                'response_agent',
                'query_classification',
                'conversation_memory'
            ],
            metadata={'hypothesis': 'Retrieval agent improves document selection'}
        ))

        # Ablation 4: Remove Response Agent
        self.add_ablation(AblationConfig(
            name="No Response Agent",
            description="Remove Response Agent - direct generation without synthesis",
            components_removed=['response_agent'],
            enabled_components=[
                'query_agent',
                'memory_agent',
                'retrieval_agent',
                'query_classification',
                'conversation_memory'
            ],
            metadata={'hypothesis': 'Response agent improves answer quality and coherence'}
        ))

        # Ablation 5: Remove Query Classification
        self.add_ablation(AblationConfig(
            name="No Query Classification",
            description="Remove query classification - treat all queries the same",
            components_removed=['query_classification'],
            enabled_components=[
                'query_agent',
                'memory_agent',
                'retrieval_agent',
                'response_agent',
                'conversation_memory'
            ],
            metadata={'hypothesis': 'Query classification helps tailor responses to query type'}
        ))

        # Ablation 6: Remove Conversation Memory
        self.add_ablation(AblationConfig(
            name="No Conversation Memory",
            description="Remove conversation memory - stateless queries",
            components_removed=['conversation_memory'],
            enabled_components=[
                'query_agent',
                'memory_agent',
                'retrieval_agent',
                'response_agent',
                'query_classification'
            ],
            metadata={'hypothesis': 'Conversation memory enables multi-turn interactions'}
        ))

        # Ablation 7: Remove all agents (Vanilla RAG)
        self.add_ablation(AblationConfig(
            name="No Agents (Vanilla RAG)",
            description="Remove all agents - pure retrieval + generation",
            components_removed=[
                'query_agent',
                'memory_agent',
                'retrieval_agent',
                'response_agent'
            ],
            enabled_components=[],
            metadata={'hypothesis': 'Agents collectively improve performance significantly'}
        ))

        # Ablation 8: Only retrieval (no agents, no memory)
        self.add_ablation(AblationConfig(
            name="Minimal System",
            description="Minimal system - only basic retrieval and generation",
            components_removed=[
                'query_agent',
                'memory_agent',
                'retrieval_agent',
                'response_agent',
                'query_classification',
                'conversation_memory'
            ],
            enabled_components=[],
            metadata={'hypothesis': 'Shows total contribution of all enhancements'}
        ))

        print(f"[Ablation Study] Defined {len(self.ablation_configs)} ablation experiments")

    def add_ablation(self, config: AblationConfig):
        """Add an ablation configuration"""
        self.ablation_configs.append(config)

    def run_single_ablation(
        self,
        config: AblationConfig,
        question: str,
        context: Dict[str, Any] = None
    ) -> AblationResult:
        """
        Run a single ablation experiment

        Args:
            config: Ablation configuration
            question: Question to query
            context: Optional context

        Returns:
            AblationResult
        """
        start_time = time.time()

        # Create ablated system
        ablated_system = self._create_ablated_system(config)

        # Run query
        result = ablated_system.query(question, context)

        latency_ms = (time.time() - start_time) * 1000

        return AblationResult(
            config=config,
            question=question,
            answer=result.get('answer', ''),
            retrieved_contexts=result.get('contexts', []),
            latency_ms=latency_ms,
            tokens_used=result.get('tokens_used', 0),
            metadata={
                'system_config': config.name,
                'components_active': len(config.enabled_components)
            }
        )

    def run_all_ablations(
        self,
        question: str,
        context: Dict[str, Any] = None
    ) -> List[AblationResult]:
        """
        Run all ablation experiments on a single question

        Args:
            question: Question to query
            context: Optional context

        Returns:
            List of AblationResults
        """
        results = []

        print(f"\n[Ablation Study] Running {len(self.ablation_configs)} experiments")

        for i, config in enumerate(self.ablation_configs):
            print(f"  [{i+1}/{len(self.ablation_configs)}] {config.name}...")

            result = self.run_single_ablation(config, question, context)
            results.append(result)

        return results

    def run_batch_ablations(
        self,
        questions: List[str],
        contexts: List[Dict[str, Any]] = None
    ) -> Dict[str, List[AblationResult]]:
        """
        Run all ablations on a batch of questions

        Args:
            questions: List of questions
            contexts: Optional list of contexts

        Returns:
            Dictionary mapping config name to list of results
        """
        if contexts is None:
            contexts = [None] * len(questions)

        # Initialize results dict
        results = {config.name: [] for config in self.ablation_configs}

        print(f"\n[Ablation Study] Batch evaluation")
        print(f"  Questions: {len(questions)}")
        print(f"  Ablations: {len(self.ablation_configs)}")
        print(f"  Total experiments: {len(questions) * len(self.ablation_configs)}")

        # Run each ablation on all questions
        for i, config in enumerate(self.ablation_configs):
            print(f"\n[{i+1}/{len(self.ablation_configs)}] Running: {config.name}")

            for j, (question, context) in enumerate(zip(questions, contexts)):
                if (j + 1) % 10 == 0:
                    print(f"  Progress: {j+1}/{len(questions)} questions")

                result = self.run_single_ablation(config, question, context)
                results[config.name].append(result)

        return results

    def _create_ablated_system(self, config: AblationConfig):
        """
        Create a version of the system with specified components removed

        Args:
            config: Ablation configuration

        Returns:
            Modified system instance
        """
        # Create a copy of the full system
        ablated_system = copy.deepcopy(self.full_system)

        # Disable components based on configuration
        for component in config.components_removed:
            self._disable_component(ablated_system, component)

        return ablated_system

    def _disable_component(self, system, component_name: str):
        """
        Disable a specific component in the system

        Args:
            system: System instance
            component_name: Name of component to disable
        """
        # Component-specific disabling logic
        if component_name == 'memory_agent':
            system.memory_agent = None
        elif component_name == 'query_agent':
            system.query_agent = None
        elif component_name == 'retrieval_agent':
            system.retrieval_agent = None
        elif component_name == 'response_agent':
            system.response_agent = None
        elif component_name == 'query_classification':
            system.enable_query_classification = False
        elif component_name == 'conversation_memory':
            system.conversation_memory = []
            system.enable_memory = False

    def compute_ablation_impact(
        self,
        results: Dict[str, List[AblationResult]],
        metric_name: str = 'score'
    ) -> Dict[str, Dict[str, float]]:
        """
        Compute the impact of each ablation

        Args:
            results: Results from batch ablations
            metric_name: Name of metric to analyze

        Returns:
            Dictionary with ablation impact analysis
        """
        analysis = {}

        # Get full system performance
        full_system_results = results.get("Full System", [])
        if not full_system_results:
            print("Warning: No full system results found")
            return analysis

        full_system_score = self._average_score(full_system_results, metric_name)

        # Compute impact for each ablation
        for config_name, ablation_results in results.items():
            if config_name == "Full System":
                continue

            ablation_score = self._average_score(ablation_results, metric_name)

            # Compute impact
            absolute_drop = full_system_score - ablation_score
            relative_drop = (absolute_drop / full_system_score * 100) if full_system_score > 0 else 0

            analysis[config_name] = {
                'full_system_score': full_system_score,
                'ablation_score': ablation_score,
                'absolute_drop': absolute_drop,
                'relative_drop_percent': relative_drop,
                'components_removed': len(self._get_config_by_name(config_name).components_removed)
            }

        # Sort by impact (highest drop first)
        analysis = dict(sorted(
            analysis.items(),
            key=lambda x: x[1]['absolute_drop'],
            reverse=True
        ))

        return analysis

    def _average_score(self, results: List[AblationResult], metric_name: str) -> float:
        """Compute average score from results"""
        scores = [r.scores.get(metric_name, 0.0) for r in results if r.scores]
        return sum(scores) / len(scores) if scores else 0.0

    def _get_config_by_name(self, name: str) -> AblationConfig:
        """Get ablation config by name"""
        for config in self.ablation_configs:
            if config.name == name:
                return config
        return None

    def generate_ablation_table(
        self,
        analysis: Dict[str, Dict[str, float]]
    ) -> str:
        """
        Generate formatted ablation table for paper

        Args:
            analysis: Ablation impact analysis

        Returns:
            Formatted table string
        """
        table = "Ablation Study Results\n"
        table += "=" * 80 + "\n\n"
        table += f"{'Configuration':<30} {'Score':<10} {'Drop':<10} {'% Drop':<10}\n"
        table += "-" * 80 + "\n"

        # Full system first
        table += f"{'Full System':<30} {'-':<10} {'-':<10} {'-':<10}\n"

        # Ablations sorted by impact
        for config_name, metrics in analysis.items():
            score = metrics['ablation_score']
            drop = metrics['absolute_drop']
            pct_drop = metrics['relative_drop_percent']

            table += f"{config_name:<30} {score:<10.3f} {drop:<10.3f} {pct_drop:<10.1f}%\n"

        return table

    def get_ablation_configs(self) -> List[AblationConfig]:
        """Get list of ablation configurations"""
        return self.ablation_configs


class ComponentContributionAnalyzer:
    """
    Analyzes the contribution of individual components

    Computes metrics like:
    - Absolute contribution
    - Relative contribution
    - Statistical significance of contribution
    """

    def __init__(self):
        print("[Component Contribution Analyzer] Initialized")

    def analyze_contributions(
        self,
        ablation_results: Dict[str, List[AblationResult]],
        full_system_name: str = "Full System"
    ) -> Dict[str, Any]:
        """
        Analyze component contributions from ablation results

        Args:
            ablation_results: Results from ablation study
            full_system_name: Name of full system configuration

        Returns:
            Analysis of component contributions
        """
        contributions = {}

        # Get baseline (full system) performance
        full_results = ablation_results.get(full_system_name, [])
        if not full_results:
            return contributions

        # Analyze each ablation
        for config_name, results in ablation_results.items():
            if config_name == full_system_name:
                continue

            contribution = self._compute_contribution(full_results, results)
            contributions[config_name] = contribution

        return contributions

    def _compute_contribution(
        self,
        full_results: List[AblationResult],
        ablation_results: List[AblationResult]
    ) -> Dict[str, float]:
        """Compute contribution metrics"""
        # Extract scores
        full_scores = [r.scores.get('overall', 0.0) for r in full_results if r.scores]
        ablation_scores = [r.scores.get('overall', 0.0) for r in ablation_results if r.scores]

        if not full_scores or not ablation_scores:
            return {}

        # Compute metrics
        import numpy as np

        full_mean = np.mean(full_scores)
        ablation_mean = np.mean(ablation_scores)

        contribution = {
            'full_system_mean': float(full_mean),
            'ablation_mean': float(ablation_mean),
            'absolute_contribution': float(full_mean - ablation_mean),
            'relative_contribution_percent': float((full_mean - ablation_mean) / full_mean * 100) if full_mean > 0 else 0.0,
            'full_system_std': float(np.std(full_scores)),
            'ablation_std': float(np.std(ablation_scores))
        }

        return contribution


if __name__ == "__main__":
    print("Ablation Study Framework")
    print("=" * 60)
    print("\nStandard Ablations for Agentic RAG:")
    print("1. No Memory Agent")
    print("2. No Query Agent")
    print("3. No Retrieval Agent")
    print("4. No Response Agent")
    print("5. No Query Classification")
    print("6. No Conversation Memory")
    print("7. No Agents (Vanilla RAG)")
    print("8. Minimal System (shows total contribution)")
    print("\nUsage:")
    print("  study = AblationStudy(full_system)")
    print("  study.define_standard_ablations()")
    print("  results = study.run_batch_ablations(questions)")
    print("  analysis = study.compute_ablation_impact(results)")
