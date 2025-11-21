"""
Example: Manual Model Selection
================================

This example shows how to manually select a specific model
instead of using automatic Smart Model Routing.

Use cases:
- You want to always use the cheapest model (flash)
- You want to always use the best model (pro)
- You want full control over which model is used
- You don't want automatic routing logic

Three ways to select a model:
1. Force a model in config (applies to all queries)
2. Pass model to query_v2() (per-query override)
3. Create a helper config (convenience methods)
"""

import os
from enhanced_agentic_rag import EnhancedAgenticRAG, EnhancedConfig
from structured_responses import RAGResponse


def example_1_force_flash_model():
    """Example 1: Always use Gemini Flash (cheapest, fastest)"""
    print("=" * 70)
    print("Example 1: Force Gemini Flash for ALL queries")
    print("=" * 70)
    print("\nUse case: Maximum cost savings, acceptable quality for most queries\n")

    # Configure to force Flash model
    config = EnhancedConfig()
    config.use_pydantic = True
    config.use_structured_output = True
    config.use_model_routing = False  # Disable automatic routing
    config.forced_model = "gemini-1.5-flash"  # Force this model

    rag = EnhancedAgenticRAG(
        api_key=os.getenv('GEMINI_API_KEY', 'your-api-key'),
        config=config
    )

    print("🔹 Configuration:")
    print(f"   Model Routing: DISABLED")
    print(f"   Forced Model: gemini-1.5-flash")
    print(f"   Cost: ~$0.075 per 1k tokens (cheapest)\n")

    # All queries will use Flash
    test_queries = [
        "Hello",
        "What is RAG?",
        "Explain machine learning",
        "Analyze the relationship between AI and ML"  # Even complex queries use Flash
    ]

    for query in test_queries:
        print(f"Query: {query}")
        response = rag.query_v2(query)

        if isinstance(response, RAGResponse):
            print(f"  Model used: {response.model_used}")
            print(f"  ✅ All queries use Flash!\n")


def example_2_force_pro_model():
    """Example 2: Always use Gemini Pro (best quality)"""
    print("\n" + "=" * 70)
    print("Example 2: Force Gemini Pro for ALL queries")
    print("=" * 70)
    print("\nUse case: Maximum quality, cost is not a concern\n")

    # Configure to force Pro model
    config = EnhancedConfig()
    config.use_pydantic = True
    config.use_structured_output = True
    config.use_model_routing = False  # Disable automatic routing
    config.forced_model = "gemini-1.5-pro"  # Force this model

    rag = EnhancedAgenticRAG(
        api_key=os.getenv('GEMINI_API_KEY', 'your-api-key'),
        config=config
    )

    print("🔹 Configuration:")
    print(f"   Model Routing: DISABLED")
    print(f"   Forced Model: gemini-1.5-pro")
    print(f"   Cost: ~$1.25 per 1k tokens (expensive but high quality)\n")

    # All queries will use Pro
    test_queries = [
        "Hello",  # Even simple queries use Pro (costly but consistent)
        "What is RAG?",
        "Analyze the implications of RAG on LLM accuracy"
    ]

    for query in test_queries:
        print(f"Query: {query}")
        response = rag.query_v2(query)

        if isinstance(response, RAGResponse):
            print(f"  Model used: {response.model_used}")
            print(f"  ✅ All queries use Pro!\n")


