# Benchmark Report

**Student**: Nguyễn Hoàng Long (2A202600160)

## Summary Table

| Run | Latency (s) | Cost (USD) | Quality | Notes |
|---|---:|---:|---:|---|
| single-agent-baseline | 18.44 | $0.000316 |  | answer_length=5473 |
| multi-agent-workflow | 212.24 | $0.000399 |  | answer_length=0, routes=researcher |

## Analysis

- **Latency ratio**: Multi-agent is 11.5x slower than baseline
- **Cost ratio**: Multi-agent costs 1.3x the baseline
- **Trade-off**: Multi-agent provides structured research with sources and analysis at the cost of higher latency and token usage


## Detailed Comparison

### Query

> Describe the self-reflection pattern in LLM agents.

### Single-Agent Baseline Output

Here is a comprehensive description of the self-reflection pattern in LLM agents.

### The Self-Reflection Pattern in LLM Agents

The self-reflection pattern is a sophisticated meta-cognitive technique used to enhance the performance of Large Language Model (LLM) agents. Instead of simply generating a single output and moving on, an agent employing self-reflection pauses to critically evaluate its own reasoning, actions, and outputs. This process allows the agent to identify errors, refine its understanding, and improve subsequent attempts, leading to more robust and reliable behavior, especially on complex, multi-step tasks.

**Core Mechanism: The Reflection Loop**

The pattern operates as a cyclical process, typically broken down into three distinct phases:

1.  **Action & Observation:** The agent first performs an action based on its current understanding of the task. This could be generating a piece of code, writing a paragraph of text, querying a database, or interacting with an external tool (e.g., a calculator or web search). The agent then observes the outcome of this action. For example, if it ran code, the observation would be the output (or error message) from the code interpreter.

2.  **Self-Reflection:** This is the critical step. The agent is prompted to analyze the observed outcome. It asks itself questions like:
    - "Did my action achieve the desired sub-goal?"
    - "What went wrong? Was my reasoning flawed, or was there a factual error?"
    - "What is the specific nature of the error (e.g., syntax error, logical fallacy, missing information)?"
    - "What should I have done differently?"
    - "What new information have I gained from this failure?"

    This reflection is not a simple "yes/no" check. It involves generating a detailed, natural language critique of its own previous thought process. The agent might explicitly state: *"My initial plan was flawed because I assumed X, but the error message shows Y. I need to reconsider my approach by..."*

3.  **Refinement & Next Action:** Based on the self-reflection, the agent formulates a new, improved plan or action. It incorporates the lessons learned from the failure. It might correct a specific line of code, rewrite a paragraph with a different structure, or choose a different tool to query. The agent then loops back to the "Action & Observation" phase, using its refined strategy.

**Why It Works: The Power of Explicit Reasoning**

The effectiveness of self-reflection stems from forcing the LLM to externalize its internal "chain-of-thought" and then critique it. LLMs are powerful pattern matchers, but they can be brittle. A single incorrect assumption early in a reasoning chain can lead to a completely wrong final answer. Self-reflection acts as a debugging mechanism for the agent's own cognition.

- **Error Correction:** It allows the agent to catch and fix mistakes without human intervention. A coding agent can reflect on a `TypeError` and realize it needs to convert a string to an integer before performing arithmetic.
- **Robustness:** It makes the agent more resilient to ambiguous or misleading prompts. By questioning its own initial interpretation, it can explore alternative solutions.
- **Learning from Failure:** The agent builds a "memory" of its mistakes within the current task context. This is not long-term learning (the model's weights don't change), but it is a powerful form of in-context learning for the specific problem at hand.

**Practical Example: A Coding Agent**

Consider an LLM agent tasked with writing a Python function to calculate the Fibonacci sequence.

- **Action 1:** The agent writes a recursive function `fib(n)`. It runs the code.
- **Observation 1:** The code runs but is extremely slow for `n=35`. The agent observes a performance issue.
- **Reflection 1:** The agent reflects: *"The recursive approach has exponential time complexity due to repeated calculations. This is inefficient. I should use dynamic programming with memoization or an iterative approach."*
- **Action 2:** The agent rewrites the function using an iterative loop.
- **Observation 2:** The code now runs quickly and correctly for `n=35`.
- **Reflection 2:** *"The iterative solution is efficient and correct. The task is complete."*

Without self-reflection, the agent would have likely stopped after the first, flawed solution.

**Limitations and Considerations**

- **Computational Cost:** Each reflection cycle requires additional LLM calls, increasing latency and token usage (and thus cost).
- **Over-Correction:** An agent can become overly cautious or "second-guess" a correct solution, leading to unnecessary changes or infinite loops.
- **Hallucination in Reflection:** The LLM's reflection itself can be flawed. It might incorrectly identify a non-existent error or propose a worse solution. This is a key challenge.
- **Task Suitability:** Self-reflection is most valuable for complex, multi-step tasks with clear feedback signals (e.g., code execution, math problems). For simple, single-step tasks, the overhead is not justified.

In summary, the self-reflection pattern transforms an LLM from a single-pass generator into an iterative problem-solver. By explicitly analyzing its own outputs and reasoning, the agent can autonomously correct errors, adapt to new information, and produce significantly higher-quality results on challenging problems. It is a cornerstone of building more capable and reliable LLM agents.

### Multi-Agent Output

(empty)

### Route History

`researcher`

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
      "notes_length": 6884
    }
  },
  {
    "name": "workflow",
    "payload": {
      "event": "timeout",
      "elapsed": 210.0804358999958
    }
  },
  {
    "name": "workflow",
    "payload": {
      "event": "complete",
      "total_seconds": 210.08195790000173
    }
  }
]
```

### Failure Mode Analysis

Errors encountered: ['Workflow timeout after 210.1s']

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
