"""
Baseline Implementations for Comparative Analysis
==================================================

Implements multiple baseline systems to compare against the Agentic RAG system:
1. Vanilla RAG - Standard retrieval + generation
2. RAG + Memory - With conversation memory but no agents
3. RAG + Agents - With agents but no memory
4. Query Classification RAG - Simple query routing
5. BM25 Baseline - Traditional keyword-based retrieval

Essential for journal publication to demonstrate improvements over existing methods.
"""

from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
import time
from abc import ABC, abstractmethod


@dataclass
class BaselineResult:
    """Result from a baseline system"""
    system_name: str
    question: str
    answer: str
    retrieved_contexts: List[str]
    latency_ms: float
    tokens_used: int
    metadata: Dict[str, Any] = None

    def to_dict(self) -> Dict:
        return {
            'system_name': self.system_name,
            'question': self.question,
            'answer': self.answer,
            'retrieved_contexts': self.retrieved_contexts,
            'latency_ms': self.latency_ms,
            'tokens_used': self.tokens_used,
            'metadata': self.metadata or {}
        }


class BaselineSystem(ABC):
    """Abstract base class for all baseline systems"""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def query(self, question: str, context: Dict[str, Any] = None) -> BaselineResult:
        """
        Process a query and return result

        Args:
            question: User's question
            context: Optional context (conversation history, etc.)

        Returns:
            BaselineResult object
        """
        pass

    @abstractmethod
    def reset(self):
        """Reset system state (memory, etc.)"""
        pass


class VanillaRAG(BaselineSystem):
    """
    Baseline 1: Vanilla RAG

    Standard retrieval-augmented generation without any enhancements.
    Uses simple vector similarity search and direct generation.
    """

    def __init__(self, retriever, generator, top_k: int = 5):
        """
        Initialize Vanilla RAG

        Args:
            retriever: Vector store retriever
            generator: LLM for generation
            top_k: Number of documents to retrieve
        """
        super().__init__("Vanilla RAG")
        self.retriever = retriever
        self.generator = generator
        self.top_k = top_k

        print(f"[{self.name}] Initialized (top_k={top_k})")

    def query(self, question: str, context: Dict[str, Any] = None) -> BaselineResult:
        """Simple retrieve + generate"""
        start_time = time.time()

        # Step 1: Retrieve documents (simple vector similarity)
        retrieved_docs = self.retriever.similarity_search(
            question,
            k=self.top_k
        )

        retrieved_contexts = [doc.page_content for doc in retrieved_docs]

        # Step 2: Generate answer
        prompt = self._build_prompt(question, retrieved_contexts)

        answer = self.generator.generate(prompt)
        tokens_used = len(answer.split()) * 2  # Rough estimate

        latency_ms = (time.time() - start_time) * 1000

        return BaselineResult(
            system_name=self.name,
            question=question,
            answer=answer,
            retrieved_contexts=retrieved_contexts,
            latency_ms=latency_ms,
            tokens_used=tokens_used,
            metadata={'top_k': self.top_k}
        )

    def _build_prompt(self, question: str, contexts: List[str]) -> str:
        """Build simple prompt"""
        context_str = "\n\n".join([f"Context {i+1}: {ctx}" for i, ctx in enumerate(contexts)])

        return f"""Based on the following contexts, answer the question.

{context_str}

Question: {question}

Answer:"""

    def reset(self):
        """No state to reset"""
        pass


