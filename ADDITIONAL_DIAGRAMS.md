# Additional UML Diagrams for Thesis

## State Diagram & Activity Diagram

These diagrams provide additional perspectives on your system for comprehensive thesis documentation.

---

## State Diagram: Query Processing States

**Purpose:** Shows the states a query goes through during processing

**File:** `state_diagram.puml`

```plantuml
@startuml state_diagram
!theme plain
skinparam backgroundColor white

title Query Processing State Machine

[*] --> Received : User submits query

Received --> Analyzing : Start processing
Analyzing : entry / Log query
Analyzing : do / Analyze complexity
Analyzing : do / Check cache

Analyzing --> Cached : Cache hit
Analyzing --> NeedsRetrieval : Cache miss, requires retrieval
Analyzing --> DirectAnswer : Can answer without retrieval

Cached --> Formatting : Retrieve from cache
Cached : entry / Increment cache hits
Cached : do / Load cached response

NeedsRetrieval --> QueryRewriting : Preprocessing
QueryRewriting : entry / Start query processor
QueryRewriting : do / Rewrite/expand query
QueryRewriting : exit / Select best query

QueryRewriting --> Retrieving : Enhanced query ready
Retrieving : entry / Select retrieval method
Retrieving : do / Hybrid search OR HyDE OR GraphRAG
Retrieving : do / Retrieve candidates

Retrieving --> Reranking : Candidates retrieved
Reranking : entry / Load cross-encoder
Reranking : do / Score all candidates
Reranking : do / Sort by relevance

Reranking --> Generating : Top-k selected
Generating : entry / Select model (routing)
Generating : do / Apply Chain-of-Thought
Generating : do / Call LLM
Generating : exit / Receive raw answer

Generating --> Validating : Answer generated
Validating : entry / Self-reflection
Validating : do / Check consistency
Validating : do / Verify groundedness
Validating : do / Score confidence

Validating --> Failed : Validation failed
Validating --> Formatting : Validation passed

Failed --> Generating : Retry with corrections
Failed : entry / Log failure
Failed : do / Improve prompt

DirectAnswer --> Generating : Generate without retrieval
DirectAnswer : entry / Use memory/knowledge
DirectAnswer : do / No retrieval needed

Formatting --> StructuredOutput : Pydantic enabled
Formatting --> LegacyOutput : Pydantic disabled

StructuredOutput : entry / Create RAGResponse
StructuredOutput : do / Validate with Pydantic
StructuredOutput : do / Populate all fields

StructuredOutput --> Validated : Validation success
StructuredOutput --> RetryStructuring : Validation error

RetryStructuring --> Generating : Auto-retry
RetryStructuring : entry / Increment retry count
RetryStructuring : do / Adjust prompt

Validated --> Caching : Cache enabled
LegacyOutput --> Caching : Cache enabled
Validated --> Logging : Cache disabled
LegacyOutput --> Logging : Cache disabled

Caching : entry / Store in cache
Caching : do / Set TTL
Caching --> Logging

Logging : entry / End trace
Logging : do / Update statistics
Logging : do / Save to Logfire
Logging --> [*] : Return response

note right of NeedsRetrieval
  Adaptive Retrieval Decision:
  • Analyze query type
  • Check if retrieval needed
  • 30-40% queries skip retrieval
end note

note right of Generating
  Model Routing:
  • Simple → Flash ($)
  • Complex → Pro ($$$)
  • 40-60% cost savings
end note

note bottom of StructuredOutput
  Novel Contribution:
  Type-safe validation
  with auto-retry
end note

@enduml
```

---

## Activity Diagram: Multi-Hop Reasoning Workflow

**Purpose:** Shows the workflow for processing complex multi-hop questions

**File:** `activity_multihop.puml`

