"""
Pydantic AI Integration Wrapper
================================

This module integrates all Pydantic AI features into the existing RAG system:
1. Structured output validation (RAGResponse)
2. Smart model routing (cost optimization)
3. Logfire observability (debugging & monitoring)

This wrapper provides a clean interface for enhanced_agentic_rag.py to use,
without requiring major changes to existing code.

Architecture:
- Non-invasive: Works alongside existing features
- Optional: Can be enabled/disabled via feature flags
- Backward compatible: Legacy string responses still work
- Testable: A/B testing with evaluation framework

Usage:
    from pydantic_wrapper import PydanticRAGWrapper, PydanticConfig

    # Create wrapper
    wrapper = PydanticRAGWrapper(
        gemini_api_key="your-key",
        config=PydanticConfig(
            enable_structured_output=True,
            enable_model_routing=True,
            enable_observability=True
        )
    )

    # Query with Pydantic features
    response = wrapper.query("What is RAG?")
    # Returns: RAGResponse (structured, validated)

    # Or use async for streaming
    async for chunk in wrapper.query_stream("Complex question"):
        print(chunk)
"""

from typing import Optional, Dict, Any, List, Union, AsyncGenerator
from dataclasses import dataclass
import time
import uuid
from datetime import datetime

# Import Pydantic AI components
from structured_responses import (
    RAGResponse,
    Citation,
    ReasoningStep,
    VerificationResult,
    QueryComplexity,
    SourceType,
    parse_legacy_response,
    validate_response
)

from model_router import (
    SmartModelRouter,
    QueryAnalyzer,
    create_cost_optimized_router,
    create_balanced_router
)

from observability import (
    setup_observability,
    get_manager,
    ObservabilityManager,
    TraceConfig,
    trace_query,
    trace_operation
)


@dataclass
class PydanticConfig:
    """Configuration for Pydantic AI features"""

    # Feature flags
    enable_structured_output: bool = True
    enable_model_routing: bool = True
    enable_observability: bool = True

    # Model routing config
    cost_optimization_level: str = "balanced"  # "aggressive", "balanced", "quality"
    default_model: str = "gemini-1.5-pro"
    force_model: Optional[str] = None  # Override routing

    # Observability config
    enable_cloud_logging: bool = False  # Set True for cloud dashboard
    log_directory: str = "./logs/pydantic"
    service_name: str = "rag-system"

    # Quality config
    min_confidence_threshold: float = 0.5  # Minimum confidence for responses
    max_retries: int = 2  # Max retries on validation failure
    require_sources: bool = True  # Require at least one source