class RAGWithMemory(BaselineSystem):
    """
    Baseline 2: RAG + Memory

    RAG system with conversation memory but no intelligent agents.
    Maintains conversation history for context-aware responses.
    """

    def __init__(self, retriever, generator, top_k: int = 5, memory_size: int = 5):
        """
        Initialize RAG with Memory

        Args:
            retriever: Vector store retriever
            generator: LLM for generation
            top_k: Number of documents to retrieve
            memory_size: Number of previous interactions to remember
        """
        super().__init__("RAG + Memory")
        self.retriever = retriever
        self.generator = generator
        self.top_k = top_k
        self.memory_size = memory_size
        self.conversation_history = []

        print(f"[{self.name}] Initialized (top_k={top_k}, memory={memory_size})")

    def query(self, question: str, context: Dict[str, Any] = None) -> BaselineResult:
        """Retrieve + generate with memory"""
        start_time = time.time()

        # Step 1: Retrieve documents
        retrieved_docs = self.retriever.similarity_search(
            question,
            k=self.top_k
        )

        retrieved_contexts = [doc.page_content for doc in retrieved_docs]

        # Step 2: Generate answer with conversation history
        prompt = self._build_prompt_with_memory(question, retrieved_contexts)

        answer = self.generator.generate(prompt)
        tokens_used = len(answer.split()) * 2

        # Step 3: Update memory
        self.conversation_history.append({
            'question': question,
            'answer': answer
        })

        # Keep only recent history
        if len(self.conversation_history) > self.memory_size:
            self.conversation_history = self.conversation_history[-self.memory_size:]

        latency_ms = (time.time() - start_time) * 1000

        return BaselineResult(
            system_name=self.name,
            question=question,
            answer=answer,
            retrieved_contexts=retrieved_contexts,
            latency_ms=latency_ms,
            tokens_used=tokens_used,
            metadata={
                'top_k': self.top_k,
                'memory_items': len(self.conversation_history)
            }
        )

    def _build_prompt_with_memory(self, question: str, contexts: List[str]) -> str:
        """Build prompt including conversation history"""
        # Add conversation history
        history_str = ""
        if self.conversation_history:
            history_str = "Previous conversation:\n"
            for i, turn in enumerate(self.conversation_history):
                history_str += f"Q{i+1}: {turn['question']}\nA{i+1}: {turn['answer']}\n\n"

        # Add contexts
        context_str = "\n\n".join([f"Context {i+1}: {ctx}" for i, ctx in enumerate(contexts)])

        return f"""{history_str}Based on the following contexts and conversation history, answer the question.

{context_str}

Current Question: {question}

Answer:"""

    def reset(self):
        """Clear conversation memory"""
        self.conversation_history = []


class RAGWithAgents(BaselineSystem):
    """
    Baseline 3: RAG + Agents

    RAG system with specialized agents but no memory.
    Uses query classification and retrieval agents.
    """

    def __init__(self, retriever, generator, query_classifier, top_k: int = 5):
        """
        Initialize RAG with Agents

        Args:
            retriever: Vector store retriever
            generator: LLM for generation
            query_classifier: Agent to classify query type
            top_k: Number of documents to retrieve
        """
        super().__init__("RAG + Agents")
        self.retriever = retriever
        self.generator = generator
        self.query_classifier = query_classifier
        self.top_k = top_k

        print(f"[{self.name}] Initialized (top_k={top_k})")

    def query(self, question: str, context: Dict[str, Any] = None) -> BaselineResult:
        """Classify query, retrieve, generate"""
        start_time = time.time()

        # Step 1: Classify query type
        query_type = self.query_classifier.classify(question)

        # Step 2: Adjust retrieval based on query type
        k = self._adjust_k_for_query_type(query_type)

        retrieved_docs = self.retriever.similarity_search(
            question,
            k=k
        )

        retrieved_contexts = [doc.page_content for doc in retrieved_docs]

        # Step 3: Generate answer
        prompt = self._build_prompt(question, retrieved_contexts, query_type)

        answer = self.generator.generate(prompt)
        tokens_used = len(answer.split()) * 2

        latency_ms = (time.time() - start_time) * 1000

        return BaselineResult(
            system_name=self.name,
            question=question,
            answer=answer,
            retrieved_contexts=retrieved_contexts,
            latency_ms=latency_ms,
            tokens_used=tokens_used,
            metadata={
                'query_type': query_type,
                'k_used': k
            }
        )

    def _adjust_k_for_query_type(self, query_type: str) -> int:
        """Adjust number of documents based on query type"""
        type_to_k = {
            'FACTUAL': 3,
            'ANALYTICAL': 5,
            'COMPARATIVE': 7,
            'TEMPORAL': 5,
            'PROCEDURAL': 4
        }
        return type_to_k.get(query_type, self.top_k)

    def _build_prompt(self, question: str, contexts: List[str], query_type: str) -> str:
        """Build prompt with query type information"""
        context_str = "\n\n".join([f"Context {i+1}: {ctx}" for i, ctx in enumerate(contexts)])

        type_instructions = {
            'FACTUAL': 'Provide a concise, fact-based answer.',
            'ANALYTICAL': 'Provide a detailed analysis.',
            'COMPARATIVE': 'Compare and contrast the relevant information.',
            'TEMPORAL': 'Focus on the timeline and sequence of events.',
            'PROCEDURAL': 'Provide step-by-step instructions.'
        }

        instruction = type_instructions.get(query_type, 'Provide a comprehensive answer.')

        return f"""Query Type: {query_type}
Instruction: {instruction}

{context_str}

Question: {question}

Answer:"""

    def reset(self):
        """No state to reset"""
        pass


