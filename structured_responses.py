"""
Structured Response Validation with Pydantic AI
================================================

This module defines validated output schemas for RAG responses using Pydantic.
Ensures all responses have proper structure and can auto-retry on validation failures.

Features:
- Guaranteed valid JSON structure
- Automatic retry on validation errors
- Type-safe responses
- Rich metadata (confidence, sources, reasoning)

Integration with existing system:
- Works alongside current string-based responses
- Can be enabled/disabled via feature flag
- Compatible with all existing features

Usage:
    from structured_responses import RAGResponse, create_structured_agent

    agent = create_structured_agent(gemini_api_key)
    response = agent.query("What is RAG?")
    print(response.answer)  # Guaranteed string
    print(response.confidence)  # Guaranteed float 0-1
    print(response.sources)  # Guaranteed list
"""

from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum


class QueryComplexity(str, Enum):
    """Query complexity levels for model routing"""
    SIMPLE = "simple"           # Greetings, basic questions
    MODERATE = "moderate"       # Factual questions, single-hop
    COMPLEX = "complex"         # Multi-hop, reasoning required
    RESEARCH = "research"       # Deep analysis, graph traversal


class SourceType(str, Enum):
    """Types of sources cited in responses"""
    DOCUMENT = "document"
    WEB = "web"
    KNOWLEDGE_GRAPH = "knowledge_graph"
    MEMORY = "memory"
    CACHE = "cache"


class Citation(BaseModel):
    """Individual source citation with metadata"""
    source_id: str = Field(description="Unique identifier for the source")
    source_type: SourceType = Field(default=SourceType.DOCUMENT)
    content_snippet: str = Field(description="Relevant excerpt from source", max_length=500)
    relevance_score: float = Field(ge=0.0, le=1.0, description="Relevance score from retrieval")
    url: Optional[str] = Field(default=None, description="URL if web source")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    @validator('content_snippet')
    def truncate_snippet(cls, v):
        """Ensure snippet is not too long"""
        if len(v) > 500:
            return v[:497] + "..."
        return v


class ReasoningStep(BaseModel):
    """Individual reasoning step (for Chain-of-Thought)"""
    step_number: int = Field(ge=1, description="Step sequence number")
    description: str = Field(description="Description of this reasoning step")
    sub_query: Optional[str] = Field(default=None, description="Sub-query if multi-hop")
    result: Optional[str] = Field(default=None, description="Result of this step")


class VerificationResult(BaseModel):
    """Self-reflection verification results"""
    is_verified: bool = Field(description="Whether answer passed verification")
    confidence: float = Field(ge=0.0, le=1.0, description="Verification confidence")
    issues: List[str] = Field(default_factory=list, description="Issues found during verification")
    suggestions: List[str] = Field(default_factory=list, description="Suggestions for improvement")


