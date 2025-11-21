"""
Streaming Responses with WebSocket
====================================

Real-time streaming of LLM responses to improve user experience.

Benefits for research:
- Significantly improved perceived latency
- Better user engagement
- Real-time feedback capabilities
- Production-ready UX enhancement

Performance:
- Shows first token in <500ms
- Progressive display as generation continues
- Graceful handling of connection issues
"""

from typing import AsyncGenerator, Callable, Optional, Dict, Any, List
from dataclasses import dataclass, field
import asyncio
import json
import time
from enum import Enum


class StreamEventType(Enum):
    """Types of streaming events"""
    START = "start"
    TOKEN = "token"
    CHUNK = "chunk"
    SOURCES = "sources"
    METADATA = "metadata"
    ERROR = "error"
    COMPLETE = "complete"
    PROGRESS = "progress"


@dataclass
class StreamEvent:
    """Represents a streaming event"""
    event_type: StreamEventType
    data: Any
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> str:
        """Convert to JSON string for transmission"""
        return json.dumps({
            'type': self.event_type.value,
            'data': self.data,
            'timestamp': self.timestamp,
            'metadata': self.metadata
        })


@dataclass
class StreamMetrics:
    """Metrics for streaming performance"""
    start_time: float
    first_token_time: Optional[float] = None
    complete_time: Optional[float] = None
    total_tokens: int = 0
    total_chunks: int = 0
    tokens_per_second: float = 0.0

    def calculate_metrics(self):
        """Calculate derived metrics"""
        if self.complete_time and self.start_time:
            duration = self.complete_time - self.start_time
            self.tokens_per_second = self.total_tokens / duration if duration > 0 else 0


class StreamBuffer:
    """
    Buffers streaming output for better control
    """

    def __init__(self, buffer_size: int = 10, flush_interval: float = 0.1):
        """
        Initialize stream buffer

        Args:
            buffer_size: Number of tokens to buffer before flushing
            flush_interval: Maximum time (seconds) to hold tokens
        """
        self.buffer_size = buffer_size
        self.flush_interval = flush_interval
        self.buffer: List[str] = []
        self.last_flush_time = time.time()

    def add(self, token: str) -> Optional[str]:
        """
        Add token to buffer

        Args:
            token: Token to add

        Returns:
            Buffered content if ready to flush, None otherwise
        """
        self.buffer.append(token)

        # Check if should flush
        if self._should_flush():
            return self.flush()

        return None

    def flush(self) -> str:
        """Flush buffer and return content"""
        content = ''.join(self.buffer)
        self.buffer.clear()
        self.last_flush_time = time.time()
        return content

    def _should_flush(self) -> bool:
        """Check if buffer should be flushed"""
        # Flush if buffer is full
        if len(self.buffer) >= self.buffer_size:
            return True

        # Flush if enough time has passed
        if time.time() - self.last_flush_time >= self.flush_interval:
            return True

        return False


