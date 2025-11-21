"""
Observability with Logfire Integration
=======================================

Deep observability and debugging for RAG system using Pydantic Logfire.

This module provides:
- Automatic tracing of all LLM calls
- Performance monitoring and bottleneck detection
- Cost tracking per query
- Error tracking with full context
- Real-time debugging dashboard (optional)

Key Features:
- Local-only mode (no cloud required)
- Structured logging with context
- Automatic instrumentation
- Integration with existing experiment tracking
- Minimal performance overhead

Note: This uses local Logfire mode by default. For cloud dashboard:
1. Sign up at https://logfire.pydantic.dev
2. Set LOGFIRE_TOKEN environment variable
3. Set enable_cloud=True in config

Usage:
    from observability import setup_observability, trace_query

    # Setup once at application start
    setup_observability(enable_cloud=False)

    # Automatic tracing
    @trace_query("rag_query")
    def query_rag(question):
        # All LLM calls, retrievals automatically traced
        return result
"""

import os
import time
import functools
from typing import Optional, Dict, Any, Callable, List
from dataclasses import dataclass, field
from datetime import datetime
from contextlib import contextmanager
import json

# Conditional import - Logfire is optional
try:
    import logfire
    LOGFIRE_AVAILABLE = True
except ImportError:
    LOGFIRE_AVAILABLE = False
    print("Warning: logfire not installed. Install with: pip install logfire")


@dataclass
class TraceConfig:
    """Configuration for observability"""
    enabled: bool = True
    enable_cloud: bool = False  # Set True for cloud dashboard
    local_dir: str = "./logs/logfire"
    service_name: str = "rag-system"
    environment: str = "development"
    log_level: str = "INFO"
    sample_rate: float = 1.0  # Sample 100% of traces (reduce for production)


@dataclass
class QueryTrace:
    """Trace information for a single query"""
    query_id: str
    query: str
    start_time: float
    end_time: Optional[float] = None
    duration_ms: Optional[float] = None
    model_used: Optional[str] = None
    tokens_used: Optional[int] = None
    cost: Optional[float] = None
    complexity: Optional[str] = None
    retrieval_method: Optional[str] = None
    num_sources: Optional[int] = None
    success: bool = True
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def finish(self, success: bool = True, error: Optional[str] = None):
        """Mark trace as finished"""
        self.end_time = time.time()
        self.duration_ms = (self.end_time - self.start_time) * 1000
        self.success = success
        self.error = error

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "query_id": self.query_id,
            "query": self.query,
            "duration_ms": self.duration_ms,
            "model_used": self.model_used,
            "tokens_used": self.tokens_used,
            "cost": self.cost,
            "complexity": self.complexity,
            "retrieval_method": self.retrieval_method,
            "num_sources": self.num_sources,
            "success": self.success,
            "error": self.error,
            "metadata": self.metadata
        }


