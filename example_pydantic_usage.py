"""
Example Usage: Pydantic AI Integration
========================================

This script demonstrates how to use the new Pydantic AI features:
1. Structured Output Validation
2. Smart Model Routing
3. Logfire Observability

Run this script to see the features in action!

Requirements:
    pip install pydantic-ai logfire
"""

import os
from enhanced_agentic_rag import EnhancedAgenticRAG, EnhancedConfig
from structured_responses import RAGResponse

def example_1_structured_output():
    """Example 1: Structured Output Validation"""
    print("=" * 70)
    print("Example 1: Structured Output Validation")
    print("=" * 70)
    print("\nThis example shows how to get structured, validated responses")
    print("instead of raw strings.\n")

    # Configure with Pydantic AI features
    config = EnhancedConfig()
    config.use_pydantic = True
    config.use_structured_output = True
    config.use_model_routing = False  # Disable routing for this example
    config.use_observability = False  # Disable for simplicity

    # Create RAG instance
    rag = EnhancedAgenticRAG(
        api_key=os.getenv('GEMINI_API_KEY', 'your-api-key'),
        config=config
    )

    print("\n🔹 Querying with structured output...")

    # Query with query_v2 (returns RAGResponse)
    response = rag.query_v2("What is Retrieval-Augmented Generation?")

    if isinstance(response, RAGResponse):
        print("\n✅ Got structured response!")
        print(f"\n📝 Answer:")
        print(f"   {response.answer[:200]}...")
        print(f"\n📊 Metadata:")
        print(f"   Confidence: {response.confidence:.2f}")
        print(f"   Complexity: {response.query_complexity.value}")
        print(f"   Model: {response.model_used}")
        print(f"   Processing Time: {response.processing_time_ms:.2f}ms")
        print(f"   Sources: {len(response.sources)}")

        if response.sources:
            print(f"\n📚 Sources:")
            for i, source in enumerate(response.sources[:3], 1):
                print(f"   {i}. {source.source_id} (score: {source.relevance_score:.2f})")

        # Access structured fields programmatically
        print(f"\n💡 Programmatic Access:")
        print(f"   response.answer: {type(response.answer)}")
        print(f"   response.confidence: {type(response.confidence)}")
        print(f"   response.sources: {type(response.sources)}")
        print(f"\n   All fields are type-safe and validated!")
    else:
        print("\n⚠️  Got dictionary response (Pydantic might not be enabled)")
        print(f"   Type: {type(response)}")


def example_2_model_routing():
    """Example 2: Smart Model Routing"""
    print("\n\n" + "=" * 70)
    print("Example 2: Smart Model Routing (Cost Optimization)")
    print("=" * 70)
    print("\nThis example shows how model routing saves costs by using")
    print("cheaper models for simple queries and expensive models for complex ones.\n")

    # Configure with model routing
    config = EnhancedConfig()
    config.use_pydantic = True
    config.use_structured_output = True
    config.use_model_routing = True  # Enable routing
    config.use_observability = False
    config.pydantic_cost_optimization = "balanced"  # or "aggressive", "quality"

    rag = EnhancedAgenticRAG(
        api_key=os.getenv('GEMINI_API_KEY', 'your-api-key'),
        config=config
    )

    # Test different query complexities
    test_queries = [
        ("Hello, how are you?", "simple"),
        ("What is machine learning?", "simple"),
        ("How does retrieval-augmented generation improve LLM accuracy?", "moderate"),
        ("Analyze the relationship between embedding quality and retrieval performance in RAG systems", "complex"),
    ]

    print("🔹 Testing multiple queries with different complexities:\n")

    for query, expected_complexity in test_queries:
        response = rag.query_v2(query)

        if isinstance(response, RAGResponse):
            print(f"Query: {query[:60]:<60}")
            print(f"  Complexity: {response.query_complexity.value:<15} Model: {response.model_used}")
        else:
            print(f"Query: {query[:60]:<60}")
            print(f"  Got dict response")
        print()

    # Show cost savings
    print("\n💰 Cost Savings Analysis:")
    savings = rag.get_cost_savings()

    if savings and 'savings' in savings:
        print(f"   Baseline cost (all Pro): ${savings['baseline_cost']:.4f}")
        print(f"   Actual cost (optimized): ${savings['actual_cost']:.4f}")
        print(f"   💵 Savings: ${savings['savings']:.4f} ({savings['savings_percent']:.1f}%)")
        print(f"\n   Model distribution:")
        for model, count in savings.get('breakdown_by_model', {}).items():
            print(f"     {model}: {count} queries")
    else:
        print("   No routing stats available yet")