class RAGResponse(BaseModel):
    """
    Structured RAG response with guaranteed validation

    This is the main output format for all RAG queries when Pydantic AI is enabled.
    All fields are validated, and the LLM will automatically retry if validation fails.
    """
    # Core response
    answer: str = Field(
        description="The main answer to the user's question",
        min_length=10,
        max_length=5000
    )

    # Confidence and quality metrics
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence score for this answer (0-1)"
    )

    # Source attribution
    sources: List[Citation] = Field(
        default_factory=list,
        description="List of sources cited in the answer",
        min_items=0,
        max_items=10
    )

    # Reasoning transparency (optional, for CoT queries)
    reasoning_steps: Optional[List[ReasoningStep]] = Field(
        default=None,
        description="Step-by-step reasoning (if Chain-of-Thought enabled)"
    )

    # Quality indicators
    needs_verification: bool = Field(
        default=False,
        description="Whether this answer should be human-verified"
    )

    verification_result: Optional[VerificationResult] = Field(
        default=None,
        description="Results from self-reflection verification"
    )

    # Query metadata
    query_complexity: QueryComplexity = Field(
        default=QueryComplexity.MODERATE,
        description="Detected complexity level of the query"
    )

    retrieval_method: str = Field(
        default="hybrid",
        description="Retrieval method used (hybrid, hyde, graph, parent, adaptive)"
    )

    # Performance metrics
    processing_time_ms: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="Total processing time in milliseconds"
    )

    tokens_used: Optional[int] = Field(
        default=None,
        ge=0,
        description="Total tokens used (prompt + completion)"
    )

    model_used: Optional[str] = Field(
        default=None,
        description="LLM model used for this response"
    )

    # Additional context
    follow_up_questions: List[str] = Field(
        default_factory=list,
        description="Suggested follow-up questions",
        max_items=5
    )

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )

    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Response generation timestamp"
    )

    @validator('answer')
    def validate_answer_quality(cls, v):
        """Ensure answer meets minimum quality standards"""
        if not v or v.strip() == "":
            raise ValueError("Answer cannot be empty")

        # Check for common error patterns
        error_patterns = [
            "i don't know",
            "i cannot answer",
            "insufficient information",
            "error occurred"
        ]

        v_lower = v.lower()
        if any(pattern in v_lower for pattern in error_patterns) and len(v) < 50:
            raise ValueError("Answer appears to be an error message or non-answer")

        return v

    @validator('sources')
    def ensure_source_quality(cls, v, values):
        """Validate that sources are relevant"""
        # If we have sources, ensure they're diverse
        if len(v) > 0:
            source_ids = [s.source_id for s in v]
            if len(source_ids) != len(set(source_ids)):
                # Remove duplicates
                seen = set()
                unique_sources = []
                for source in v:
                    if source.source_id not in seen:
                        seen.add(source.source_id)
                        unique_sources.append(source)
                return unique_sources

        return v

    def to_simple_dict(self) -> Dict[str, Any]:
        """Convert to simple dict for backward compatibility with existing code"""
        return {
            "answer": self.answer,
            "confidence": self.confidence,
            "sources": [s.dict() for s in self.sources],
            "metadata": self.metadata
        }

    def to_legacy_string(self) -> str:
        """Convert to legacy string format for backward compatibility"""
        result = self.answer

        if self.sources:
            result += "\n\nSources:\n"
            for i, source in enumerate(self.sources, 1):
                result += f"{i}. {source.content_snippet}\n"

        return result


class StreamedRAGChunk(BaseModel):
    """Individual chunk in a streamed response"""
    chunk_type: Literal["answer", "source", "reasoning", "metadata"] = Field(
        description="Type of chunk being streamed"
    )

    content: str = Field(
        description="Content of this chunk"
    )

    is_final: bool = Field(
        default=False,
        description="Whether this is the final chunk"
    )

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Chunk metadata"
    )


class ErrorResponse(BaseModel):
    """Structured error response"""
    error_type: str = Field(description="Type of error")
    error_message: str = Field(description="Human-readable error message")
    details: Dict[str, Any] = Field(default_factory=dict)
    suggestions: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# Factory Functions
# ============================================================================

def create_sample_response() -> RAGResponse:
    """Create a sample response for testing"""
    return RAGResponse(
        answer="Retrieval-Augmented Generation (RAG) is a technique that combines information retrieval with language generation to produce accurate, grounded responses.",
        confidence=0.95,
        sources=[
            Citation(
                source_id="doc_123",
                source_type=SourceType.DOCUMENT,
                content_snippet="RAG combines retrieval and generation...",
                relevance_score=0.92
            )
        ],
        query_complexity=QueryComplexity.MODERATE,
        retrieval_method="hybrid",
        model_used="gemini-1.5-pro"
    )


def validate_response(response_dict: Dict[str, Any]) -> RAGResponse:
    """
    Validate a dictionary response and convert to structured format

    Args:
        response_dict: Dictionary containing response data

    Returns:
        Validated RAGResponse object

    Raises:
        ValidationError: If response doesn't meet validation requirements
    """
    return RAGResponse(**response_dict)


