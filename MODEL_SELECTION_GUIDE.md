# Model Selection Guide

## Overview

You have **two ways** to select which LLM model to use:

1. **Manual Selection** - You pick a specific model (e.g., always use Flash)
2. **Automatic Routing** - System picks the best model based on query complexity

This guide shows you how to use both approaches.

---

## Available Models

| Model | Cost/1k tokens | Speed | Quality | Use Case |
|-------|---------------|-------|---------|----------|
| **gemini-1.5-flash** | $0.075 | ⚡⚡⚡ Fast | Good | Simple queries, high volume |
| **gemini-1.5-pro** | $1.25 | ⚡⚡ Normal | Excellent | Complex queries, critical tasks |
| **gemini-2.0-flash-exp** | $0 (preview) | ⚡ Slower | Advanced | Research, experimental features |

---

## Option 1: Manual Model Selection

### When to Use Manual Selection

✅ **Use manual selection when:**
- You want predictable, consistent costs
- Your queries are all similar complexity
- You want maximum control
- You're running high-volume simple queries (use Flash)
- You're running critical queries (use Pro)

❌ **Don't use manual selection when:**
- You have mixed complexity queries (simple + complex)
- You want automatic cost optimization
- Query complexity varies widely

---

### Method 1: Force Model in Config

The simplest way - set once, applies to all queries:

```python
from enhanced_agentic_rag import EnhancedAgenticRAG, EnhancedConfig

# Always use Flash (cheapest)
config = EnhancedConfig()
config.use_pydantic = True
config.use_structured_output = True
config.forced_model = "gemini-1.5-flash"  # 👈 Force this model

rag = EnhancedAgenticRAG(api_key='your-key', config=config)

# ALL queries will use Flash
response = rag.query_v2("Any question")
print(response.model_used)  # "gemini-1.5-flash"
```

**Available models:**
- `"gemini-1.5-flash"` - Cheapest, fastest
- `"gemini-1.5-pro"` - Balanced, high quality
- `"gemini-2.0-flash-exp"` - Experimental, free

---

### Method 2: Per-Query Override

Force a specific model for individual queries:

```python
config = EnhancedConfig()
config.use_pydantic = True
config.use_structured_output = True
config.forced_model = "gemini-1.5-flash"  # Default to Flash

rag = EnhancedAgenticRAG(api_key='your-key', config=config)

# Query 1: Use default (Flash)
response1 = rag.query_v2("Simple question")
print(response1.model_used)  # "gemini-1.5-flash"

# Query 2: Override to Pro for this one query
response2 = rag.query_v2(
    "Complex critical question",
    force_model="gemini-1.5-pro"  # 👈 Override for this query only
)
print(response2.model_used)  # "gemini-1.5-pro"

# Query 3: Back to default (Flash)
response3 = rag.query_v2("Another simple question")
print(response3.model_used)  # "gemini-1.5-flash"
```

---

### Method 3: Convenience Configurations

Use pre-configured setups:

```python
from enhanced_agentic_rag import EnhancedAgenticRAG, EnhancedConfig

# Option A: Ultra-Cheap (always Flash)
config = EnhancedConfig.pydantic_flash_config()
rag = EnhancedAgenticRAG(api_key='your-key', config=config)
# All queries use Flash ($0.075/1k tokens)

# Option B: High-Quality (always Pro)
config = EnhancedConfig.pydantic_pro_config()
rag = EnhancedAgenticRAG(api_key='your-key', config=config)
# All queries use Pro ($1.25/1k tokens)

# Option C: Automatic Routing (balanced)
config = EnhancedConfig.pydantic_auto_config()
rag = EnhancedAgenticRAG(api_key='your-key', config=config)
# Automatic routing based on complexity
```

---

## Option 2: Automatic Smart Routing

### When to Use Automatic Routing

✅ **Use automatic routing when:**
- You have mixed complexity queries (simple + complex)
- You want to optimize costs automatically
- You want the system to adapt to query complexity
- You're in production with varying query types

❌ **Don't use automatic routing when:**
- You want predictable costs
- All queries are similar complexity
- You want full control over model selection

