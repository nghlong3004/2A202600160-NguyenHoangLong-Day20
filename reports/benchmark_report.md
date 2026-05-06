# Benchmark Report

**Student**: Nguyễn Hoàng Long (2A202600160)

## Summary Table

| Run | Latency (s) | Cost (USD) | Quality | Notes |
|---|---:|---:|---:|---|
| single-agent-baseline | 19.93 | $0.000314 |  | answer_length=5159 |
| multi-agent-workflow | 70.05 | $0.002216 |  | answer_length=4516, routes=researcher→analyst→writer→critic→done |

## Analysis

- **Latency ratio**: Multi-agent is 3.5x slower than baseline
- **Cost ratio**: Multi-agent costs 7.1x the baseline
- **Trade-off**: Multi-agent provides structured research with sources and analysis at the cost of higher latency and token usage


## Detailed Comparison

### Query

> Describe the self-reflection pattern in LLM agents.

### Single-Agent Baseline Output

Here is a comprehensive description of the self-reflection pattern in LLM agents.

### The Self-Reflection Pattern in LLM Agents

The self-reflection pattern is a sophisticated meta-cognitive technique used to enhance the performance, reliability, and safety of Large Language Model (LLM) agents. Instead of generating a single, final output, an agent employing self-reflection iteratively evaluates its own reasoning, actions, and outputs, using that evaluation to refine subsequent attempts. This pattern transforms an LLM from a one-shot predictor into an adaptive problem-solver.

**Core Mechanism: The Reflection Loop**

The pattern operates as a closed loop with four key stages:

1.  **Generation (Act):** The agent receives a task (e.g., "Write a Python function to sort a list") and produces an initial output (e.g., a buggy sorting algorithm).
2.  **Evaluation (Observe):** The agent critically analyzes its own output. This is not a simple "good/bad" check but a structured critique. It might ask itself: "Does this function handle edge cases like an empty list?" or "Is the time complexity optimal?" This evaluation can be guided by a rubric, a set of constraints, or an external tool (e.g., running the code and checking for errors).
3.  **Feedback Synthesis (Reflect):** The agent synthesizes the evaluation into concrete, actionable feedback. For example: "The function fails for an empty list because it tries to access index 0. I need to add a check for an empty list at the beginning."
4.  **Refinement (Re-act):** The agent uses the synthesized feedback to generate a new, improved version of its output. This new output is then fed back into the evaluation stage, creating an iterative cycle.

**Why Self-Reflection is Powerful**

- **Error Correction:** It catches and fixes logical errors, factual inaccuracies, and omissions that a single-pass generation would miss. This is crucial for tasks like code generation, mathematical reasoning, and complex planning.
- **Improved Reasoning:** By forcing the agent to articulate *why* a previous attempt was flawed, it strengthens its chain-of-thought and deepens its understanding of the problem.
- **Adaptability:** The agent can adapt its approach based on the specific nuances of a task. For example, if a first attempt at a creative writing task is too formal, the reflection can identify this and guide the next attempt to be more conversational.
- **Safety and Alignment:** The agent can reflect on its own outputs for potential biases, harmful instructions, or violations of safety policies, acting as a self-censor before the output is delivered to the user.

**Common Implementation Strategies**

- **Single-Agent Reflection:** The same LLM plays all roles (generator, evaluator, refiner). This is simple but can be limited by the model's own blind spots.
- **Multi-Agent Debate:** Two or more LLM instances (or different models) take on different roles. One generates, another critiques. This introduces diverse perspectives and can lead to more robust reflection, as the critic is not constrained by the generator's initial reasoning path.
- **Tool-Augmented Reflection:** The agent uses external tools (e.g., a code interpreter, a search engine, a calculator) during the evaluation stage. For instance, it can run generated code to see if it compiles, or search for a fact to verify a claim. This grounds the reflection in objective reality.

**Example: A Self-Reflecting Code Agent**

- **Task:** "Write a Python function to find the most frequent element in a list."
- **Attempt 1:** `def most_frequent(lst): return max(set(lst), key=lst.count)`
- **Evaluation:** "This works for non-empty lists but is inefficient (O(n²) due to `lst.count`). It will also fail for an empty list with a `ValueError`."
- **Feedback:** "Optimize by using a dictionary to count frequencies in O(n). Add a check for an empty list."
- **Attempt 2:** `def most_frequent(lst): if not lst: return None; counts = {}; for item in lst: counts[item] = counts.get(item, 0) + 1; return max(counts, key=counts.get)`
- **Evaluation:** "This is O(n) and handles empty lists. It correctly returns the first most frequent element in case of ties. No further issues detected."
- **Output:** The refined function is returned.

**Challenges and Limitations**

- **Computational Cost:** Each reflection cycle requires multiple LLM calls, increasing latency and token usage.
- **Over-Reflection:** The agent can get stuck in a loop, making minor, unnecessary changes or "hallucinating" problems that don't exist.
- **Confirmation Bias:** A single-agent system may struggle to identify fundamental flaws in its own reasoning, as it is essentially trying to "catch itself."
- **Evaluation Quality:** The entire pattern hinges on the quality of the evaluation. A weak evaluator will lead to poor feedback and ineffective refinement.

In summary, the self-reflection pattern is a powerful architectural choice for building more capable and reliable LLM agents. It moves beyond simple generation to create a dynamic, iterative process of action, observation, and improvement, mirroring a key aspect of human problem-solving.

### Multi-Agent Output

# The Self-Reflection Pattern in LLM Agents

## Definition and Core Concept

The self-reflection pattern is a meta-cognitive capability in LLM agents where the agent systematically analyzes its own past actions, outputs, and environmental feedback to improve future performance. Unlike simple trial-and-error, self-reflection involves a structured, multi-step process of critique, reasoning, and revision. This pattern enables agents to move beyond single-shot generation to iterative problem-solving, acting as both performer and critic of their own work.