def example_3_per_query_override():
    """Example 3: Override model per query"""
    print("\n" + "=" * 70)
    print("Example 3: Per-Query Model Override")
    print("=" * 70)
    print("\nUse case: Default model with occasional overrides\n")

    # Default configuration (no forced model)
    config = EnhancedConfig()
    config.use_pydantic = True
    config.use_structured_output = True
    config.use_model_routing = False  # Disable routing
    config.forced_model = "gemini-1.5-flash"  # Default to Flash

    rag = EnhancedAgenticRAG(
        api_key=os.getenv('GEMINI_API_KEY', 'your-api-key'),
        config=config
    )

    print("🔹 Default: gemini-1.5-flash\n")

    # Query 1: Use default (Flash)
    print("Query 1 (default): What is RAG?")
    response1 = rag.query_v2("What is RAG?")
    if isinstance(response1, RAGResponse):
        print(f"  Model: {response1.model_used} (default)\n")

    # Query 2: Override to Pro
    print("Query 2 (override to Pro): Analyze complex relationships")
    response2 = rag.query_v2(
        "Analyze complex relationships",
        force_model="gemini-1.5-pro"  # Override for this query only
    )
    if isinstance(response2, RAGResponse):
        print(f"  Model: {response2.model_used} (overridden)\n")

    # Query 3: Back to default
    print("Query 3 (default again): Simple question")
    response3 = rag.query_v2("Simple question")
    if isinstance(response3, RAGResponse):
        print(f"  Model: {response3.model_used} (default again)\n")


def example_4_comparison():
    """Example 4: Compare Manual vs Automatic Routing"""
    print("\n" + "=" * 70)
    print("Example 4: Manual Selection vs Automatic Routing")
    print("=" * 70)
    print()

    test_queries = [
        "Hello",
        "What is RAG?",
        "Analyze the relationship between retrieval and generation quality"
    ]

    # Setup 1: Manual (always Flash)
    config_manual = EnhancedConfig()
    config_manual.use_pydantic = True
    config_manual.use_structured_output = True
    config_manual.use_model_routing = False
    config_manual.forced_model = "gemini-1.5-flash"

    rag_manual = EnhancedAgenticRAG(
        api_key=os.getenv('GEMINI_API_KEY', 'your-api-key'),
        config=config_manual
    )

    # Setup 2: Automatic routing
    config_auto = EnhancedConfig()
    config_auto.use_pydantic = True
    config_auto.use_structured_output = True
    config_auto.use_model_routing = True
    config_auto.pydantic_cost_optimization = "balanced"

    rag_auto = EnhancedAgenticRAG(
        api_key=os.getenv('GEMINI_API_KEY', 'your-api-key'),
        config=config_auto
    )

    print("Comparing Manual (Flash) vs Automatic Routing:\n")
    print(f"{'Query':<60} {'Manual':<25} {'Automatic':<25}")
    print("-" * 110)

    for query in test_queries:
        # Manual
        response_manual = rag_manual.query_v2(query)
        model_manual = response_manual.model_used if isinstance(response_manual, RAGResponse) else "unknown"

        # Automatic
        response_auto = rag_auto.query_v2(query)
        model_auto = response_auto.model_used if isinstance(response_auto, RAGResponse) else "unknown"

        print(f"{query[:60]:<60} {model_manual:<25} {model_auto:<25}")

    print("\n💡 Insights:")
    print("   Manual: Consistent model (Flash), lowest cost, simpler")
    print("   Automatic: Adapts to complexity, balanced cost/quality")


def example_5_convenience_configs():
    """Example 5: Convenience configuration methods"""
    print("\n" + "=" * 70)
    print("Example 5: Convenience Configuration Methods")
    print("=" * 70)
    print("\nPre-configured setups for common use cases\n")

    # Config 1: Ultra-cheap (always Flash)
    print("🔹 Setup 1: Ultra-Cheap Mode")
    config_cheap = EnhancedConfig()
    config_cheap.use_pydantic = True
    config_cheap.use_structured_output = True
    config_cheap.use_model_routing = False
    config_cheap.forced_model = "gemini-1.5-flash"
    print("   Forced model: gemini-1.5-flash")
    print("   Best for: High-volume, cost-sensitive applications")
    print("   Cost: Minimum ($0.075/1k tokens)\n")

    # Config 2: High-quality (always Pro)
    print("🔹 Setup 2: High-Quality Mode")
    config_quality = EnhancedConfig()
    config_quality.use_pydantic = True
    config_quality.use_structured_output = True
    config_quality.use_model_routing = False
    config_quality.forced_model = "gemini-1.5-pro"
    print("   Forced model: gemini-1.5-pro")
    print("   Best for: Critical queries, quality over cost")
    print("   Cost: High ($1.25/1k tokens)\n")

    # Config 3: Experimental (2.0)
    print("🔹 Setup 3: Experimental Mode")
    config_exp = EnhancedConfig()
    config_exp.use_pydantic = True
    config_exp.use_structured_output = True
    config_exp.use_model_routing = False
    config_exp.forced_model = "gemini-2.0-flash-exp"
    print("   Forced model: gemini-2.0-flash-exp")
    print("   Best for: Testing latest features, research")
    print("   Cost: Free during preview\n")

    # Config 4: Automatic (balanced routing)
    print("🔹 Setup 4: Smart Routing Mode")
    config_smart = EnhancedConfig()
    config_smart.use_pydantic = True
    config_smart.use_structured_output = True
    config_smart.use_model_routing = True
    config_smart.pydantic_cost_optimization = "balanced"
    print("   Model routing: ENABLED (balanced)")
    print("   Best for: Production, balanced cost/quality")
    print("   Cost: 40-60% savings vs always-Pro\n")