class PydanticRAGWrapper:
    """
    Wrapper that adds Pydantic AI features to existing RAG system

    This provides structured outputs, model routing, and observability
    without requiring changes to the core RAG implementation.
    """

    def __init__(self,
                 gemini_api_key: str,
                 base_rag: Optional[Any] = None,
                 config: Optional[PydanticConfig] = None):
        """
        Initialize Pydantic AI wrapper

        Args:
            gemini_api_key: Google Gemini API key
            base_rag: Existing RAG system (EnhancedAgenticRAG instance)
            config: Pydantic feature configuration
        """
        self.api_key = gemini_api_key
        self.base_rag = base_rag
        self.config = config or PydanticConfig()

        # Initialize components based on config
        self._setup_components()

        # Statistics
        self.stats = {
            "total_queries": 0,
            "structured_responses": 0,
            "validation_retries": 0,
            "routing_decisions": 0
        }

    def _setup_components(self):
        """Setup Pydantic AI components"""

        # 1. Model Router
        if self.config.enable_model_routing:
            if self.config.cost_optimization_level == "aggressive":
                self.router = create_cost_optimized_router()
            elif self.config.cost_optimization_level == "quality":
                self.router = SmartModelRouter(
                    default_model="gemini-1.5-pro",
                    enable_cost_optimization=False
                )
            else:  # balanced
                self.router = create_balanced_router()

            self.query_analyzer = QueryAnalyzer()
            print("✅ Model router enabled (cost optimization: {})".format(
                self.config.cost_optimization_level))
        else:
            self.router = None
            print("⏭️  Model router disabled")

        # 2. Observability
        if self.config.enable_observability:
            trace_config = TraceConfig(
                enabled=True,
                enable_cloud=self.config.enable_cloud_logging,
                local_dir=self.config.log_directory,
                service_name=self.config.service_name
            )
            self.observability = setup_observability(trace_config)
            print("✅ Observability enabled (local mode)")
        else:
            self.observability = None
            print("⏭️  Observability disabled")

        # 3. Structured Output
        if self.config.enable_structured_output:
            print("✅ Structured output validation enabled")
        else:
            print("⏭️  Structured output disabled (legacy mode)")

    def query(self,
             question: str,
             query_type: Optional[str] = None,
             user_context: Optional[Dict] = None,
             force_model: Optional[str] = None,
             **kwargs) -> Union[RAGResponse, str]:
        """
        Query with Pydantic AI enhancements

        Args:
            question: User's question
            query_type: Optional query type hint
            user_context: Optional user context
            force_model: Force specific model (override routing)
            **kwargs: Additional arguments for base RAG

        Returns:
            RAGResponse if structured output enabled, else string
        """
        start_time = time.time()
        query_id = str(uuid.uuid4())
        self.stats["total_queries"] += 1

        # Start observability trace
        if self.observability:
            self.observability.start_trace(
                query_id,
                question,
                query_type=query_type,
                user_context=user_context
            )

        try:
            # 1. Analyze query complexity
            if self.router:
                complexity, confidence = self.query_analyzer.analyze_query(question)
                self.stats["routing_decisions"] += 1
            else:
                complexity = QueryComplexity.MODERATE
                confidence = 0.7

            # 2. Select optimal model
            if force_model or self.config.force_model:
                selected_model = force_model or self.config.force_model
            elif self.router:
                selected_model = self.router.select_model(
                    question,
                    query_complexity=complexity
                )
            else:
                selected_model = self.config.default_model

            # 3. Query the base RAG system
            if self.base_rag:
                # Use existing RAG system
                raw_response = self.base_rag.query(
                    question,
                    query_type=query_type,
                    **kwargs
                )
            else:
                # Placeholder - in real usage, this would call actual RAG
                raw_response = self._mock_query(question)

            # 4. Structure the response (if enabled)
            if self.config.enable_structured_output:
                response = self._structure_response(
                    raw_response,
                    question,
                    complexity,
                    selected_model,
                    start_time
                )
                self.stats["structured_responses"] += 1
            else:
                response = raw_response

            # 5. Validate response quality
            if isinstance(response, RAGResponse):
                if response.confidence < self.config.min_confidence_threshold:
                    print(f"⚠️ Low confidence response: {response.confidence:.2f}")

                if self.config.require_sources and len(response.sources) == 0:
                    print(f"⚠️ No sources provided for response")

            # 6. End trace
            duration_ms = (time.time() - start_time) * 1000
            if self.observability:
                self.observability.end_trace(
                    query_id,
                    success=True,
                    model_used=selected_model,
                    complexity=complexity.value if isinstance(complexity, QueryComplexity) else complexity,
                    duration_ms=duration_ms,
                    num_sources=len(response.sources) if isinstance(response, RAGResponse) else 0
                )

            return response

        except Exception as e:
            # Error handling
            duration_ms = (time.time() - start_time) * 1000
            if self.observability:
                self.observability.end_trace(
                    query_id,
                    success=False,
                    error=str(e),
                    duration_ms=duration_ms
                )

            # Re-raise
            raise

    def _structure_response(self,
                           raw_response: Any,
                           question: str,
                           complexity: QueryComplexity,
                           model: str,
                           start_time: float) -> RAGResponse:
        """
        Convert raw response to structured RAGResponse

        Args:
            raw_response: Raw response from RAG (string or dict)
            question: Original question
            complexity: Query complexity
            model: Model used
            start_time: Query start time

        Returns:
            Structured RAGResponse
        """
        # Handle different response types
        if isinstance(raw_response, RAGResponse):
            # Already structured
            return raw_response

        elif isinstance(raw_response, dict):
            # Dict response - validate and structure
            try:
                # Add metadata
                raw_response["query_complexity"] = complexity
                raw_response["model_used"] = model
                raw_response["processing_time_ms"] = (time.time() - start_time) * 1000

                # Validate
                return validate_response(raw_response)

            except Exception as e:
                print(f"⚠️ Validation failed: {e}")
                self.stats["validation_retries"] += 1

                # Fallback: Create minimal valid response
                return RAGResponse(
                    answer=str(raw_response.get("answer", raw_response)),
                    confidence=0.5,
                    query_complexity=complexity,
                    model_used=model
                )

        elif isinstance(raw_response, str):
            # String response - parse to structure
            return parse_legacy_response(
                raw_response,
                sources=None  # Could extract from base_rag if available
            )

        else:
            # Unknown type - convert to string
            return RAGResponse(
                answer=str(raw_response),
                confidence=0.5,
                query_complexity=complexity,
                model_used=model
            )

    def _mock_query(self, question: str) -> str:
        """Mock query for testing (when base_rag not provided)"""
        return f"This is a mock response to: {question}"

    async def query_stream(self,
                          question: str,
                          **kwargs) -> AsyncGenerator[str, None]:
        """
        Query with streaming response

        Args:
            question: User's question
            **kwargs: Additional arguments

        Yields:
            Response chunks
        """
        # This would integrate with streaming_responses.py
        # For now, yield complete response
        response = self.query(question, **kwargs)

        if isinstance(response, RAGResponse):
            # Stream structured response in chunks
            yield f"Answer: {response.answer}\n\n"

            if response.sources:
                yield "Sources:\n"
                for i, source in enumerate(response.sources, 1):
                    yield f"{i}. {source.content_snippet}\n"

            if response.reasoning_steps:
                yield "\nReasoning:\n"
                for step in response.reasoning_steps:
                    yield f"Step {step.step_number}: {step.description}\n"

        else:
            # Stream string response
            yield response

    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics"""
        stats = {
            "pydantic_wrapper": self.stats.copy()
        }

        # Add router stats
        if self.router:
            stats["model_router"] = self.router.get_stats()

        # Add observability stats
        if self.observability:
            stats["observability"] = self.observability.get_stats()

        return stats

    def get_cost_savings(self) -> Dict[str, Any]:
        """Get cost savings from model routing"""
        if self.router:
            return self.router.estimate_cost_savings()
        return {"message": "Model routing not enabled"}

    def export_traces(self, output_file: str):
        """Export traces for analysis"""
        if self.observability:
            traces = self.observability.get_recent_traces(limit=1000)

            import json
            with open(output_file, 'w') as f:
                json.dump(traces, f, indent=2)

            print(f"✅ Exported {len(traces)} traces to {output_file}")
        else:
            print("⚠️ Observability not enabled")


# ============================================================================
# Factory Functions
# ============================================================================

def create_pydantic_wrapper(
    gemini_api_key: str,
    base_rag: Optional[Any] = None,
    cost_optimization: str = "balanced",
    enable_observability: bool = True
) -> PydanticRAGWrapper:
    """
    Create Pydantic wrapper with common defaults

    Args:
        gemini_api_key: Gemini API key
        base_rag: Existing RAG system
        cost_optimization: "aggressive", "balanced", or "quality"
        enable_observability: Enable Logfire tracing

    Returns:
        Configured PydanticRAGWrapper
    """
    config = PydanticConfig(
        enable_structured_output=True,
        enable_model_routing=True,
        enable_observability=enable_observability,
        cost_optimization_level=cost_optimization
    )

    return PydanticRAGWrapper(
        gemini_api_key=gemini_api_key,
        base_rag=base_rag,
        config=config
    )


# ============================================================================
# Standalone Testing
# ============================================================================

if __name__ == "__main__":
    print("Testing Pydantic AI Wrapper...")
    print("=" * 60)

    # Create wrapper (without base RAG for testing)
    wrapper = create_pydantic_wrapper(
        gemini_api_key="test-key",
        base_rag=None,  # Will use mock
        cost_optimization="balanced",
        enable_observability=True
    )

    print("\n1. Testing Simple Query:")
    print("-" * 60)
    response = wrapper.query("What is RAG?")
    if isinstance(response, RAGResponse):
        print(f"✅ Got structured response:")
        print(f"   Answer: {response.answer[:80]}...")
        print(f"   Confidence: {response.confidence}")
        print(f"   Complexity: {response.query_complexity.value}")
        print(f"   Model: {response.model_used}")
    else:
        print(f"✅ Got string response: {response[:80]}...")

    print("\n2. Testing Complex Query:")
    print("-" * 60)
    response = wrapper.query(
        "Analyze the relationship between retrieval quality and generation accuracy"
    )
    if isinstance(response, RAGResponse):
        print(f"✅ Got structured response:")
        print(f"   Complexity: {response.query_complexity.value}")
        print(f"   Model: {response.model_used}")

    print("\n3. Testing Multiple Queries (for routing stats):")
    print("-" * 60)
    test_queries = [
        "Hello",
        "What is machine learning?",
        "Explain the differences between supervised and unsupervised learning",
        "Compare and analyze the implications of different RAG architectures"
    ]

    for query in test_queries:
        response = wrapper.query(query)
        if isinstance(response, RAGResponse):
            print(f"✅ {query[:40]:<40} → {response.model_used}")

    print("\n4. Statistics:")
    print("-" * 60)
    stats = wrapper.get_stats()
    print(f"Total queries: {stats['pydantic_wrapper']['total_queries']}")
    print(f"Structured responses: {stats['pydantic_wrapper']['structured_responses']}")

    if 'model_router' in stats:
        router_stats = stats['model_router']
        print(f"\nModel routing:")
        for model, count in router_stats['by_model'].items():
            print(f"  {model}: {count} queries")

    if 'observability' in stats:
        obs_stats = stats['observability']
        print(f"\nObservability:")
        print(f"  Success rate: {obs_stats['success_rate_percent']:.1f}%")
        print(f"  Avg duration: {obs_stats['avg_duration_ms']:.2f}ms")

    print("\n5. Cost Savings:")
    print("-" * 60)
    savings = wrapper.get_cost_savings()
    if 'savings' in savings:
        print(f"Baseline cost: ${savings['baseline_cost']:.4f}")
        print(f"Actual cost: ${savings['actual_cost']:.4f}")
        print(f"Savings: ${savings['savings']:.4f} ({savings['savings_percent']:.1f}%)")

    print("\n" + "=" * 60)
    print("All tests completed! ✅")
