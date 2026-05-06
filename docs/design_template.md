# Design Template

## Problem

Xây dựng hệ thống nghiên cứu tự động có thể nhận câu hỏi phức tạp, tìm kiếm thông tin trên web, phân tích nguồn, và viết câu trả lời tổng hợp có citations. Hệ thống cần so sánh hiệu quả giữa single-agent (1 LLM call) và multi-agent (supervisor + workers).

## Why multi-agent?

Single-agent gặp hạn chế khi xử lý task phức tạp:

1. **Một prompt quá dài**: phải vừa search, vừa phân tích, vừa viết → dễ mất focus.
2. **Không có specialization**: mỗi bước cần temperature/prompt khác nhau (research=0.2, writing=0.4).
3. **Khó debug**: output là black box, không biết sai ở bước nào.
4. **Không có guardrail**: không kiểm soát được flow, retry, hay fallback.

Multi-agent giải quyết bằng separation of concerns: mỗi agent 1 việc, supervisor điều phối, state rõ ràng.

## Agent roles

| Agent | Responsibility | Input | Output | Failure mode |
|---|---|---|---|---|
| Supervisor | Quyết định agent tiếp theo, enforce guardrails | `ResearchState` | `route_history` updated | Max iterations → force done |
| Researcher | Tìm kiếm web, tổng hợp sources thành notes | Query + search results | `sources`, `research_notes` | Search fail → empty sources, LLM dùng knowledge riêng |
| Analyst | Phân tích notes, so sánh, flag weak evidence | `research_notes`, `sources` | `analysis_notes` | LLM timeout → retry 3x |
| Writer | Viết câu trả lời cuối cùng có citations | All notes + sources | `final_answer` | Output ngắn/sai → critic có thể reject |

## Shared state

```python
class ResearchState:
    request: ResearchQuery    # Query gốc, max_sources, audience
    iteration: int            # Đếm vòng lặp cho guardrail
    route_history: list[str]  # Lịch sử routing để trace
    sources: list[SourceDocument]   # Sources từ web search
    research_notes: str       # Output của Researcher
    analysis_notes: str       # Output của Analyst
    final_answer: str         # Output của Writer
    agent_results: list[AgentResult]  # Chi tiết output + metadata mỗi agent
    trace: list[dict]         # Events cho tracing/debugging
    errors: list[str]         # Lỗi để post-mortem analysis
```

**Lý do mỗi field:**
- `iteration` + `route_history`: để supervisor enforce max_iterations, trace luồng.
- `sources`: researcher collect, analyst/writer reference.
- `research_notes` / `analysis_notes`: handoff data giữa agents.
- `agent_results`: metadata chi tiết (tokens, cost) cho benchmark.
- `errors`: fault-tolerance, không crash toàn bộ workflow.

## Routing policy

```text
START → Supervisor
  |
  ├── no research_notes? → Researcher → Supervisor
  ├── no analysis_notes? → Analyst → Supervisor
  ├── no final_answer?   → Writer → Supervisor
  ├── final_answer done? → DONE
  └── iteration >= max?  → DONE (guardrail)
```

Flow tuyến tính nhưng supervisor kiểm soát từng bước. Nếu agent fail, supervisor vẫn nhận control và quyết định tiếp.

## Guardrails

- **Max iterations**: 6 (config), supervisor force `done` khi vượt.
- **Timeout**: 120s (workflow-level), break loop khi quá.
- **Retry**: LLM client retry 3x với exponential backoff (tenacity).
- **Fallback**: Search fail → return empty list, agent dùng LLM knowledge. Agent crash → log error, supervisor tiếp tục.
- **Validation**: Pydantic schemas enforce input/output types. ResearchQuery yêu cầu min_length=5.

## Benchmark plan

| Query | Metrics đo | Expected |
|---|---|---|
| "Research GraphRAG state-of-the-art and write a 500-word summary" | Latency, cost, answer_length, sources_count | Multi-agent chậm hơn 3-5x nhưng có sources |
| "Compare single-agent and multi-agent workflows for customer support" | Latency, cost, quality | Multi-agent structured hơn |
| "Summarize production guardrails for LLM agents" | Latency, cost, citation_coverage | Multi-agent có citations |

**Metrics:**
- Latency: wall-clock time (perf_counter)
- Cost: token count × DeepSeek pricing ($0.14/1M input, $0.28/1M output)
- Quality: answer length + structure + citations (manual review or LLM-as-judge)
- Failure rate: errors count / total runs