```plantuml
@startuml activity_multihop
!theme plain
skinparam backgroundColor white

title Multi-Hop Reasoning Activity Diagram

start

:Receive Complex Query;
note right
  Example: "Compare the accuracy of
  RAG systems using BM25 vs
  dense retrieval for technical docs"
end note

:Analyze Query Complexity;

if (Is Multi-Hop?) then (yes)
  :Activate Multi-Hop Reasoner;

  :Decompose into Sub-Questions;
  note right
    Sub-Q1: "What is RAG accuracy with BM25?"
    Sub-Q2: "What is RAG accuracy with dense retrieval?"
    Sub-Q3: "How do they compare?"
  end note

  partition "For Each Sub-Question" {
    fork
      :Process Sub-Q1;
      :Retrieve Documents (BM25);
      :Generate Answer 1;
    fork again
      :Process Sub-Q2;
      :Retrieve Documents (Dense);
      :Generate Answer 2;
    fork again
      :Process Sub-Q3;
      :Load Previous Answers;
      :Compare Results;
    end fork
  }

  :Aggregate Answers;
  note right
    Combine sub-answers into
    coherent final answer
  end note

  :Apply Chain-of-Thought;
  note right
    Step 1: Analyze BM25 results
    Step 2: Analyze Dense results
    Step 3: Compare metrics
    Step 4: Draw conclusion
  end note

else (no)
  :Process as Single-Hop;

  :Retrieve Relevant Documents;

  :Generate Answer;
endif

:Self-Reflection Validation;

if (Validation Passed?) then (yes)
  :Format as RAGResponse;
else (no)
  :Identify Issues;

  if (Can Auto-Correct?) then (yes)
    :Apply Corrections;
    :Regenerate Answer;
  else (no)
    :Flag for Manual Review;
  endif
endif

:Cache Result;

:Log to Observability;

:Return to User;

stop

@enduml
```

---

## Activity Diagram: Model Routing Decision

**Purpose:** Shows how the system decides which model to use

**File:** `activity_routing.puml`

```plantuml
@startuml activity_routing
!theme plain
skinparam backgroundColor white

title Smart Model Routing - Activity Diagram

start

:Receive Query;

if (Manual Model Forced?) then (yes)
  :Use Forced Model;
  note right
    config.forced_model = "gemini-1.5-flash"
    All queries use this model
  end note
  stop
else (no)
  if (Model Routing Enabled?) then (yes)
    :Analyze Query;

    partition "Query Analysis" {
      :Extract Patterns;
      :Count Complexity Indicators;
      :Calculate Word Count;
      :Check Question Type;
    }

    :Calculate Complexity Score;

    if (Score < 0.3) then (SIMPLE)
      :Select gemini-1.5-flash;
      note right
        Cost: $0.075/1k tokens
        Use cases:
        • Greetings
        • Basic factual questions
        • Simple "what is" queries
      end note

    elseif (Score < 0.6) then (MODERATE)
      if (Cost Optimization = Aggressive?) then (yes)
        :Select gemini-1.5-flash;
      else (no)
        :Select gemini-1.5-flash;
      endif

    elseif (Score < 0.9) then (COMPLEX)
      :Select gemini-1.5-pro;
      note right
        Cost: $1.25/1k tokens
        Use cases:
        • Analysis
        • Reasoning
        • Comparisons
      end note

    else (RESEARCH)
      :Select gemini-2.0-flash-exp;
      note right
        Cost: $0 (preview)
        Use cases:
        • Deep analysis
        • Relationship queries
        • Frontier research
      end note
    endif

    :Record Decision;
    :Update Cost Tracker;

  else (no)
    :Use Default Model;
    note right
      Default: gemini-1.5-pro
    end note
  endif
endif

:Execute Query with Selected Model;

:Track Token Usage;

:Calculate Cost;

:Update Savings Statistics;

stop

@enduml
```

---

## Activity Diagram: Pydantic Validation Flow

**Purpose:** Shows structured output validation with retry logic

**File:** `activity_validation.puml`

```plantuml
@startuml activity_validation
!theme plain
skinparam backgroundColor white

title Pydantic Structured Output Validation

start

:LLM Generates Raw Response;

if (Structured Output Enabled?) then (yes)
  :Attempt to Parse JSON;

  if (Valid JSON?) then (yes)
    :Create RAGResponse Object;

    partition "Pydantic Validation" {
      :Validate answer field;
      note right: Must be 10-5000 chars

      :Validate confidence field;
      note right: Must be 0.0-1.0

      :Validate sources field;
      note right: Max 10 sources

      :Validate all other fields;
    }

    if (All Fields Valid?) then (yes)
      :RAGResponse Created ✓;
      note right
        Type-safe object:
        • Guaranteed valid
        • All fields present
        • Proper types
      end note

    else (no)
      :Collect Validation Errors;

      if (Retry Count < Max?) then (yes)
        :Increment Retry Count;
        :Generate Improved Prompt;
        note right
          Prompt includes:
          • Validation errors
          • Expected format
          • Examples
        end note
        :Re-query LLM;
        backward :Parse Response;
      else (no)
        :Create Fallback Response;
        note right
          Use partial data
          + default values
        end note
      endif
    endif

  else (no)
    :Log Parse Error;

    if (Retry Count < Max?) then (yes)
      :Retry with Better Prompt;
      backward :LLM Generates;
    else (no)
      :Parse as Legacy String;
      :Convert to RAGResponse;
    endif
  endif

else (no)
  :Return Raw Dict;
  note right: Legacy mode
endif

:Return Response;

stop

@enduml
```

