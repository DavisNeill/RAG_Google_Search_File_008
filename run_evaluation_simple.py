"""
Simple Evaluation Script - Create Your Own Dataset
===================================================

This script shows how to:
1. Create a custom evaluation dataset
2. Run your RAG system on it
3. Compare against baselines
4. Generate publication tables/figures

Perfect for domain-specific research or quick publication.
"""

import os
from enhanced_agentic_rag import EnhancedAgenticRAG, EnhancedConfig
from dataset_builder import DatasetBuilder, GroundTruthItem
from evaluation_framework import EvaluationFramework, EvaluationConfig
from baselines import VanillaRAG
import json

# Set your API key
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', 'your-api-key-here')

def create_custom_dataset():
    """
    Step 1: Create your evaluation dataset

    For a research paper, you need:
    - 50-100 questions minimum (200+ is better)
    - Ground truth answers
    - Diverse question types
    """

    builder = DatasetBuilder()

    # Example questions in your domain (replace with your own)
    questions = [
        # Factual questions
        "What is Retrieval-Augmented Generation?",
        "What are the main components of a RAG system?",
        "How does vector search work?",

        # Comparison questions
        "What is the difference between BM25 and semantic search?",
        "Compare dense retrieval and sparse retrieval methods.",

        # Analysis questions
        "Why is RAG better than fine-tuning for factual accuracy?",
        "What are the challenges in production RAG deployments?",

        # Multi-hop questions
        "How does query complexity affect model selection in RAG systems?",
        "What is the relationship between retrieval quality and generation accuracy?",

        # Add 40-90 more questions here for a solid evaluation
    ]

    # Create dataset
    dataset = builder.create_from_queries(
        questions=questions,
        dataset_name="rag_evaluation_dataset",
        dataset_description="Custom RAG evaluation dataset for publication"
    )

    # Add ground truth answers (manual annotation required)
    # For research, you need reference answers to compute metrics

    ground_truths = {
        "q_0001": "Retrieval-Augmented Generation (RAG) is a framework that combines information retrieval with language generation...",
        "q_0002": "The main components of a RAG system are: (1) a retriever that finds relevant documents, (2) a generator (LLM) that produces answers...",
        # Add ground truth for all questions
    }

    for item in dataset.items:
        if item.query_id in ground_truths:
            builder.add_ground_truth(
                dataset=dataset,
                query_id=item.query_id,
                ground_truth_answer=ground_truths[item.query_id],
                relevant_doc_ids=[],  # Add if you know which docs should be retrieved
                annotator_id="researcher_1"
            )

    # Save dataset
    builder.save_dataset(dataset, "datasets/evaluation_dataset.json")
    print(f"✅ Created dataset with {len(dataset)} questions")

    return dataset


def setup_systems():
    """
    Step 2: Set up systems to compare

    For publication, you need:
    - Your system (full)
    - At least 3 baselines
    """

    # Your full system
    config_full = EnhancedConfig()
    config_full.use_pydantic = True
    config_full.use_structured_output = True
    config_full.use_model_routing = True  # Your novel contribution
    config_full.use_hybrid_search = True
    config_full.use_reranking = True

    rag_full = EnhancedAgenticRAG(api_key=GEMINI_API_KEY, config=config_full)

    # Baseline 1: Without Pydantic (no routing)
    config_baseline = EnhancedConfig()
    config_baseline.use_pydantic = False
    config_baseline.use_hybrid_search = True
    config_baseline.use_reranking = True

    rag_baseline = EnhancedAgenticRAG(api_key=GEMINI_API_KEY, config=config_baseline)

    # Baseline 2: Simple RAG (minimal features)
    config_simple = EnhancedConfig()
    config_simple.use_hybrid_search = False  # Dense only
    config_simple.use_reranking = False
    config_simple.use_pydantic = False

    rag_simple = EnhancedAgenticRAG(api_key=GEMINI_API_KEY, config=config_simple)

    systems = {
        'Enhanced RAG (Full)': rag_full,
        'RAG (No Routing)': rag_baseline,
        'Simple RAG': rag_simple,
    }

    print(f"✅ Set up {len(systems)} systems for comparison")
    return systems


def run_evaluation(dataset, systems):
    """
    Step 3: Run the evaluation

    This runs all systems on all questions and computes metrics
    """

    # Configure evaluation
    config = EvaluationConfig(
        experiment_name="rag_cost_optimization_study",
        dataset_path="datasets/evaluation_dataset.json",
        evaluate_baselines=True,
        evaluate_ablations=True,
        compute_ragas=True,
        compute_ir_metrics=True,
        compute_semantic=True,
        compute_significance=True,
        generate_latex=True,
        generate_plots=True,
        output_dir="evaluation_results"
    )

    # Initialize framework
    framework = EvaluationFramework(config)

    # Run full evaluation
    print("🔬 Running evaluation (this may take 10-30 minutes)...")
    results = framework.run_full_evaluation(systems)

    print("\n✅ Evaluation complete!")
    print(f"📊 Results saved to: evaluation_results/")
    print(f"📈 LaTeX tables: evaluation_results/latex_tables/")
    print(f"📉 Figures: evaluation_results/figures/")

    return results


def print_results(results):
    """
    Step 4: View results
    """

    print("\n" + "="*60)
    print("EVALUATION RESULTS SUMMARY")
    print("="*60)

    for system_name, metrics in results.items():
        print(f"\n{system_name}:")
        print(f"  Recall@5: {metrics.get('recall@5', 0):.3f}")
        print(f"  NDCG@10: {metrics.get('ndcg@10', 0):.3f}")
        print(f"  BERTScore: {metrics.get('bertscore_f1', 0):.3f}")
        print(f"  Faithfulness: {metrics.get('faithfulness', 0):.3f}")
        print(f"  Avg Latency: {metrics.get('avg_latency_ms', 0):.1f}ms")
        print(f"  Cost per 1k queries: ${metrics.get('cost_per_1k', 0):.2f}")

    print("\n📁 Publication materials generated:")
    print("  - evaluation_results/latex_tables/system_comparison.tex")
    print("  - evaluation_results/latex_tables/ablation_table.tex")
    print("  - evaluation_results/figures/system_comparison.pdf")
    print("  - evaluation_results/figures/ablation_study.pdf")
    print("\n💡 Copy these directly into your paper!")


if __name__ == "__main__":
    print("="*60)
    print("RUNNING RAG EVALUATION FOR PUBLICATION")
    print("="*60)

    # Step 1: Create dataset
    print("\n📝 Step 1: Creating evaluation dataset...")
    dataset = create_custom_dataset()

    # Step 2: Setup systems
    print("\n⚙️  Step 2: Setting up systems...")
    systems = setup_systems()

    # Step 3: Upload documents to create knowledge base
    print("\n📚 Step 3: Creating knowledge base...")
    # Upload your domain documents here
    for system in systems.values():
        system.create_knowledge_base(
            store_name="evaluation_kb",
            file_paths=["your_docs/doc1.pdf", "your_docs/doc2.txt"]
            # Add all your documents
        )

    # Step 4: Run evaluation
    print("\n🔬 Step 4: Running evaluation...")
    results = run_evaluation(dataset, systems)

    # Step 5: Print results
    print_results(results)

    print("\n✅ Done! You can now write your paper using the generated materials.")