def example_3_observability():
    """Example 3: Observability with Logfire"""
    print("\n\n" + "=" * 70)
    print("Example 3: Observability with Logfire")
    print("=" * 70)
    print("\nThis example shows how Logfire traces all operations for debugging.\n")

    # Configure with observability
    config = EnhancedConfig()
    config.use_pydantic = True
    config.use_structured_output = True
    config.use_model_routing = True
    config.use_observability = True  # Enable tracing
    config.pydantic_cost_optimization = "balanced"

    rag = EnhancedAgenticRAG(
        api_key=os.getenv('GEMINI_API_KEY', 'your-api-key'),
        config=config
    )

    print("🔹 Running queries with full observability...\n")

    # Run some queries
    queries = [
        "What is RAG?",
        "Explain how embedding models work",
        "Compare different retrieval strategies"
    ]

    for query in queries:
        print(f"Querying: {query}")
        response = rag.query_v2(query)

        if isinstance(response, RAGResponse):
            print(f"  ✅ Completed in {response.processing_time_ms:.2f}ms")
            print(f"     Model: {response.model_used}, Confidence: {response.confidence:.2f}")
        print()

    # Show observability stats
    print("\n📊 Observability Statistics:")
    pydantic_stats = rag.get_pydantic_stats()

    if pydantic_stats and 'observability' in pydantic_stats:
        obs_stats = pydantic_stats['observability']
        print(f"   Total queries: {obs_stats.get('total_queries', 0)}")
        print(f"   Successful: {obs_stats.get('successful_queries', 0)}")
        print(f"   Failed: {obs_stats.get('failed_queries', 0)}")
        print(f"   Success rate: {obs_stats.get('success_rate_percent', 0):.1f}%")
        print(f"   Avg duration: {obs_stats.get('avg_duration_ms', 0):.2f}ms")
        print(f"   Total tokens: {obs_stats.get('total_tokens', 0)}")
        print(f"\n   💡 Check logs at: ./logs/pydantic/")
    else:
        print("   No observability stats available")


def example_4_all_features():
    """Example 4: All Pydantic Features Together"""
    print("\n\n" + "=" * 70)
    print("Example 4: All Pydantic Features Together")
    print("=" * 70)
    print("\nThis example enables all three features for the ultimate RAG experience!\n")

    # Configure with ALL Pydantic features
    config = EnhancedConfig()
    config.use_pydantic = True
    config.use_structured_output = True   # ✅ Validated responses
    config.use_model_routing = True       # ✅ Cost optimization
    config.use_observability = True       # ✅ Deep tracing
    config.pydantic_cost_optimization = "balanced"

    rag = EnhancedAgenticRAG(
        api_key=os.getenv('GEMINI_API_KEY', 'your-api-key'),
        config=config
    )

    print("🚀 Full Pydantic AI stack enabled:")
    print("   ✅ Structured Output Validation")
    print("   ✅ Smart Model Routing")
    print("   ✅ Logfire Observability\n")

    # Complex query
    query = "Explain how retrieval-augmented generation improves factual accuracy in large language models"

    print(f"🔹 Query: {query}\n")

    response = rag.query_v2(query)

    if isinstance(response, RAGResponse):
        print("✅ Structured Response Received!\n")
        print(f"📝 Answer (first 300 chars):")
        print(f"   {response.answer[:300]}...\n")

        print(f"📊 Response Metadata:")
        print(f"   Model Used: {response.model_used}")
        print(f"   Complexity: {response.query_complexity.value}")
        print(f"   Confidence: {response.confidence:.2f}")
        print(f"   Processing Time: {response.processing_time_ms:.2f}ms")
        print(f"   Sources: {len(response.sources)}")

        if response.sources:
            print(f"\n📚 Top Sources:")
            for i, source in enumerate(response.sources[:3], 1):
                print(f"   {i}. {source.content_snippet[:80]}...")

    # Final stats
    print("\n\n📈 Final Statistics:")

    # Cost savings
    savings = rag.get_cost_savings()
    if savings and 'savings' in savings:
        print(f"\n💰 Cost Analysis:")
        print(f"   Savings: ${savings['savings']:.4f} ({savings['savings_percent']:.1f}%)")

    # Observability
    pydantic_stats = rag.get_pydantic_stats()
    if pydantic_stats and 'observability' in pydantic_stats:
        obs = pydantic_stats['observability']
        print(f"\n📊 Performance:")
        print(f"   Success Rate: {obs.get('success_rate_percent', 0):.1f}%")
        print(f"   Avg Duration: {obs.get('avg_duration_ms', 0):.2f}ms")