---

## Swimlane Diagram: System Components Interaction

**Purpose:** Shows which components handle which parts of the process

**File:** `swimlane_diagram.puml`

```plantuml
@startuml swimlane_diagram
!theme plain
skinparam backgroundColor white

title Component Responsibilities - Swimlane Diagram

|User|
start
:Submit Query;

|EnhancedRAG|
:Receive Query;
:Load Configuration;

|PydanticWrapper|
if (Pydantic Enabled?) then (yes)
  :Start Trace;

  |ModelRouter|
  :Analyze Complexity;
  :Select Model;
  note right
    Flash vs Pro decision
    Saves 40-60% costs
  end note

  |PydanticWrapper|
else (no)
  |EnhancedRAG|
endif

|AdaptiveRetrieval|
:Check if Retrieval Needed;

if (Need Retrieval?) then (yes)
  |HybridSearch|
  :Execute BM25;
  :Execute Dense Search;
  :Fuse Results (RRF);

  |Reranker|
  :Score with Cross-Encoder;
  :Select Top-K;
else (no)
  |AdaptiveRetrieval|
  :Answer from Memory;
  note right: 30-40% queries
endif

|ChainOfThought|
:Enhance Prompt;
:Add Reasoning Steps;

|LLM (Gemini)|
:Generate Response;

|SelfReflection|
:Validate Answer;
:Check Consistency;
:Score Confidence;

if (Pydantic Enabled?) then (yes)
  |StructuredOutput|
  :Parse to RAGResponse;
  :Validate All Fields;

  if (Valid?) then (yes)
    :RAGResponse ✓;
  else (no)
    :Auto-Retry;
    |LLM (Gemini)|
    backward :Regenerate;
  endif

  |Observability|
  :Log Trace;
  :Update Stats;
else (no)
  |EnhancedRAG|
  :Return Dict;
endif

|User|
:Receive Response;
stop

@enduml
```

---

## Comparison: Before vs After Pydantic AI

**File:** `comparison_diagram.puml`

```plantuml
@startuml comparison_diagram
!theme plain
skinparam backgroundColor white

title System Evolution: Before vs After Pydantic AI

rectangle "Before (Baseline RAG)" as before {
  component "Query" as q1
  component "Retrieval" as r1
  component "LLM" as llm1
  component "Response (String)" as resp1

  q1 --> r1
  r1 --> llm1
  llm1 --> resp1

  note bottom of resp1
    Issues:
    • Unvalidated string
    • No type safety
    • Always use same model (expensive)
    • No tracing
    • Parse errors
  end note
}

rectangle "After (With Pydantic AI)" as after {
  component "Query" as q2
  component "Model Router" as router
  component "Retrieval" as r2
  component "LLM (Selected)" as llm2
  component "Validator" as val
  component "RAGResponse (Typed)" as resp2
  component "Observability" as obs

  q2 --> router : analyze
  router --> r2 : select Flash or Pro
  r2 --> llm2
  llm2 --> val : validate
  val --> resp2
  router --> obs : log
  val --> obs : trace

  note right of router
    **New: Smart Routing**
    • 40-60% cost savings
    • Automatic selection
  end note

  note right of resp2
    **New: Structured Output**
    • Type-safe
    • Validated
    • Auto-retry
  end note

  note right of obs
    **New: Observability**
    • Full tracing
    • Statistics
    • Debug logs
  end note
}

note as improvements
  **Improvements:**
  1. Cost: 40-60% reduction
  2. Quality: Type-safe responses
  3. Reliability: Auto-validation & retry
  4. Debugging: Full observability
  5. Predictability: Consistent structure
end note

@enduml
```

---

## State Diagram: Observability Trace Lifecycle

**File:** `trace_states.puml`

