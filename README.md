# Multi-Agent Research System

A production-grade multi-agent research system built with LangGraph, DeepSeek, and DuckDuckGo. This project orchestrates multiple specialized AI agents to research, analyze, write, and critique a user query, providing high-quality automated research outputs.

## Architecture

The system utilizes a cyclic LangGraph StateGraph with the following agent nodes:

1. Supervisor: Acts as the central router and orchestrator. It manages the state, checks guardrails (iteration limits, timeouts), and routes tasks to the appropriate worker agent based on the current state.
2. Researcher: Conducts web searches using DuckDuckGo to gather relevant source documents and compiles initial research notes.
3. Analyst: Analyzes the research notes, synthesizes the findings, and prepares a structured analysis.
4. Writer: Drafts the final comprehensive answer based on the analysis.
5. Critic: Acts as a quality assurance feedback loop. It evaluates the writer's final answer against the original sources. If the score is below 7/10, the output is rejected and sent back for revision.

## Prerequisites

- Python 3.12 or higher
- API Keys:
  - DeepSeek API Key (or OpenAI compatible key)

## Installation

1. Clone the repository and navigate to the project directory:
   ```bash
   git clone <repository_url>
   cd <repository_directory>
   ```

2. Create and activate a virtual environment:
   ```bash
   # Windows
   python -m venv .venv
   .venv\Scripts\activate
   
   # Linux/macOS
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Install the dependencies:
   ```bash
   pip install -e .
   ```

## Configuration

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Open the `.env` file and configure your API keys. For DeepSeek:
   ```env
   OPENAI_API_KEY=your_deepseek_api_key
   OPENAI_BASE_URL=https://api.deepseek.com
   ```

## Usage

The system provides a command-line interface (CLI) to interact with the agents.

### 1. Single-Agent Baseline
Run a simple, single-agent prompt without the graph orchestrator. Useful for comparing performance and cost against the multi-agent system.
```bash
python -m multi_agent_research_lab.cli baseline -q "Describe the self-reflection pattern in LLM agents."
```

### 2. Multi-Agent Workflow
Run the full LangGraph orchestration with the Researcher, Analyst, Writer, and Critic feedback loop.
```bash
python -m multi_agent_research_lab.cli multi-agent -q "Describe the self-reflection pattern in LLM agents."
```

### 3. Automated Benchmark
Run both the baseline and the multi-agent workflow sequentially. The system will automatically generate an execution trace and a comparative markdown report detailing latency, token cost, and output quality.
```bash
python -m multi_agent_research_lab.cli benchmark -q "Describe the self-reflection pattern in LLM agents."
```

## Testing

To verify the logic and routing of the agents, run the automated test suite using pytest:
```bash
python -m pytest tests/ -v
```

## Tracing and Evaluation

- Execution Tracing: Every multi-agent run automatically generates a JSON trace file in the `reports/` directory, logging state changes, API calls, and routing decisions.
- Benchmark Reports: The `benchmark` command generates a detailed comparative markdown report in `reports/benchmark_report.md`.
