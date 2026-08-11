# 📚 Documentation Index

| Document | What it covers |
|---|---|
| [AGENT_PIPELINE_USER_GUIDE.md](AGENT_PIPELINE_USER_GUIDE.md) | User guide — sprint pipeline, Agent Monitor, Sprint Monitor |
| [AgenticOps_AI_Overview.pptx](AgenticOps_AI_Overview.pptx) | Platform overview deck (auto-generated) |
| [AgenticOps_AI_Documentation.docx](AgenticOps_AI_Documentation.docx) | Full platform documentation in Word (auto-generated) |
| [agents.md](agents.md) | All 7 agent modules — what they do, key methods, usage |
| [mcp_servers.md](mcp_servers.md) | All 4 MCP servers — tools, config, agent usage |
| [backend.md](backend.md) | FastAPI backend — routes, services, schemas |
| [architecture.md](architecture.md) | Full system diagram, data flows, tech decisions |


---

## 🤖 Agent Fleet & LLM Model Allocation Matrix

| Agent Name | Script File | LLM Model Used | Primary Function |
|---|---|---|---|
| **Orchestrator Agent** | [`orchestrator_agent.py`](../agents/orchestrator_agent.py) | `Claude 3.5 Opus` (`claude-opus-4-5`) | Master workflow coordination, task breakdown, architectural decisions |
| **Builder Agent** | [`builder_agent.py`](../agents/builder_agent.py) | `Claude 3.5 Opus` (`claude-opus-4-5`) | Code generation (FastAPI & React), refactoring, bug fixing |
| **Tester Agent** | [`tester_agent.py`](../agents/tester_agent.py) | `Claude 3.5 Sonnet` (`claude-sonnet-4-5`) | Automated testing (`pytest` + `Playwright`), test suite validation |
| **Sprint Watcher** | [`sprint_watcher_agent.py`](../agents/sprint_watcher_agent.py) | `Claude 3.5 Haiku` (`claude-haiku-4-5`) | Fast 60s polling loop, comment monitoring, build triggering |
| **Git Agent** | [`git_agent.py`](../agents/git_agent.py) | `Claude 3.5 Haiku` (`claude-haiku-4-5`) | Git staging, committing, and End-Of-Day auto-push to GitHub |
| **Plane Agent** | [`plane_agent.py`](../agents/plane_agent.py) | `Claude 3.5 Haiku` (`claude-haiku-4-5`) | Task creation and issue state updates in Plane PM tool |
| **Memory Manager** | [`memory_manager.py`](../agents/memory_manager.py) | Deterministic / Rule-Based Engine | State persistence (`agent_state.json`), process monitoring (`psutil`) |

---

## Quick Links

- **Start here:** [architecture.md](architecture.md)
- **Adding a task & watching it build:** [agents.md](agents.md#1-sprint_watcher_agentpy-)
- **API endpoints reference:** [backend.md](backend.md)
- **Adding a new MCP tool:** [mcp_servers.md](mcp_servers.md#adding-a-new-mcp-server)
- **Regenerate PPTX + DOCX:** `python docs/sync_all_documentation.py` (source: `doc_content.py`)