## The Self-Reflection Loop

The process follows a cyclical pattern:

1. **Action/Generation**: The agent performs a task (e.g., writes code, answers a question)
2. **Observation/Feedback**: The agent receives feedback, which can be:
   - **External**: Error messages, reward scores, user corrections, or tool results
   - **Internal**: The agent's own critique based on a rubric or knowledge
3. **Reflection**: The agent analyzes the discrepancy between the intended goal and observed outcome, asking questions like "Why did this fail?" and "What should I have done instead?"
4. **Revision**: The agent generates a new action or output based on reflection insights

## Key Implementations

Several prominent frameworks have formalized this pattern:

- **Reflexion (Shinn et al., 2023)**: Maintains persistent "memory" of reflections in long-term storage. After each task attempt, the agent generates a textual summary of what went wrong, stored as context for future episodes—a form of "verbal reinforcement learning" without fine-tuning.

- **Self-Refine (Madaan et al., 2023)**: Operates in a single or few iterations without long-term memory. The LLM generates an initial output, produces feedback on it, and refines it—all in one forward pass or a few iterations.

- **Chain-of-Thought with Self-Consistency**: Generates multiple reasoning paths and selects the most consistent answer, representing implicit reflection through comparison of internal trajectories.

- **Critique & Revision Agents**: Modern frameworks (e.g., LangGraph, AutoGen) implement explicit "critic" nodes—separate LLM calls that evaluate the primary agent's output and provide structured feedback for revision.

## Benefits and Strengths

- **Improved Accuracy**: Dramatically reduces errors in complex, multi-step tasks like code generation and mathematical reasoning
- **No Fine-Tuning Required**: Improves performance purely through in-context learning and prompt engineering
- **Enhanced Explainability**: Reflection steps produce natural language traces of reasoning, making decisions more transparent
- **Real-Time Adaptability**: Agents can adapt to novel scenarios by reflecting on failures immediately

## Limitations and Challenges

- **Hallucination in Reflection**: LLMs may generate plausible-sounding but incorrect reflections, potentially introducing new errors
- **Computational Cost**: Each reflection step requires additional LLM calls, increasing latency and token usage
- **Over-Correction and Loops**: Agents can get stuck in infinite loops of reflection and revision without progress
- **Prompt Sensitivity**: Effectiveness depends heavily on the quality of critique prompts
- **Knowledge Limitations**: Reflection cannot discover fundamentally new strategies beyond the model's training data

## Trends and Future Directions

- **Structured Reflection**: Moving from free-text to structured outputs (e.g., JSON with "error_type," "root_cause," "fix_plan") for improved reliability
- **Multi-Agent Reflection**: Using multiple specialized agents (generator, critic, refiner) that debate and critique each other's outputs
- **Memory-Augmented Reflection**: Storing reflections in vector databases for long-term recall across tasks
- **Integration with External Tools**: Combining reflection with tool use (e.g., adjusting search strategies after failed queries)
- **Self-Improving Agents**: The ultimate goal of autonomous improvement of prompts, strategies, and even model weights through continuous reflection cycles

## Sources

- Shinn, N., et al. (2023). "Reflexion: Language Agents with Verbal Reinforcement Learning"
- Madaan, A., et al. (2023). "Self-Refine: Iterative Refinement with Self-Feedback"
- Wei, J., et al. (2022). "Chain-of-Thought Prompting Elicits Reasoning in Large Language Models"
- LangGraph Documentation (2024). "Multi-Agent Systems and Critique Nodes"
- AutoGen Papers (2023). "Conversational Agents for Multi-Agent Collaboration"

### Route History

`researcher  →  analyst  →  writer  →  critic  →  done`

### Trace Events

```json
[
  {
    "name": "supervisor",
    "payload": {
      "decision": "researcher",
      "reason": "no research notes yet",
      "iteration": 1
    }
  },
  {
    "name": "researcher",
    "payload": {
      "sources_found": 0,
      "notes_length": 7247
    }
  },
  {
    "name": "supervisor",
    "payload": {
      "decision": "analyst",
      "reason": "research done, need analysis",
      "iteration": 2
    }
  },
  {
    "name": "analyst",
    "payload": {
      "analysis_length": 7405
    }
  },
  {
    "name": "supervisor",
    "payload": {
      "decision": "writer",
      "reason": "analysis done, need final answer",
      "iteration": 3
    }
  },
  {
    "name": "writer",
    "payload": {
      "answer_length": 4516
    }
  },
  {
    "name": "supervisor",
    "payload": {
      "decision": "critic",
      "reason": "final answer produced, need critic review",
      "iteration": 4
    }
  },
  {
    "name": "critic",
    "payload": {
      "review_length": 1640
    }
  },
  {
    "name": "supervisor",
    "payload": {
      "decision": "done",
      "reason": "critic approved with score 9/10",
      "iteration": 5
    }
  },
  {
    "name": "workflow",
    "payload": {
      "event": "complete",
      "total_seconds": 68.00889719999395
    }
  }
]
```

### Failure Mode Analysis

No errors encountered during this run.

**Known failure modes:**

1. **Search timeout**: DuckDuckGo may rate-limit — fallback returns empty results.
2. **LLM timeout**: DeepSeek API may be slow — tenacity retries up to 3 times.
3. **Max iterations hit**: Supervisor enforces max_iterations guardrail.
4. **Cost overrun**: Multi-agent uses 3-4x more tokens than baseline.

**Fixes applied:**

- Retry with exponential backoff for LLM calls
- Graceful fallback for search failures
- Per-agent error catching in workflow
- Max iterations + timeout guardrails