def example_5_backward_compatibility():
    """Example 5: Backward Compatibility"""
    print("\n\n" + "=" * 70)
    print("Example 5: Backward Compatibility")
    print("=" * 70)
    print("\nPydantic features are optional - old code still works!\n")

    # Old way (no Pydantic)
    config_old = EnhancedConfig()
    config_old.use_pydantic = False  # Disabled

    rag_old = EnhancedAgenticRAG(
        api_key=os.getenv('GEMINI_API_KEY', 'your-api-key'),
        config=config_old
    )

    print("🔹 Old way (query returns dict):")
    result_old = rag_old.query("What is RAG?")
    print(f"   Type: {type(result_old)}")
    print(f"   Keys: {list(result_old.keys())[:5]}")

    # New way (with Pydantic)
    config_new = EnhancedConfig()
    config_new.use_pydantic = True
    config_new.use_structured_output = True

    rag_new = EnhancedAgenticRAG(
        api_key=os.getenv('GEMINI_API_KEY', 'your-api-key'),
        config=config_new
    )

    print("\n🔹 New way (query_v2 returns RAGResponse):")
    result_new = rag_new.query_v2("What is RAG?")
    print(f"   Type: {type(result_new)}")
    if isinstance(result_new, RAGResponse):
        print(f"   Fields: answer, confidence, sources, etc.")
        print(f"   ✅ Type-safe and validated!")

    print("\n💡 Both methods work - choose based on your needs!")


if __name__ == "__main__":
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 68 + "║")
    print("║" + "   Pydantic AI Integration - Example Usage".center(68) + "║")
    print("║" + " " * 68 + "║")
    print("╚" + "=" * 68 + "╝")

    print("\n\nThis script demonstrates the new Pydantic AI features.")
    print("Note: Examples use mock data since we don't have a real API key.\n")

    try:
        # Run examples
        example_1_structured_output()
        example_2_model_routing()
        example_3_observability()
        example_4_all_features()
        example_5_backward_compatibility()

        print("\n\n" + "=" * 70)
        print("✅ All examples completed successfully!")
        print("=" * 70)

        print("\n📚 Next Steps:")
        print("   1. Install dependencies: pip install pydantic-ai logfire")
        print("   2. Set GEMINI_API_KEY environment variable")
        print("   3. Enable Pydantic features in your config")
        print("   4. Use query_v2() for structured responses")
        print("   5. Check ./logs/pydantic/ for observability traces")

        print("\n💡 Integration Tips:")
        print("   - Start with structured_output only (safest)")
        print("   - Add model_routing for cost savings (40-60%)")
        print("   - Enable observability for debugging")
        print("   - Use query() for old code, query_v2() for new code")
        print("   - All features are optional and backward compatible!")

    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        print("\nThis is expected if you haven't installed dependencies yet.")
        print("Install with: pip install pydantic-ai logfire")