---

### Basic Setup

```python
from enhanced_agentic_rag import EnhancedAgenticRAG, EnhancedConfig

config = EnhancedConfig()
config.use_pydantic = True
config.use_structured_output = True
config.use_model_routing = True  # 👈 Enable automatic routing
config.pydantic_cost_optimization = "balanced"  # See options below

rag = EnhancedAgenticRAG(api_key='your-key', config=config)

# System automatically selects model based on complexity
response = rag.query_v2("What is RAG?")  # → Uses Flash (simple)
response = rag.query_v2("Analyze...")     # → Uses Pro (complex)
```

---

### Optimization Levels

Choose how aggressive the cost optimization should be:

#### 1. Aggressive (Maximum Savings)

```python
config.pydantic_cost_optimization = "aggressive"
```

**Behavior:**
- Uses Flash for everything except research-level queries
- Maximum cost savings (50-60%)
- Acceptable quality for most queries

**Use when:** Cost is primary concern, quality can be "good enough"

---

#### 2. Balanced (Recommended)

```python
config.pydantic_cost_optimization = "balanced"
```

**Behavior:**
- Uses Flash for simple/moderate queries
- Uses Pro for complex queries
- Uses 2.0 for research queries
- Good balance (40-50% savings)

**Use when:** Production environment, want balance of cost and quality

---

#### 3. Quality (Minimum Savings)

```python
config.pydantic_cost_optimization = "quality"
```

**Behavior:**
- Uses Pro for most queries
- Uses 2.0 for research queries
- Only uses Flash for trivial queries
- Minimum savings (20-30%)

**Use when:** Quality is critical, cost is secondary

---

## Comparison Table

| Feature | Manual Selection | Automatic Routing |
|---------|-----------------|-------------------|
| **Cost Predictability** | ✅ High (fixed cost per query) | ⚠️ Variable (depends on queries) |
| **Cost Savings** | ⚠️ None (unless you pick cheap model) | ✅ 40-60% savings |
| **Quality** | ✅ Consistent (your chosen model) | ✅ Adaptive (best for each query) |
| **Complexity** | ✅ Simple (one setting) | ⚠️ More complex (routing logic) |
| **Control** | ✅ Full control | ⚠️ System decides |
| **Best For** | Similar complexity queries | Mixed complexity queries |

---

## Decision Tree

```
Start: What are your queries like?
│
├─ All simple queries (greetings, basic questions)
│  └─ ✅ Manual: gemini-1.5-flash
│
├─ All complex queries (analysis, reasoning)
│  └─ ✅ Manual: gemini-1.5-pro
│
├─ Mixed complexity (some simple, some complex)
│  └─ ✅ Automatic: balanced routing
│
└─ Need predictable costs
   └─ ✅ Manual: pick any model
```

---

## Real-World Examples

### Example 1: Chatbot (Simple Queries)

**Scenario:** Customer support chatbot, mostly greetings and FAQs

**Recommendation:** Manual selection (Flash)

```python
config = EnhancedConfig()
config.use_pydantic = True
config.use_structured_output = True
config.forced_model = "gemini-1.5-flash"

# Cost: ~$0.075 per 1k tokens
# Quality: Good enough for simple queries
# Predictable: Fixed cost
```

---

### Example 2: Research Assistant (Complex Queries)

**Scenario:** Academic research, complex analysis required

**Recommendation:** Manual selection (Pro)

```python
config = EnhancedConfig()
config.use_pydantic = True
config.use_structured_output = True
config.forced_model = "gemini-1.5-pro"

# Cost: ~$1.25 per 1k tokens
# Quality: Excellent
# Predictable: Fixed cost
```

---

### Example 3: General-Purpose RAG (Mixed)

**Scenario:** Production RAG with varying query complexity

**Recommendation:** Automatic routing (balanced)

```python
config = EnhancedConfig()
config.use_pydantic = True
config.use_structured_output = True
config.use_model_routing = True
config.pydantic_cost_optimization = "balanced"

# Cost: 40-50% lower than always-Pro
# Quality: Adapts to complexity
# Smart: Flash for simple, Pro for complex
```