```plantuml
@startuml trace_states
!theme plain
skinparam backgroundColor white

title Query Trace Lifecycle

[*] --> Created : start_trace()

Created : entry / Generate trace_id
Created : entry / Record start_time
Created : entry / Log query text

Created --> Active : Begin processing

Active : do / Record model selection
Active : do / Record retrieval method
Active : do / Track API calls
Active : do / Measure latency

Active --> Completed : Success
Active --> Failed : Error

Completed : entry / Calculate duration
Completed : entry / Record metrics
Completed : do / Update success count
Completed : do / Calculate cost

Failed : entry / Log error
Failed : entry / Record stack trace
Failed : do / Update failure count

Completed --> Logged : end_trace()
Failed --> Logged : end_trace()

Logged : entry / Write to file
Logged : entry / Update statistics
Logged : do / Save JSON
Logged : do / Trigger alerts if needed

Logged --> [*]

note right of Active
  Tracked Metrics:
  • Duration (ms)
  • Model used
  • Tokens consumed
  • Cost ($)
  • Success/failure
end note

note right of Logged
  Persisted Data:
  • ./logs/pydantic/traces_*.jsonl
  • Queryable for analysis
  • Exportable to tools
end note

@enduml
```

---

## Summary

You now have **7 additional diagrams**:

### State Diagrams (2)
1. ✅ **Query Processing States** - Shows lifecycle of a query
2. ✅ **Trace Lifecycle** - Shows observability state machine

### Activity Diagrams (4)
3. ✅ **Multi-Hop Reasoning** - Complex question workflow
4. ✅ **Model Routing** - Decision tree for model selection
5. ✅ **Pydantic Validation** - Validation with retry logic
6. ✅ **Component Swimlane** - Who does what

### Comparison Diagram (1)
7. ✅ **Before/After Pydantic** - Shows your contribution

---

## When to Use Each Diagram

### For Thesis Introduction
- High-level architecture (from PLANTUML_DIAGRAMS.md)
- Before/After comparison (shows contribution)

### For Methodology Chapter
- Query processing state diagram (shows algorithm)
- Multi-hop activity diagram (shows complex logic)
- Component swimlane (shows interaction)

### For Implementation Chapter
- Class diagram (from PLANTUML_DIAGRAMS.md)
- Model routing activity (shows decision logic)
- Validation flow (shows error handling)

### For Novel Contributions
- Pydantic integration (from PLANTUML_DIAGRAMS.md)
- Model routing activity (shows cost optimization)
- Before/After comparison (quantifies improvement)

### For Results/Evaluation
- Trace lifecycle (shows observability)
- Before/After comparison (shows impact)

---

## Generation Instructions

```bash
# Generate all additional diagrams
plantuml state_diagram.puml
plantuml activity_multihop.puml
plantuml activity_routing.puml
plantuml activity_validation.puml
plantuml swimlane_diagram.puml
plantuml comparison_diagram.puml
plantuml trace_states.puml

# Or generate all at once
plantuml *.puml
```

---

## LaTeX Integration Example

```latex
\section{System Behavior}

\subsection{Query Processing Lifecycle}

Figure \ref{fig:state} illustrates the state machine governing
query processing. Each query transitions through states from
reception to final response, with branch points for caching,
retrieval decisions, and validation.

\begin{figure}[htbp]
    \centering
    \includegraphics[width=\textwidth]{state_diagram.pdf}
    \caption{State diagram showing query processing lifecycle}
    \label{fig:state}
\end{figure}

\subsection{Multi-Hop Reasoning Workflow}

For complex queries requiring multiple reasoning steps, our system
implements a decomposition-aggregation strategy (Figure \ref{fig:multihop}).

\begin{figure}[htbp]
    \centering
    \includegraphics[width=0.8\textwidth]{activity_multihop.pdf}
    \caption{Activity diagram for multi-hop reasoning}
    \label{fig:multihop}
\end{figure}
```

---

## Professional Tips

1. **Don't Overload with Diagrams**
   - Choose 5-7 most relevant
   - Mix types (class, sequence, state, activity)
   - Each should add new insight

2. **Maintain Consistency**
   - Same naming across diagrams
   - Consistent color scheme
   - Similar layout style

3. **Link Diagrams to Text**
   - Reference every figure: "As shown in Figure X..."
   - Explain what the diagram shows
   - Discuss key insights

4. **Quality Over Quantity**
   - Better to have 5 perfect diagrams
   - Than 15 mediocre ones
   - Each should earn its space

**You now have 13 professional diagrams total!** 🎓
