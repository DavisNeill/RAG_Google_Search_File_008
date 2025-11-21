"""
Parent Document Retrieval
==========================

Retrieve small chunks for precision, return larger parent chunks for context.

Research Benefits:
- 15-25% better answer quality (more context)
- Better search precision (small chunks)
- Better generation quality (larger context)
- Simple but effective technique

How It Works:
1. Index small chunks (100-200 tokens) for precise search
2. When chunk is retrieved, return its parent (500-1000 tokens)
3. Best of both: precise search + rich context

Example:
  Small chunk (indexed): "Python is a high-level language"
  Parent chunk (returned): "Python is a high-level language created by
                           Guido van Rossum. It emphasizes readability...
                           [full paragraph or section]"
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class ParentChildMapping:
    """Maps child chunks to their parent documents"""
    child_id: str
    parent_id: str
    child_text: str
    parent_text: str
    child_start_pos: int
    child_end_pos: int
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ParentDocumentResult:
    """Result with parent document context"""
    query: str
    matched_child_chunks: List[Dict[str, Any]]
    retrieved_parents: List[Dict[str, Any]]
    child_to_parent_map: Dict[str, str]
    num_unique_parents: int


class ParentDocumentStore:
    """
    Stores and manages parent-child chunk relationships.

    Storage Strategy:
    - Child chunks: Small (100-200 tokens) - indexed for search
    - Parent chunks: Large (500-1000 tokens) - returned for context
    - Mapping: child_id → parent_id lookup
    """

    def __init__(self):
        """Initialize parent document store"""
        self.parent_documents: Dict[str, Dict[str, Any]] = {}
        self.child_to_parent: Dict[str, str] = {}
        self.mappings: List[ParentChildMapping] = []

        print("[ParentDocStore] Initialized")

    def add_document_with_chunks(
        self,
        parent_id: str,
        parent_text: str,
        child_chunks: List[Dict[str, Any]],
        parent_metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Add a parent document with its child chunks.

        Args:
            parent_id: Unique ID for parent document
            parent_text: Full text of parent document
            child_chunks: List of child chunk dictionaries
            parent_metadata: Optional metadata for parent
        """
        # Store parent
        self.parent_documents[parent_id] = {
            'id': parent_id,
            'text': parent_text,
            'metadata': parent_metadata or {},
            'child_count': len(child_chunks)
        }

        # Store mappings
        for child in child_chunks:
            child_id = child.get('id', child.get('chunk_id'))
            self.child_to_parent[child_id] = parent_id

            # Create mapping object
            mapping = ParentChildMapping(
                child_id=child_id,
                parent_id=parent_id,
                child_text=child.get('text', child.get('content', '')),
                parent_text=parent_text,
                child_start_pos=child.get('start_pos', 0),
                child_end_pos=child.get('end_pos', len(parent_text)),
                metadata={'chunk_index': child.get('index', 0)}
            )
            self.mappings.append(mapping)

        print(f"[ParentDocStore] Added parent '{parent_id}' with {len(child_chunks)} children")

    def get_parent_for_child(self, child_id: str) -> Optional[Dict[str, Any]]:
        """
        Get parent document for a child chunk.

        Args:
            child_id: Child chunk ID

        Returns:
            Parent document dict or None
        """
        parent_id = self.child_to_parent.get(child_id)
        if parent_id:
            return self.parent_documents.get(parent_id)
        return None

    def get_parents_for_children(
        self,
        child_ids: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Get parent documents for multiple child chunks (deduplicated).

        Args:
            child_ids: List of child chunk IDs

        Returns:
            List of unique parent documents
        """
        parent_ids = set()
        parents = []

        for child_id in child_ids:
            parent_id = self.child_to_parent.get(child_id)
            if parent_id and parent_id not in parent_ids:
                parent = self.parent_documents.get(parent_id)
                if parent:
                    parents.append(parent)
                    parent_ids.add(parent_id)

        return parents

    def get_statistics(self) -> Dict[str, Any]:
        """Get store statistics"""
        return {
            'total_parents': len(self.parent_documents),
            'total_children': len(self.child_to_parent),
            'total_mappings': len(self.mappings),
            'avg_children_per_parent': (
                len(self.child_to_parent) / len(self.parent_documents)
                if len(self.parent_documents) > 0 else 0
            )
        }


class ParentDocumentRetriever:
    """
    Retriever that searches child chunks but returns parent documents.

    This is the main interface for parent document retrieval.
    """

    def __init__(
        self,
        base_retriever: Any,
        parent_store: ParentDocumentStore,
        child_weight: float = 0.3,
        parent_weight: float = 0.7
    ):
        """
        Initialize parent document retriever.

        Args:
            base_retriever: Base retriever that searches child chunks
            parent_store: Store managing parent-child relationships
            child_weight: Weight for child chunk scores
            parent_weight: Weight for parent document scores
        """
        self.base_retriever = base_retriever
        self.parent_store = parent_store
        self.child_weight = child_weight
        self.parent_weight = parent_weight

        print(f"[ParentDocRetriever] Initialized (child_weight={child_weight}, parent_weight={parent_weight})")

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        return_children: bool = False
    ) -> ParentDocumentResult:
        """
        Retrieve parent documents by searching child chunks.

        Args:
            query: Search query
            top_k: Number of results to return
            return_children: Whether to also return matched child chunks

        Returns:
            ParentDocumentResult with parent documents
        """
        # Step 1: Search child chunks (precise)
        child_results = self._search_children(query, top_k * 2)  # Get more for deduplication

        print(f"[ParentDocRetriever] Found {len(child_results)} child chunks")

        # Step 2: Map to parent documents
        child_ids = [c.get('chunk_id', c.get('id')) for c in child_results]
        parent_documents = self.parent_store.get_parents_for_children(child_ids)

        print(f"[ParentDocRetriever] Mapped to {len(parent_documents)} unique parents")

        # Step 3: Rank and limit
        ranked_parents = self._rank_parents(
            parent_documents,
            child_results,
            top_k
        )

        # Step 4: Create mapping
        child_to_parent_map = {}
        for child_id in child_ids:
            parent_id = self.parent_store.child_to_parent.get(child_id)
            if parent_id:
                child_to_parent_map[child_id] = parent_id

        return ParentDocumentResult(
            query=query,
            matched_child_chunks=child_results if return_children else [],
            retrieved_parents=ranked_parents,
            child_to_parent_map=child_to_parent_map,
            num_unique_parents=len(ranked_parents)
        )

    def _search_children(
        self,
        query: str,
        top_k: int
    ) -> List[Dict[str, Any]]:
        """Search child chunks using base retriever"""
        try:
            if hasattr(self.base_retriever, 'search'):
                return self.base_retriever.search(query, top_k=top_k)
            elif hasattr(self.base_retriever, 'retrieve'):
                return self.base_retriever.retrieve(query, top_k=top_k)
            else:
                print("[ParentDocRetriever] Base retriever has no search/retrieve method")
                return []
        except Exception as e:
            print(f"[ParentDocRetriever] Search error: {e}")
            return []

    def _rank_parents(
        self,
        parents: List[Dict[str, Any]],
        child_results: List[Dict[str, Any]],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """
        Rank parent documents based on their children's scores.

        Strategy: Aggregate child scores for each parent
        """
        from collections import defaultdict

        # Aggregate scores per parent
        parent_scores = defaultdict(list)

        for child in child_results:
            child_id = child.get('chunk_id', child.get('id'))
            child_score = child.get('score', child.get('relevance_score', 0.0))

            parent_id = self.parent_store.child_to_parent.get(child_id)
            if parent_id:
                parent_scores[parent_id].append(child_score)

        # Calculate final scores (max + average of children)
        scored_parents = []
        for parent in parents:
            parent_id = parent['id']
            child_scores = parent_scores.get(parent_id, [0.0])

            # Combined score: max child score + average child score
            max_score = max(child_scores)
            avg_score = sum(child_scores) / len(child_scores)
            final_score = self.child_weight * max_score + self.parent_weight * avg_score

            parent['score'] = final_score
            parent['num_matching_children'] = len(child_scores)
            scored_parents.append(parent)

        # Sort by score
        scored_parents.sort(key=lambda x: x['score'], reverse=True)

        return scored_parents[:top_k]


class ParentDocumentChunker:
    """
    Helper to create parent-child chunk structure from documents.

    Chunking Strategy:
    - Parents: By paragraph or section (500-1000 tokens)
    - Children: By sentence or small paragraphs (100-200 tokens)
    """

    def __init__(
        self,
        parent_chunk_size: int = 800,
        child_chunk_size: int = 150,
        overlap: int = 50
    ):
        """
        Initialize chunker.

        Args:
            parent_chunk_size: Size of parent chunks (tokens)
            child_chunk_size: Size of child chunks (tokens)
            overlap: Overlap between chunks (tokens)
        """
        self.parent_chunk_size = parent_chunk_size
        self.child_chunk_size = child_chunk_size
        self.overlap = overlap

        print(f"[ParentDocChunker] Initialized (parent={parent_chunk_size}, child={child_chunk_size})")

    def chunk_document(
        self,
        text: str,
        document_id: str
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Chunk document into parent and child chunks.

        Args:
            text: Document text
            document_id: Document ID

        Returns:
            Tuple of (parent_chunks, child_chunks)
        """
        # Create parent chunks
        parent_chunks = self._create_chunks(
            text,
            self.parent_chunk_size,
            self.overlap,
            f"{document_id}_parent"
        )

        # Create child chunks (smaller, more granular)
        child_chunks = self._create_chunks(
            text,
            self.child_chunk_size,
            self.overlap // 2,
            f"{document_id}_child"
        )

        # Link children to parents
        for child in child_chunks:
            # Find which parent contains this child
            child_start = child['start_pos']
            child_end = child['end_pos']

            for parent in parent_chunks:
                parent_start = parent['start_pos']
                parent_end = parent['end_pos']

                # Check if child is within parent
                if child_start >= parent_start and child_end <= parent_end:
                    child['parent_id'] = parent['id']
                    break

        return parent_chunks, child_chunks

    def _create_chunks(
        self,
        text: str,
        chunk_size: int,
        overlap: int,
        id_prefix: str
    ) -> List[Dict[str, Any]]:
        """Create chunks from text"""
        chunks = []
        words = text.split()

        start_idx = 0
        chunk_idx = 0

        while start_idx < len(words):
            end_idx = min(start_idx + chunk_size, len(words))

            chunk_words = words[start_idx:end_idx]
            chunk_text = ' '.join(chunk_words)

            chunks.append({
                'id': f"{id_prefix}_{chunk_idx}",
                'text': chunk_text,
                'start_pos': start_idx,
                'end_pos': end_idx,
                'index': chunk_idx
            })

            chunk_idx += 1
            start_idx = end_idx - overlap

            if end_idx >= len(words):
                break

        return chunks


def create_parent_document_system(
    base_retriever: Any,
    parent_chunk_size: int = 800,
    child_chunk_size: int = 150
) -> Tuple[ParentDocumentRetriever, ParentDocumentStore, ParentDocumentChunker]:
    """
    Factory function to create complete parent document system.

    Args:
        base_retriever: Base retriever for child chunks
        parent_chunk_size: Size of parent chunks
        child_chunk_size: Size of child chunks

    Returns:
        Tuple of (retriever, store, chunker)
    """
    store = ParentDocumentStore()
    chunker = ParentDocumentChunker(
        parent_chunk_size=parent_chunk_size,
        child_chunk_size=child_chunk_size
    )
    retriever = ParentDocumentRetriever(
        base_retriever=base_retriever,
        parent_store=store
    )

    return retriever, store, chunker


if __name__ == "__main__":
    print("Parent Document Retrieval")
    print("=" * 60)
    print("\nConcept:")
    print("  Search with small chunks (precise)")
    print("  Return large parent chunks (contextual)")
    print("\nBenefits:")
    print("  ✓ 15-25% better answer quality")
    print("  ✓ Better search precision (small chunks)")
    print("  ✓ Better generation (more context)")
    print("  ✓ Simple but effective")
    print("\nHow It Works:")
    print("  1. Index small chunks (100-200 tokens)")
    print("  2. Search finds precise matches")
    print("  3. Return parent chunks (500-1000 tokens)")
    print("  4. Generate with rich context")
    print("\nUsage:")
    print("  retriever, store, chunker = create_parent_document_system(base_retriever)")
    print("  ")
    print("  # Chunk documents")
    print("  parents, children = chunker.chunk_document(text, doc_id)")
    print("  ")
    print("  # Add to store")
    print("  for parent in parents:")
    print("      store.add_document_with_chunks(parent['id'], parent['text'], children)")
    print("  ")
    print("  # Retrieve")
    print("  result = retriever.retrieve(query, top_k=5)")
    print("  # result.retrieved_parents contains full context!")
    print("\nExample:")
    print("-" * 60)
    print("Small Child Chunk (indexed for search):")
    print("  'Python is a high-level programming language'")
    print("")
    print("Large Parent Chunk (returned for generation):")
    print("  'Python is a high-level programming language created by")
    print("   Guido van Rossum in 1991. It emphasizes code readability")
    print("   and uses significant indentation. Python supports multiple")
    print("   programming paradigms including object-oriented, imperative,")
    print("   functional, and procedural programming...'")
    print("")
    print("→ Search precision (small chunk) + Generation quality (large chunk)!")