class QueryClassificationRAG(BaselineSystem):
    """
    Baseline 4: Query Classification RAG

    Simple query routing based on classification.
    Routes to different retrieval strategies based on query type.
    """

    def __init__(self, retriever, generator, query_classifier):
        """
        Initialize Query Classification RAG

        Args:
            retriever: Vector store retriever
            generator: LLM for generation
            query_classifier: Query type classifier
        """
        super().__init__("Query Classification RAG")
        self.retriever = retriever
        self.generator = generator
        self.query_classifier = query_classifier

        print(f"[{self.name}] Initialized")

    def query(self, question: str, context: Dict[str, Any] = None) -> BaselineResult:
        """Classify and route query"""
        start_time = time.time()

        # Step 1: Classify query
        query_type = self.query_classifier.classify(question)

        # Step 2: Route to appropriate retrieval strategy
        retrieved_contexts = self._route_retrieval(question, query_type)

        # Step 3: Generate answer
        prompt = self._build_prompt(question, retrieved_contexts, query_type)

        answer = self.generator.generate(prompt)
        tokens_used = len(answer.split()) * 2

        latency_ms = (time.time() - start_time) * 1000

        return BaselineResult(
            system_name=self.name,
            question=question,
            answer=answer,
            retrieved_contexts=retrieved_contexts,
            latency_ms=latency_ms,
            tokens_used=tokens_used,
            metadata={'query_type': query_type}
        )

    def _route_retrieval(self, question: str, query_type: str) -> List[str]:
        """Route to different retrieval strategies"""
        # Simple routing logic
        if query_type == 'FACTUAL':
            # Use top-3 for factual
            docs = self.retriever.similarity_search(question, k=3)
        elif query_type in ['ANALYTICAL', 'COMPARATIVE']:
            # Use more documents for complex queries
            docs = self.retriever.similarity_search(question, k=7)
        else:
            # Default retrieval
            docs = self.retriever.similarity_search(question, k=5)

        return [doc.page_content for doc in docs]

    def _build_prompt(self, question: str, contexts: List[str], query_type: str) -> str:
        """Build prompt"""
        context_str = "\n\n".join([f"Context {i+1}: {ctx}" for i, ctx in enumerate(contexts)])

        return f"""Query Type: {query_type}

{context_str}

Question: {question}

Answer:"""

    def reset(self):
        """No state to reset"""
        pass


class BM25Baseline(BaselineSystem):
    """
    Baseline 5: BM25 (Traditional Keyword-based Retrieval)

    Traditional information retrieval using BM25 algorithm.
    No neural retrieval, just keyword matching.
    """

    def __init__(self, bm25_retriever, generator, top_k: int = 5):
        """
        Initialize BM25 Baseline

        Args:
            bm25_retriever: BM25 retriever instance
            generator: LLM for generation
            top_k: Number of documents to retrieve
        """
        super().__init__("BM25 Baseline")
        self.bm25_retriever = bm25_retriever
        self.generator = generator
        self.top_k = top_k

        print(f"[{self.name}] Initialized (top_k={top_k})")

    def query(self, question: str, context: Dict[str, Any] = None) -> BaselineResult:
        """BM25 retrieval + generation"""
        start_time = time.time()

        # Step 1: BM25 retrieval (keyword-based)
        retrieved_docs = self.bm25_retriever.get_relevant_documents(
            question,
            k=self.top_k
        )

        retrieved_contexts = [doc.page_content for doc in retrieved_docs]

        # Step 2: Generate answer
        prompt = self._build_prompt(question, retrieved_contexts)

        answer = self.generator.generate(prompt)
        tokens_used = len(answer.split()) * 2

        latency_ms = (time.time() - start_time) * 1000

        return BaselineResult(
            system_name=self.name,
            question=question,
            answer=answer,
            retrieved_contexts=retrieved_contexts,
            latency_ms=latency_ms,
            tokens_used=tokens_used,
            metadata={'retrieval_method': 'BM25'}
        )

    def _build_prompt(self, question: str, contexts: List[str]) -> str:
        """Build simple prompt"""
        context_str = "\n\n".join([f"Context {i+1}: {ctx}" for i, ctx in enumerate(contexts)])

        return f"""Based on the following contexts, answer the question.

{context_str}

Question: {question}

Answer:"""

    def reset(self):
        """No state to reset"""
        pass