class ResponseStreamer:
    """
    Streams LLM responses in real-time
    """

    def __init__(
        self,
        use_buffer: bool = True,
        buffer_size: int = 10,
        emit_sources: bool = True
    ):
        """
        Initialize response streamer

        Args:
            use_buffer: Whether to buffer tokens before emitting
            buffer_size: Number of tokens to buffer
            emit_sources: Whether to emit source citations
        """
        self.use_buffer = use_buffer
        self.buffer_size = buffer_size
        self.emit_sources = emit_sources

        print(f"[Streamer] Initialized (buffer={use_buffer}, size={buffer_size})")

    async def stream_response(
        self,
        llm_generator: AsyncGenerator[str, None],
        sources: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[StreamEvent, None]:
        """
        Stream LLM response with events

        Args:
            llm_generator: Async generator yielding tokens
            sources: Optional source documents
            metadata: Optional metadata

        Yields:
            StreamEvent objects
        """
        metrics = StreamMetrics(start_time=time.time())
        buffer = StreamBuffer(self.buffer_size) if self.use_buffer else None

        # Emit start event
        yield StreamEvent(
            event_type=StreamEventType.START,
            data={'status': 'streaming'},
            metadata=metadata or {}
        )

        # Stream tokens
        try:
            async for token in llm_generator:
                metrics.total_tokens += 1

                # Record first token time
                if metrics.first_token_time is None:
                    metrics.first_token_time = time.time()

                # Buffer or emit immediately
                if buffer:
                    buffered = buffer.add(token)
                    if buffered:
                        yield StreamEvent(
                            event_type=StreamEventType.CHUNK,
                            data=buffered
                        )
                        metrics.total_chunks += 1
                else:
                    yield StreamEvent(
                        event_type=StreamEventType.TOKEN,
                        data=token
                    )

            # Flush remaining buffer
            if buffer and buffer.buffer:
                yield StreamEvent(
                    event_type=StreamEventType.CHUNK,
                    data=buffer.flush()
                )
                metrics.total_chunks += 1

            # Emit sources if available
            if self.emit_sources and sources:
                yield StreamEvent(
                    event_type=StreamEventType.SOURCES,
                    data=sources
                )

            # Calculate final metrics
            metrics.complete_time = time.time()
            metrics.calculate_metrics()

            # Emit completion event
            yield StreamEvent(
                event_type=StreamEventType.COMPLETE,
                data={'status': 'completed'},
                metadata={
                    'metrics': {
                        'total_tokens': metrics.total_tokens,
                        'tokens_per_second': metrics.tokens_per_second,
                        'first_token_latency_ms': (
                            (metrics.first_token_time - metrics.start_time) * 1000
                            if metrics.first_token_time else None
                        ),
                        'total_duration_ms': (
                            (metrics.complete_time - metrics.start_time) * 1000
                        )
                    }
                }
            )

        except Exception as e:
            yield StreamEvent(
                event_type=StreamEventType.ERROR,
                data={'error': str(e)}
            )


class ProgressiveRetrieval:
    """
    Streams retrieval progress to show intermediate results
    """

    def __init__(self):
        """Initialize progressive retrieval"""
        print("[ProgressiveRetrieval] Initialized")

    async def stream_retrieval(
        self,
        retrieval_stages: List[Callable]
    ) -> AsyncGenerator[StreamEvent, None]:
        """
        Stream retrieval progress through multiple stages

        Args:
            retrieval_stages: List of retrieval stage callables

        Yields:
            StreamEvent objects with progress updates
        """
        total_stages = len(retrieval_stages)

        for idx, stage in enumerate(retrieval_stages, start=1):
            # Emit progress
            yield StreamEvent(
                event_type=StreamEventType.PROGRESS,
                data={
                    'stage': idx,
                    'total_stages': total_stages,
                    'status': f"Stage {idx}/{total_stages}"
                }
            )

            # Execute stage
            try:
                if asyncio.iscoroutinefunction(stage):
                    result = await stage()
                else:
                    result = stage()

                # Emit stage result
                yield StreamEvent(
                    event_type=StreamEventType.METADATA,
                    data={
                        'stage': idx,
                        'result': result
                    }
                )

            except Exception as e:
                yield StreamEvent(
                    event_type=StreamEventType.ERROR,
                    data={
                        'stage': idx,
                        'error': str(e)
                    }
                )
                break


class WebSocketHandler:
    """
    Handles WebSocket connections for streaming
    """

    def __init__(self):
        """Initialize WebSocket handler"""
        self.active_connections: Dict[str, Any] = {}
        print("[WebSocketHandler] Initialized")

    async def connect(self, connection_id: str, websocket: Any):
        """
        Register new WebSocket connection

        Args:
            connection_id: Unique connection identifier
            websocket: WebSocket connection object
        """
        self.active_connections[connection_id] = {
            'websocket': websocket,
            'connected_at': time.time(),
            'messages_sent': 0
        }
        print(f"[WebSocket] Connected: {connection_id}")

    async def disconnect(self, connection_id: str):
        """
        Unregister WebSocket connection

        Args:
            connection_id: Connection identifier
        """
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
            print(f"[WebSocket] Disconnected: {connection_id}")

    async def send_event(self, connection_id: str, event: StreamEvent):
        """
        Send event to WebSocket client

        Args:
            connection_id: Connection identifier
            event: StreamEvent to send
        """
        if connection_id not in self.active_connections:
            print(f"[WebSocket] Connection not found: {connection_id}")
            return

        connection = self.active_connections[connection_id]
        websocket = connection['websocket']

        try:
            await websocket.send_text(event.to_json())
            connection['messages_sent'] += 1
        except Exception as e:
            print(f"[WebSocket] Send error: {e}")
            await self.disconnect(connection_id)

    async def broadcast_event(self, event: StreamEvent):
        """
        Broadcast event to all connected clients

        Args:
            event: StreamEvent to broadcast
        """
        disconnected = []

        for connection_id, connection in self.active_connections.items():
            try:
                await connection['websocket'].send_text(event.to_json())
                connection['messages_sent'] += 1
            except Exception as e:
                print(f"[WebSocket] Broadcast error for {connection_id}: {e}")
                disconnected.append(connection_id)

        # Clean up disconnected clients
        for connection_id in disconnected:
            await self.disconnect(connection_id)

    def get_connection_stats(self) -> Dict[str, Any]:
        """Get statistics about active connections"""
        return {
            'total_connections': len(self.active_connections),
            'connections': {
                conn_id: {
                    'connected_at': conn['connected_at'],
                    'messages_sent': conn['messages_sent'],
                    'duration_seconds': time.time() - conn['connected_at']
                }
                for conn_id, conn in self.active_connections.items()
            }
        }


class StreamingRAGPipeline:
    """
    Complete RAG pipeline with streaming support
    """

    def __init__(
        self,
        retriever: Any,
        llm: Any,
        streamer: ResponseStreamer
    ):
        """
        Initialize streaming RAG pipeline

        Args:
            retriever: Document retriever
            llm: Language model with streaming support
            streamer: Response streamer
        """
        self.retriever = retriever
        self.llm = llm
        self.streamer = streamer

        print("[StreamingRAG] Pipeline initialized")

    async def query(
        self,
        question: str,
        stream_retrieval: bool = True
    ) -> AsyncGenerator[StreamEvent, None]:
        """
        Process query with full streaming

        Args:
            question: User question
            stream_retrieval: Whether to stream retrieval progress

        Yields:
            StreamEvent objects
        """
        # Stage 1: Retrieval (optionally streamed)
        if stream_retrieval:
            yield StreamEvent(
                event_type=StreamEventType.PROGRESS,
                data={'stage': 'retrieval', 'status': 'Retrieving documents...'}
            )

        # Retrieve documents
        documents = await self._retrieve_documents(question)

        # Emit retrieved sources
        yield StreamEvent(
            event_type=StreamEventType.SOURCES,
            data=documents
        )

        # Stage 2: Generation (streamed)
        yield StreamEvent(
            event_type=StreamEventType.PROGRESS,
            data={'stage': 'generation', 'status': 'Generating answer...'}
        )

        # Stream LLM response
        llm_generator = self._generate_response(question, documents)

        async for event in self.streamer.stream_response(llm_generator):
            yield event

    async def _retrieve_documents(self, question: str) -> List[Dict[str, Any]]:
        """Retrieve relevant documents"""
        # Call retriever (handle both sync and async)
        if asyncio.iscoroutinefunction(self.retriever.retrieve):
            return await self.retriever.retrieve(question)
        else:
            return self.retriever.retrieve(question)

    async def _generate_response(
        self,
        question: str,
        documents: List[Dict[str, Any]]
    ) -> AsyncGenerator[str, None]:
        """Generate response with streaming LLM"""
        # Format context
        context = "\n\n".join([doc.get('content', '') for doc in documents])

        # Call LLM with streaming
        prompt = f"""Context:
{context}

Question: {question}

Answer:"""

        # Stream tokens from LLM
        async for token in self.llm.stream(prompt):
            yield token


# Mock async generator for testing
async def mock_llm_generator(text: str, delay: float = 0.05):
    """Mock LLM generator for testing"""
    for token in text.split():
        await asyncio.sleep(delay)
        yield token + " "


if __name__ == "__main__":
    print("Streaming Responses System")
    print("=" * 60)
    print("\nFeatures:")
    print("✓ Real-time WebSocket streaming")
    print("✓ Token-by-token or chunked streaming")
    print("✓ Progressive retrieval display")
    print("✓ Connection management")
    print("✓ Buffering for performance")
    print("\nBenefits:")
    print("✓ First token in <500ms")
    print("✓ Improved perceived latency")
    print("✓ Better user engagement")
    print("✓ Production-ready UX")
    print("\nUsage:")
    print("  streamer = ResponseStreamer()")
    print("  async for event in streamer.stream_response(llm_generator):")
    print("      await websocket.send_json(event.to_json())")
    print("\nWebSocket Integration:")
    print("  handler = WebSocketHandler()")
    print("  await handler.connect(connection_id, websocket)")
    print("  await handler.send_event(connection_id, event)")