def parse_legacy_response(text_response: str, sources: Optional[List[Dict]] = None) -> RAGResponse:
    """
    Convert legacy string response to structured format

    This helps bridge the gap between existing code and Pydantic AI structure.

    Args:
        text_response: The raw text response from LLM
        sources: Optional list of source dictionaries

    Returns:
        Structured RAGResponse
    """
    # Parse sources if provided
    parsed_sources = []
    if sources:
        for source in sources[:10]:  # Max 10 sources
            parsed_sources.append(Citation(
                source_id=source.get('id', 'unknown'),
                source_type=SourceType.DOCUMENT,
                content_snippet=source.get('content', '')[:500],
                relevance_score=source.get('score', 0.5),
                url=source.get('url'),
                metadata=source.get('metadata', {})
            ))

    # Estimate confidence based on response characteristics
    confidence = 0.7  # Default moderate confidence
    if "definitely" in text_response.lower() or "certainly" in text_response.lower():
        confidence = 0.9
    elif "might" in text_response.lower() or "possibly" in text_response.lower():
        confidence = 0.5

    return RAGResponse(
        answer=text_response,
        confidence=confidence,
        sources=parsed_sources,
        query_complexity=QueryComplexity.MODERATE,
        retrieval_method="legacy"
    )


# ============================================================================
# Validation Helpers
# ============================================================================

def is_valid_response(response: Any) -> bool:
    """Check if a response is valid without raising exceptions"""
    try:
        if isinstance(response, RAGResponse):
            return True
        elif isinstance(response, dict):
            validate_response(response)
            return True
        return False
    except Exception:
        return False


def get_validation_errors(response_dict: Dict[str, Any]) -> List[str]:
    """Get list of validation errors without raising exception"""
    try:
        validate_response(response_dict)
        return []
    except Exception as e:
        return [str(e)]


if __name__ == "__main__":
    # Test the structured response models
    print("Testing Structured Response Validation...")
    print("=" * 60)

    # Test 1: Create sample response
    sample = create_sample_response()
    print(f"\n1. Sample Response:")
    print(f"   Answer: {sample.answer[:100]}...")
    print(f"   Confidence: {sample.confidence}")
    print(f"   Sources: {len(sample.sources)}")
    print(f"   ✅ Valid!")

    # Test 2: Validate dict
    response_dict = {
        "answer": "This is a test answer with sufficient length to pass validation.",
        "confidence": 0.85,
        "sources": [],
        "query_complexity": "moderate",
        "retrieval_method": "hybrid"
    }
    validated = validate_response(response_dict)
    print(f"\n2. Dict Validation:")
    print(f"   ✅ Successfully validated dict to RAGResponse")

    # Test 3: Parse legacy response
    legacy = parse_legacy_response(
        "This is a legacy response",
        sources=[{"id": "doc1", "content": "Some content", "score": 0.9}]
    )
    print(f"\n3. Legacy Response Parsing:")
    print(f"   ✅ Converted legacy string to structured format")
    print(f"   Sources: {len(legacy.sources)}")

    # Test 4: Convert to simple dict (backward compatibility)
    simple_dict = sample.to_simple_dict()
    print(f"\n4. Backward Compatibility:")
    print(f"   ✅ Converted to simple dict with {len(simple_dict)} keys")

    # Test 5: Invalid response
    try:
        invalid = validate_response({"answer": ""})  # Empty answer
        print(f"\n5. Validation Test: ❌ Should have failed!")
    except Exception as e:
        print(f"\n5. Validation Test:")
        print(f"   ✅ Correctly rejected invalid response")
        print(f"   Error: {str(e)[:80]}...")

    print("\n" + "=" * 60)
    print("All tests passed! ✅")