class BaselineManager:
    """
    Manager for all baseline systems

    Facilitates running experiments on multiple baselines simultaneously.
    """

    def __init__(self):
        self.baselines: Dict[str, BaselineSystem] = {}

    def register_baseline(self, baseline: BaselineSystem):
        """Register a baseline system"""
        self.baselines[baseline.name] = baseline
        print(f"[Baseline Manager] Registered: {baseline.name}")

    def run_all_baselines(self, question: str, context: Dict[str, Any] = None) -> Dict[str, BaselineResult]:
        """
        Run all registered baselines on a single question

        Args:
            question: Question to query
            context: Optional context

        Returns:
            Dictionary mapping baseline name to result
        """
        results = {}

        for name, baseline in self.baselines.items():
            print(f"[Baseline Manager] Running {name}...")
            result = baseline.query(question, context)
            results[name] = result

        return results

    def run_batch_evaluation(
        self,
        questions: List[str],
        contexts: List[Dict[str, Any]] = None
    ) -> Dict[str, List[BaselineResult]]:
        """
        Run all baselines on a batch of questions

        Args:
            questions: List of questions
            contexts: Optional list of contexts (one per question)

        Returns:
            Dictionary mapping baseline name to list of results
        """
        if contexts is None:
            contexts = [None] * len(questions)

        results = {name: [] for name in self.baselines.keys()}

        for i, (question, context) in enumerate(zip(questions, contexts)):
            print(f"\n[Baseline Manager] Question {i+1}/{len(questions)}")

            for name, baseline in self.baselines.items():
                result = baseline.query(question, context)
                results[name].append(result)

        return results

    def reset_all(self):
        """Reset all baseline systems"""
        for baseline in self.baselines.values():
            baseline.reset()

    def get_baseline_names(self) -> List[str]:
        """Get list of registered baseline names"""
        return list(self.baselines.keys())


# Helper functions for creating standard baseline configurations

def create_standard_baselines(
    retriever,
    generator,
    query_classifier=None,
    bm25_retriever=None
) -> BaselineManager:
    """
    Create standard set of baselines for comparison

    Args:
        retriever: Vector store retriever
        generator: LLM for generation
        query_classifier: Optional query classifier
        bm25_retriever: Optional BM25 retriever

    Returns:
        BaselineManager with all baselines registered
    """
    manager = BaselineManager()

    # Baseline 1: Vanilla RAG
    manager.register_baseline(VanillaRAG(retriever, generator, top_k=5))

    # Baseline 2: RAG + Memory
    manager.register_baseline(RAGWithMemory(retriever, generator, top_k=5, memory_size=5))

    # Baseline 3: RAG + Agents (if classifier available)
    if query_classifier:
        manager.register_baseline(RAGWithAgents(retriever, generator, query_classifier, top_k=5))

    # Baseline 4: Query Classification RAG (if classifier available)
    if query_classifier:
        manager.register_baseline(QueryClassificationRAG(retriever, generator, query_classifier))

    # Baseline 5: BM25 (if BM25 retriever available)
    if bm25_retriever:
        manager.register_baseline(BM25Baseline(bm25_retriever, generator, top_k=5))

    return manager


if __name__ == "__main__":
    print("Baseline Systems for Comparative Analysis")
    print("=" * 60)
    print("\nAvailable Baselines:")
    print("1. Vanilla RAG - Standard retrieval + generation")
    print("2. RAG + Memory - With conversation memory")
    print("3. RAG + Agents - With query classification and routing")
    print("4. Query Classification RAG - Simple query routing")
    print("5. BM25 Baseline - Traditional keyword-based retrieval")
    print("\nUsage:")
    print("  manager = create_standard_baselines(retriever, generator, classifier, bm25)")
    print("  results = manager.run_batch_evaluation(questions)")
