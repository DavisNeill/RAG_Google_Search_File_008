"""
Experiment Tracking System
===========================

Tracks experiments, configurations, and results for research publication.

Benefits for research:
- Systematic experiment management
- Configuration versioning
- Result comparison across experiments
- Publication-ready tracking
- Reproducibility support

Features:
- Experiment metadata tracking
- Configuration snapshots
- Parameter logging
- Result aggregation
- Comparison tools
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime
import json
import hashlib
from pathlib import Path


@dataclass
class ExperimentConfig:
    """Configuration for an experiment"""
    # Retrieval configuration
    retrieval_method: str = "hybrid"  # hybrid, dense, bm25
    embedding_model: str = "text-embedding-004"
    top_k: int = 5
    use_reranking: bool = True
    reranker_model: Optional[str] = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    # Query processing
    use_query_rewriting: bool = True
    use_query_expansion: bool = True
    use_multi_query: bool = False

    # Generation configuration
    llm_model: str = "gemini-1.5-pro"
    temperature: float = 0.7
    max_tokens: int = 1024
    use_streaming: bool = True

    # Advanced features
    use_multihop: bool = True
    max_hops: int = 3
    use_self_reflection: bool = True
    use_citation_system: bool = True

    # Caching
    use_embedding_cache: bool = True
    cache_type: str = "memory"  # memory, redis, semantic

    # Custom parameters
    custom_params: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)

    def get_hash(self) -> str:
        """Get configuration hash for uniqueness"""
        config_str = json.dumps(self.to_dict(), sort_keys=True)
        return hashlib.md5(config_str.encode()).hexdigest()


@dataclass
class ExperimentMetadata:
    """Metadata for an experiment"""
    experiment_id: str
    experiment_name: str
    description: str
    created_at: str
    created_by: str
    tags: List[str] = field(default_factory=list)
    dataset_name: Optional[str] = None
    dataset_size: Optional[int] = None
    version: str = "1.0"
    notes: str = ""


@dataclass
class ExperimentResult:
    """Results from an experiment"""
    experiment_id: str
    overall_score: float
    ragas_score: Optional[float] = None
    ir_score: Optional[float] = None
    semantic_score: Optional[float] = None
    avg_latency_ms: Optional[float] = None
    total_queries: int = 0
    successful_queries: int = 0
    failed_queries: int = 0

    # Detailed metrics
    detailed_metrics: Dict[str, float] = field(default_factory=dict)

    # Performance metrics
    performance_metrics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class Experiment:
    """Complete experiment record"""
    metadata: ExperimentMetadata
    config: ExperimentConfig
    results: Optional[ExperimentResult] = None
    status: str = "pending"  # pending, running, completed, failed
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    duration_seconds: Optional[float] = None
    error_message: Optional[str] = None


class ExperimentTracker:
    """
    Tracks experiments and their configurations
    """

    def __init__(
        self,
        storage_path: Optional[str] = None,
        use_database: bool = True,
        supabase_client: Any = None
    ):
        """
        Initialize experiment tracker

        Args:
            storage_path: Optional local storage path for experiments
            use_database: Whether to use database (Supabase)
            supabase_client: Supabase client for database storage
        """
        self.storage_path = Path(storage_path) if storage_path else Path("experiments")
        self.use_database = use_database
        self.supabase_client = supabase_client

        # Create storage directory
        if storage_path:
            self.storage_path.mkdir(parents=True, exist_ok=True)

        self.experiments: Dict[str, Experiment] = {}

        print(f"[ExperimentTracker] Initialized (db={use_database}, path={self.storage_path})")

    def create_experiment(
        self,
        name: str,
        description: str,
        config: ExperimentConfig,
        created_by: str = "system",
        tags: Optional[List[str]] = None,
        dataset_name: Optional[str] = None
    ) -> Experiment:
        """
        Create new experiment

        Args:
            name: Experiment name
            description: Experiment description
            config: Experiment configuration
            created_by: User creating the experiment
            tags: Optional tags for categorization
            dataset_name: Dataset used for evaluation

        Returns:
            Created Experiment object
        """
        # Generate experiment ID
        experiment_id = self._generate_experiment_id(name)

        # Create metadata
        metadata = ExperimentMetadata(
            experiment_id=experiment_id,
            experiment_name=name,
            description=description,
            created_at=datetime.now().isoformat(),
            created_by=created_by,
            tags=tags or [],
            dataset_name=dataset_name
        )

        # Create experiment
        experiment = Experiment(
            metadata=metadata,
            config=config,
            status="pending"
        )

        # Store in memory
        self.experiments[experiment_id] = experiment

        # Persist
        self._save_experiment(experiment)

        print(f"[Tracker] Created experiment: {experiment_id}")
        return experiment

    def start_experiment(self, experiment_id: str):
        """Mark experiment as started"""
        if experiment_id not in self.experiments:
            raise ValueError(f"Experiment not found: {experiment_id}")

        experiment = self.experiments[experiment_id]
        experiment.status = "running"
        experiment.start_time = datetime.now().isoformat()

        self._save_experiment(experiment)
        print(f"[Tracker] Started experiment: {experiment_id}")

    def complete_experiment(
        self,
        experiment_id: str,
        results: ExperimentResult
    ):
        """Mark experiment as completed with results"""
        if experiment_id not in self.experiments:
            raise ValueError(f"Experiment not found: {experiment_id}")

        experiment = self.experiments[experiment_id]
        experiment.status = "completed"
        experiment.end_time = datetime.now().isoformat()
        experiment.results = results

        # Calculate duration
        if experiment.start_time:
            start_dt = datetime.fromisoformat(experiment.start_time)
            end_dt = datetime.fromisoformat(experiment.end_time)
            experiment.duration_seconds = (end_dt - start_dt).total_seconds()

        self._save_experiment(experiment)
        print(f"[Tracker] Completed experiment: {experiment_id}")

    def fail_experiment(self, experiment_id: str, error_message: str):
        """Mark experiment as failed"""
        if experiment_id not in self.experiments:
            raise ValueError(f"Experiment not found: {experiment_id}")

        experiment = self.experiments[experiment_id]
        experiment.status = "failed"
        experiment.end_time = datetime.now().isoformat()
        experiment.error_message = error_message

        self._save_experiment(experiment)
        print(f"[Tracker] Failed experiment: {experiment_id} - {error_message}")

    def get_experiment(self, experiment_id: str) -> Optional[Experiment]:
        """Get experiment by ID"""
        if experiment_id in self.experiments:
            return self.experiments[experiment_id]

        # Try loading from storage
        return self._load_experiment(experiment_id)

    def list_experiments(
        self,
        tags: Optional[List[str]] = None,
        status: Optional[str] = None
    ) -> List[Experiment]:
        """
        List experiments with optional filtering

        Args:
            tags: Filter by tags
            status: Filter by status

        Returns:
            List of matching experiments
        """
        experiments = list(self.experiments.values())

        # Filter by tags
        if tags:
            experiments = [
                exp for exp in experiments
                if any(tag in exp.metadata.tags for tag in tags)
            ]

        # Filter by status
        if status:
            experiments = [exp for exp in experiments if exp.status == status]

        return sorted(
            experiments,
            key=lambda x: x.metadata.created_at,
            reverse=True
        )

    def compare_experiments(
        self,
        experiment_ids: List[str]
    ) -> Dict[str, Any]:
        """
        Compare multiple experiments

        Args:
            experiment_ids: List of experiment IDs to compare

        Returns:
            Comparison data structure
        """
        experiments = [self.get_experiment(eid) for eid in experiment_ids]
        experiments = [e for e in experiments if e is not None]

        if not experiments:
            return {}

        comparison = {
            'experiments': [],
            'metric_comparison': {},
            'config_diff': {}
        }

        # Gather data for each experiment
        for exp in experiments:
            exp_data = {
                'id': exp.metadata.experiment_id,
                'name': exp.metadata.experiment_name,
                'created_at': exp.metadata.created_at,
                'status': exp.status,
                'config': exp.config.to_dict()
            }

            if exp.results:
                exp_data['results'] = exp.results.to_dict()

            comparison['experiments'].append(exp_data)

        # Compare metrics
        if all(e.results for e in experiments):
            metrics = ['overall_score', 'ragas_score', 'ir_score', 'semantic_score', 'avg_latency_ms']

            for metric in metrics:
                values = []
                for exp in experiments:
                    value = getattr(exp.results, metric, None)
                    if value is not None:
                        values.append({
                            'experiment_id': exp.metadata.experiment_id,
                            'value': value
                        })

                if values:
                    comparison['metric_comparison'][metric] = {
                        'values': values,
                        'best': max(values, key=lambda x: x['value'] if metric != 'avg_latency_ms' else -x['value']),
                        'worst': min(values, key=lambda x: x['value'] if metric != 'avg_latency_ms' else -x['value'])
                    }

        # Compare configurations
        if len(experiments) > 1:
            base_config = experiments[0].config.to_dict()
            for exp in experiments[1:]:
                current_config = exp.config.to_dict()
                diff = {}

                for key in base_config:
                    if base_config[key] != current_config.get(key):
                        diff[key] = {
                            'base': base_config[key],
                            exp.metadata.experiment_id: current_config.get(key)
                        }

                if diff:
                    comparison['config_diff'][exp.metadata.experiment_id] = diff

        return comparison

    def export_experiment(
        self,
        experiment_id: str,
        export_path: Optional[str] = None
    ) -> str:
        """
        Export experiment to JSON

        Args:
            experiment_id: Experiment ID
            export_path: Optional export file path

        Returns:
            Path to exported file
        """
        experiment = self.get_experiment(experiment_id)
        if not experiment:
            raise ValueError(f"Experiment not found: {experiment_id}")

        # Prepare export data
        export_data = {
            'metadata': asdict(experiment.metadata),
            'config': experiment.config.to_dict(),
            'status': experiment.status,
            'start_time': experiment.start_time,
            'end_time': experiment.end_time,
            'duration_seconds': experiment.duration_seconds
        }

        if experiment.results:
            export_data['results'] = experiment.results.to_dict()

        # Determine export path
        if export_path is None:
            export_path = self.storage_path / f"{experiment_id}_export.json"
        else:
            export_path = Path(export_path)

        # Write to file
        with open(export_path, 'w') as f:
            json.dump(export_data, f, indent=2)

        print(f"[Tracker] Exported experiment to: {export_path}")
        return str(export_path)

    def _generate_experiment_id(self, name: str) -> str:
        """Generate unique experiment ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name_slug = name.lower().replace(" ", "_")[:20]
        return f"{name_slug}_{timestamp}"

    def _save_experiment(self, experiment: Experiment):
        """Save experiment to storage"""
        # Save to local file
        if self.storage_path:
            file_path = self.storage_path / f"{experiment.metadata.experiment_id}.json"
            with open(file_path, 'w') as f:
                export_data = {
                    'metadata': asdict(experiment.metadata),
                    'config': experiment.config.to_dict(),
                    'status': experiment.status,
                    'start_time': experiment.start_time,
                    'end_time': experiment.end_time,
                    'duration_seconds': experiment.duration_seconds,
                    'error_message': experiment.error_message
                }
                if experiment.results:
                    export_data['results'] = experiment.results.to_dict()

                json.dump(export_data, f, indent=2)

        # Save to database if enabled
        if self.use_database and self.supabase_client:
            self._save_to_database(experiment)

    def _load_experiment(self, experiment_id: str) -> Optional[Experiment]:
        """Load experiment from storage"""
        file_path = self.storage_path / f"{experiment_id}.json"

        if not file_path.exists():
            return None

        with open(file_path, 'r') as f:
            data = json.load(f)

        # Reconstruct experiment
        metadata = ExperimentMetadata(**data['metadata'])
        config = ExperimentConfig(**data['config'])

        experiment = Experiment(
            metadata=metadata,
            config=config,
            status=data['status'],
            start_time=data.get('start_time'),
            end_time=data.get('end_time'),
            duration_seconds=data.get('duration_seconds'),
            error_message=data.get('error_message')
        )

        if 'results' in data:
            experiment.results = ExperimentResult(**data['results'])

        return experiment

    def _save_to_database(self, experiment: Experiment):
        """Save experiment to Supabase database"""
        try:
            # Prepare data for database
            db_data = {
                'experiment_id': experiment.metadata.experiment_id,
                'experiment_name': experiment.metadata.experiment_name,
                'description': experiment.metadata.description,
                'created_by': experiment.metadata.created_by,
                'tags': experiment.metadata.tags,
                'config': experiment.config.to_dict(),
                'status': experiment.status,
                'start_time': experiment.start_time,
                'end_time': experiment.end_time,
                'duration_seconds': experiment.duration_seconds
            }

            if experiment.results:
                db_data.update({
                    'overall_score': experiment.results.overall_score,
                    'ragas_score': experiment.results.ragas_score,
                    'ir_score': experiment.results.ir_score,
                    'semantic_score': experiment.results.semantic_score,
                    'avg_latency_ms': experiment.results.avg_latency_ms
                })

            # Upsert to database
            self.supabase_client.table('experiments').upsert(
                db_data,
                on_conflict='experiment_id'
            ).execute()

        except Exception as e:
            print(f"[Tracker] Database save error: {e}")


def create_tracker(supabase_client: Any = None, **kwargs) -> ExperimentTracker:
    """
    Factory function to create experiment tracker

    Args:
        supabase_client: Supabase client instance
        **kwargs: Additional configuration

    Returns:
        ExperimentTracker instance
    """
    return ExperimentTracker(supabase_client=supabase_client, **kwargs)


if __name__ == "__main__":
    print("Experiment Tracking System")
    print("=" * 60)
    print("\nFeatures:")
    print("✓ Experiment metadata tracking")
    print("✓ Configuration versioning")
    print("✓ Result aggregation")
    print("✓ Experiment comparison")
    print("✓ Export capabilities")
    print("\nBenefits:")
    print("✓ Systematic experiment management")
    print("✓ Reproducibility support")
    print("✓ Publication-ready tracking")
    print("✓ Configuration diff tools")
    print("\nUsage:")
    print("  tracker = create_tracker()")
    print("  experiment = tracker.create_experiment(name, description, config)")
    print("  tracker.start_experiment(experiment.metadata.experiment_id)")
    print("  # Run evaluation...")
    print("  tracker.complete_experiment(experiment_id, results)")
    print("\nComparison:")
    print("  comparison = tracker.compare_experiments([exp1_id, exp2_id])")