def example_6_when_to_use_what():
    """Example 6: Decision guide"""
    print("\n" + "=" * 70)
    print("Example 6: When to Use Manual vs Automatic?")
    print("=" * 70)
    print()

    decision_guide = [
        {
            "scenario": "High-volume chatbot (simple queries)",
            "recommendation": "Manual: gemini-1.5-flash",
            "reason": "Consistent low cost, acceptable quality"
        },
        {
            "scenario": "Critical business queries",
            "recommendation": "Manual: gemini-1.5-pro",
            "reason": "Maximum quality, cost less important"
        },
        {
            "scenario": "Mixed complexity (simple + complex)",
            "recommendation": "Automatic: balanced routing",
            "reason": "Best cost/quality tradeoff"
        },
        {
            "scenario": "Research/experimentation",
            "recommendation": "Manual: gemini-2.0-flash-exp",
            "reason": "Latest features, free during preview"
        },
        {
            "scenario": "Budget-constrained production",
            "recommendation": "Automatic: aggressive routing",
            "reason": "Maximum cost savings with acceptable quality"
        },
        {
            "scenario": "Predictable cost planning",
            "recommendation": "Manual: any model",
            "reason": "Fixed cost per query, easier budgeting"
        }
    ]

    for item in decision_guide:
        print(f"📌 Scenario: {item['scenario']}")
        print(f"   ✅ Recommendation: {item['recommendation']}")
        print(f"   💡 Reason: {item['reason']}\n")


if __name__ == "__main__":
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 68 + "║")
    print("║" + "   Manual Model Selection - Examples".center(68) + "║")
    print("║" + " " * 68 + "║")
    print("╚" + "=" * 68 + "╝")

    print("\n\nThis script shows how to manually select models instead of automatic routing.\n")

    try:
        # Run examples
        example_1_force_flash_model()
        example_2_force_pro_model()
        example_3_per_query_override()
        example_4_comparison()
        example_5_convenience_configs()
        example_6_when_to_use_what()

        print("\n" + "=" * 70)
        print("✅ All examples completed!")
        print("=" * 70)

        print("\n📚 Quick Reference:")
        print()
        print("# Always use Flash (cheapest)")
        print("config.forced_model = 'gemini-1.5-flash'")
        print()
        print("# Always use Pro (best quality)")
        print("config.forced_model = 'gemini-1.5-pro'")
        print()
        print("# Always use 2.0 (experimental)")
        print("config.forced_model = 'gemini-2.0-flash-exp'")
        print()
        print("# Automatic routing (balanced)")
        print("config.use_model_routing = True")
        print("config.pydantic_cost_optimization = 'balanced'")
        print()
        print("# Per-query override")
        print("rag.query_v2('question', force_model='gemini-1.5-pro')")

        print("\n💡 Pro Tip:")
        print("   Manual selection = Predictable cost, consistent behavior")
        print("   Automatic routing = Cost optimization, adapts to complexity")
        print("   Choose based on your needs!")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nNote: Examples use mock data if API key not set")