---

### Example 4: Budget-Constrained Startup

**Scenario:** Limited budget, need to minimize costs

**Recommendation:** Manual selection (Flash) or Automatic (aggressive)

**Option A: Manual Flash (simplest)**
```python
config.forced_model = "gemini-1.5-flash"
# Minimum cost, acceptable quality
```

**Option B: Automatic Aggressive (better quality when needed)**
```python
config.use_model_routing = True
config.pydantic_cost_optimization = "aggressive"
# Still cheap, but uses Pro when really needed
```

---

## Cost Analysis

### Scenario: 10,000 queries/day, 1k tokens each

| Strategy | Model Mix | Daily Cost | Monthly Cost | Annual Cost |
|----------|-----------|------------|--------------|-------------|
| **Always Pro** | 100% Pro | $125/day | $3,750/mo | $45,000/yr |
| **Always Flash** | 100% Flash | $7.50/day | $225/mo | $2,700/yr |
| **Auto (Balanced)** | 70% Flash, 30% Pro | $42.75/day | $1,283/mo | $15,394/yr |
| **Auto (Aggressive)** | 85% Flash, 15% Pro | $25.13/day | $754/mo | $9,047/yr |

**Savings:**
- Manual Flash: $42,300/yr saved vs Always-Pro (94% savings)
- Auto Balanced: $29,606/yr saved vs Always-Pro (66% savings)
- Auto Aggressive: $35,953/yr saved vs Always-Pro (80% savings)

---

## Quick Reference

### Manual Selection (Always Flash)

```python
config = EnhancedConfig()
config.use_pydantic = True
config.use_structured_output = True
config.forced_model = "gemini-1.5-flash"
```

### Manual Selection (Always Pro)

```python
config = EnhancedConfig()
config.use_pydantic = True
config.use_structured_output = True
config.forced_model = "gemini-1.5-pro"
```

### Automatic Routing (Balanced)

```python
config = EnhancedConfig()
config.use_pydantic = True
config.use_structured_output = True
config.use_model_routing = True
config.pydantic_cost_optimization = "balanced"
```

### Per-Query Override

```python
response = rag.query_v2(
    "Question",
    force_model="gemini-1.5-pro"
)
```

### Convenience Methods

```python
# Ultra-cheap (always Flash)
config = EnhancedConfig.pydantic_flash_config()

# High-quality (always Pro)
config = EnhancedConfig.pydantic_pro_config()

# Smart routing (automatic)
config = EnhancedConfig.pydantic_auto_config()
```

---

## FAQ

### Q: Can I change models between queries?

**A:** Yes! Use per-query override:
```python
rag.query_v2("q1", force_model="gemini-1.5-flash")
rag.query_v2("q2", force_model="gemini-1.5-pro")
```

### Q: What happens if I set both `forced_model` and `use_model_routing`?

**A:** `forced_model` takes priority. Routing is disabled when a model is forced.

### Q: How do I know which model was used?

**A:** Check the response:
```python
response = rag.query_v2("Question")
print(response.model_used)  # "gemini-1.5-flash"
```

### Q: Can I use automatic routing without Pydantic AI?

**A:** No, model routing is a Pydantic AI feature. Set `use_pydantic = True`.

### Q: What's the default if I don't configure anything?

**A:** Without Pydantic AI, uses your Gemini API key's default model. With Pydantic AI enabled but no forced model or routing, defaults to `gemini-1.5-pro`.

---

## Testing Your Configuration

Run the example script:

```bash
python example_manual_model_selection.py
```

This shows:
- How to force Flash (cheap)
- How to force Pro (quality)
- How to override per query
- Comparison of manual vs automatic
- Decision guide

---

## Summary

**Choose Manual Selection when:**
- ✅ Predictable costs needed
- ✅ Similar complexity queries
- ✅ Full control desired
- ✅ Simplicity preferred

**Choose Automatic Routing when:**
- ✅ Mixed complexity queries
- ✅ Want cost optimization
- ✅ System should adapt
- ✅ Production environment

**Both options are valid** - choose based on your needs! 🚀