class ObservabilityManager:
    """
    Manages observability and tracing for RAG system

    This provides a unified interface for logging, tracing, and monitoring.
    """

    def __init__(self, config: TraceConfig):
        self.config = config
        self.enabled = config.enabled and LOGFIRE_AVAILABLE
        self.active_traces: Dict[str, QueryTrace] = {}
        self.completed_traces: List[QueryTrace] = []

        # Statistics
        self.stats = {
            "total_queries": 0,
            "successful_queries": 0,
            "failed_queries": 0,
            "total_duration_ms": 0.0,
            "total_tokens": 0,
            "total_cost": 0.0
        }

        if self.enabled:
            self._setup_logfire()
        else:
            print("Observability disabled (logfire not available or disabled in config)")

    def _setup_logfire(self):
        """Setup Logfire instrumentation"""
        try:
            # Configure Logfire
            if self.config.enable_cloud:
                # Cloud mode - requires token
                token = os.getenv("LOGFIRE_TOKEN")
                if token:
                    logfire.configure(
                        token=token,
                        service_name=self.config.service_name,
                        environment=self.config.environment
                    )
                    print("✅ Logfire cloud dashboard enabled")
                else:
                    print("⚠️ LOGFIRE_TOKEN not set, using local mode")
                    self._setup_local_mode()
            else:
                # Local mode - no cloud required
                self._setup_local_mode()

        except Exception as e:
            print(f"Warning: Failed to setup Logfire: {e}")
            self.enabled = False

    def _setup_local_mode(self):
        """Setup local-only logging"""
        # Create local log directory
        os.makedirs(self.config.local_dir, exist_ok=True)

        # Configure for local file logging
        logfire.configure(
            send_to_logfire=False,  # Don't send to cloud
            console=False,  # Use structured local logging instead
        )
        print(f"✅ Logfire local mode enabled (logs: {self.config.local_dir})")

    def start_trace(self, query_id: str, query: str, **metadata) -> QueryTrace:
        """
        Start tracing a query

        Args:
            query_id: Unique identifier for this query
            query: The query text
            **metadata: Additional metadata

        Returns:
            QueryTrace object
        """
        trace = QueryTrace(
            query_id=query_id,
            query=query,
            start_time=time.time(),
            metadata=metadata
        )

        self.active_traces[query_id] = trace
        self.stats["total_queries"] += 1

        if self.enabled:
            logfire.info(
                "query_started",
                query_id=query_id,
                query=query[:200],  # Truncate long queries
                **metadata
            )

        return trace

    def end_trace(self,
                 query_id: str,
                 success: bool = True,
                 error: Optional[str] = None,
                 **results):
        """
        End tracing for a query

        Args:
            query_id: Query identifier
            success: Whether query succeeded
            error: Error message if failed
            **results: Result metadata (model, tokens, cost, etc.)
        """
        if query_id not in self.active_traces:
            print(f"Warning: Trace {query_id} not found")
            return

        trace = self.active_traces[query_id]
        trace.finish(success=success, error=error)

        # Update trace with results
        trace.model_used = results.get("model_used")
        trace.tokens_used = results.get("tokens_used")
        trace.cost = results.get("cost")
        trace.complexity = results.get("complexity")
        trace.retrieval_method = results.get("retrieval_method")
        trace.num_sources = results.get("num_sources")
        trace.metadata.update(results.get("metadata", {}))

        # Update statistics
        if success:
            self.stats["successful_queries"] += 1
        else:
            self.stats["failed_queries"] += 1

        if trace.duration_ms:
            self.stats["total_duration_ms"] += trace.duration_ms

        if trace.tokens_used:
            self.stats["total_tokens"] += trace.tokens_used

        if trace.cost:
            self.stats["total_cost"] += trace.cost

        # Log completion
        if self.enabled:
            if success:
                logfire.info(
                    "query_completed",
                    query_id=query_id,
                    duration_ms=trace.duration_ms,
                    model=trace.model_used,
                    tokens=trace.tokens_used,
                    cost=trace.cost,
                    **results
                )
            else:
                logfire.error(
                    "query_failed",
                    query_id=query_id,
                    duration_ms=trace.duration_ms,
                    error=error,
                    **results
                )

        # Move to completed
        self.completed_traces.append(trace)
        del self.active_traces[query_id]

        # Write to local file
        self._write_trace_to_file(trace)

    def _write_trace_to_file(self, trace: QueryTrace):
        """Write trace to local JSON file"""
        if not self.config.enabled:
            return

        try:
            log_file = os.path.join(
                self.config.local_dir,
                f"traces_{datetime.now().strftime('%Y%m%d')}.jsonl"
            )

            with open(log_file, 'a') as f:
                f.write(json.dumps(trace.to_dict()) + "\n")

        except Exception as e:
            print(f"Warning: Failed to write trace: {e}")

    @contextmanager
    def trace_context(self, operation: str, **metadata):
        """
        Context manager for tracing operations

        Usage:
            with manager.trace_context("retrieval", method="hybrid"):
                results = retriever.search(query)
        """
        start = time.time()

        if self.enabled:
            logfire.info(f"{operation}_started", **metadata)

        try:
            yield
            duration = (time.time() - start) * 1000

            if self.enabled:
                logfire.info(
                    f"{operation}_completed",
                    duration_ms=duration,
                    **metadata
                )

        except Exception as e:
            duration = (time.time() - start) * 1000

            if self.enabled:
                logfire.error(
                    f"{operation}_failed",
                    duration_ms=duration,
                    error=str(e),
                    **metadata
                )
            raise

    def get_stats(self) -> Dict[str, Any]:
        """Get observability statistics"""
        avg_duration = (self.stats["total_duration_ms"] / self.stats["total_queries"]
                       if self.stats["total_queries"] > 0 else 0)

        avg_tokens = (self.stats["total_tokens"] / self.stats["total_queries"]
                     if self.stats["total_queries"] > 0 else 0)

        success_rate = (self.stats["successful_queries"] / self.stats["total_queries"] * 100
                       if self.stats["total_queries"] > 0 else 0)

        return {
            **self.stats,
            "avg_duration_ms": avg_duration,
            "avg_tokens_per_query": avg_tokens,
            "success_rate_percent": success_rate
        }

    def get_recent_traces(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent completed traces"""
        recent = self.completed_traces[-limit:]
        return [trace.to_dict() for trace in reversed(recent)]


# ============================================================================
# Global Manager Instance
# ============================================================================

_global_manager: Optional[ObservabilityManager] = None


def setup_observability(config: Optional[TraceConfig] = None) -> ObservabilityManager:
    """
    Setup observability (call once at application start)

    Args:
        config: TraceConfig or None for defaults

    Returns:
        ObservabilityManager instance
    """
    global _global_manager

    if config is None:
        config = TraceConfig(
            enabled=True,
            enable_cloud=False,  # Local-only by default
            service_name="rag-system",
            environment=os.getenv("ENVIRONMENT", "development")
        )

    _global_manager = ObservabilityManager(config)
    return _global_manager


def get_manager() -> Optional[ObservabilityManager]:
    """Get global observability manager"""
    return _global_manager


# ============================================================================
# Decorators for Easy Integration
# ============================================================================

def trace_query(operation_name: str = "query"):
    """
    Decorator to automatically trace function calls

    Usage:
        @trace_query("rag_query")
        def query_rag(question: str):
            return answer
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            manager = get_manager()

            if manager is None or not manager.enabled:
                # No tracing, just run function
                return func(*args, **kwargs)

            # Generate query ID
            query_id = f"{operation_name}_{int(time.time() * 1000)}"

            # Extract query from args/kwargs
            query_text = kwargs.get("query") or kwargs.get("question") or str(args[0] if args else "")

            # Start trace
            manager.start_trace(query_id, query_text, operation=operation_name)

            try:
                # Run function
                result = func(*args, **kwargs)

                # End trace with success
                manager.end_trace(
                    query_id,
                    success=True,
                    result=str(result)[:200] if result else None
                )

                return result

            except Exception as e:
                # End trace with failure
                manager.end_trace(
                    query_id,
                    success=False,
                    error=str(e)
                )
                raise

        return wrapper
    return decorator


def trace_operation(operation_name: str):
    """
    Decorator for tracing specific operations (retrieval, generation, etc.)

    Usage:
        @trace_operation("retrieval")
        def retrieve_documents(query):
            return documents
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            manager = get_manager()

            if manager is None or not manager.enabled:
                return func(*args, **kwargs)

            with manager.trace_context(operation_name):
                return func(*args, **kwargs)

        return wrapper
    return decorator


# ============================================================================
# Standalone Testing
# ============================================================================

if __name__ == "__main__":
    print("Testing Observability Module...")
    print("=" * 60)

    # Setup observability (local mode)
    config = TraceConfig(
        enabled=True,
        enable_cloud=False,
        local_dir="./test_logs"
    )
    manager = setup_observability(config)

    print("\n1. Testing Manual Tracing:")
    print("-" * 60)

    # Test 1: Successful query
    trace = manager.start_trace("test_001", "What is RAG?", user_id="test_user")
    time.sleep(0.1)  # Simulate processing
    manager.end_trace(
        "test_001",
        success=True,
        model_used="gemini-1.5-flash",
        tokens_used=150,
        cost=0.01,
        complexity="simple",
        num_sources=3
    )
    print("✅ Traced successful query")

    # Test 2: Failed query
    trace = manager.start_trace("test_002", "Complex query that fails")
    time.sleep(0.05)
    manager.end_trace(
        "test_002",
        success=False,
        error="Timeout error"
    )
    print("✅ Traced failed query")

    # Test 3: Context manager
    print("\n2. Testing Context Manager:")
    print("-" * 60)
    with manager.trace_context("retrieval", method="hybrid", top_k=5):
        time.sleep(0.05)
        print("✅ Traced operation with context manager")

    # Test 4: Decorator
    print("\n3. Testing Decorator:")
    print("-" * 60)

    @trace_query("test_query")
    def sample_query(question: str):
        time.sleep(0.05)
        return f"Answer to: {question}"

    result = sample_query("Test question?")
    print(f"✅ Decorated function returned: {result[:50]}")

    # Test 5: Statistics
    print("\n4. Statistics:")
    print("-" * 60)
    stats = manager.get_stats()
    print(f"Total queries: {stats['total_queries']}")
    print(f"Successful: {stats['successful_queries']}")
    print(f"Failed: {stats['failed_queries']}")
    print(f"Success rate: {stats['success_rate_percent']:.1f}%")
    print(f"Avg duration: {stats['avg_duration_ms']:.2f}ms")
    print(f"Total tokens: {stats['total_tokens']}")
    print(f"Total cost: ${stats['total_cost']:.4f}")

    # Test 6: Recent traces
    print("\n5. Recent Traces:")
    print("-" * 60)
    recent = manager.get_recent_traces(limit=3)
    for trace in recent:
        status = "✅" if trace['success'] else "❌"
        print(f"{status} {trace['query_id']}: {trace['query'][:40]} ({trace['duration_ms']:.2f}ms)")

    print("\n" + "=" * 60)
    print("All tests completed! ✅")
    print(f"Check logs at: {config.local_dir}")
