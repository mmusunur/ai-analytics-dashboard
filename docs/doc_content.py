"""
Shared documentation content — single source of truth for PPTX, DOCX, and markdown sync.
Update this file when platform features change; then run: python docs/sync_all_documentation.py
"""

from datetime import datetime

GENERATED_DATE = datetime.now().strftime("%Y-%m-%d")

PLATFORM_TITLE = "AgenticOps AI"
PLATFORM_SUBTITLE = "MCP-Driven Autonomous Enterprise Platform"

SECTIONS = [
    {
        "title": "1. Platform Overview",
        "paragraphs": [
            "AgenticOps AI is an autonomous multi-agent enterprise control plane powered by FastAPI, React, and an autonomous agent fleet with live telemetry.",
            "The platform provides warehouse PostgreSQL analytics, an AI Data Copilot, Plane sprint board integration, and a fully automated 6-stage task pipeline with no user interaction required during sprint execution.",
        ],
        "bullets": [
            "Executive Dashboard — KPI cards, bar charts, scatter plots, heatmaps",
            "Warehouse Sales & Invoice Analytics — multi-filter PostgreSQL queries",
            "AI Data Copilot — date-agnostic natural language search",
            "Plane Sprint Board — multi-workspace / multi-project kanban",
            "Autonomous Agent Fleet — Builder, Tester, Sprint Watcher, Git, Memory",
        ],
    },
    {
        "title": "2. Autonomous Agent Fleet",
        "paragraphs": [
            "Six specialized agents coordinate sprint task execution. LLM model assignments are defined in README.md and must not be modified during documentation updates.",
        ],
        "bullets": [
            "Orchestrator Agent — fleet coordination and health decisions",
            "Builder Agent — autonomous code implementation (React & FastAPI)",
            "Tester Agent — 68 unit + 46 browser tests including dynamic sprint cases",
            "Sprint Watcher — continuous Plane polling and pipeline orchestration",
            "Git Agent — commit and push after successful task completion",
            "Memory Manager — persistent state in memory/agent_state.json",
        ],
    },
    {
        "title": "3. Sprint Auto-Pickup (No User Interaction)",
        "paragraphs": [
            "When you add a task in Plane with status To Do, Unstarted, or Triaged, the Sprint Watcher automatically picks it up within 15–60 seconds while run_sprint_watcher.py or start_all_services.bat is running.",
            "Tasks in Backlog are NOT auto-picked. Stale In Progress tasks may be retried if the pipeline was interrupted.",
        ],
        "bullets": [
            "Step 1: Pickup — Sprint Watcher reads Plane task, marks In Progress",
            "Step 2: Building — Builder Agent applies code changes (LLM + rule fallback)",
            "Step 3: Testing — Tester runs unit + browser + dynamic sprint task tests",
            "Step 4: Close Task — Plane Agent marks completed on success",
            "Step 5: Git Push — Git Agent commits and pushes meaningful changes",
            "Step 6: Done — Watcher resumes monitoring for next task",
            "On test failure: task returns to To Do (never auto-cancelled)",
        ],
    },
    {
        "title": "4. Live Agent Monitor & Sprint Monitor UI",
        "paragraphs": [
            "Two dedicated monitor pages provide clear, accurate auto-reloading status. Both show Last updated timestamp, countdown to next refresh, and a Refresh Now button.",
        ],
        "table": [
            ["Page", "URL", "Refresh Rate"],
            ["Agent Monitor", "/agents (http://localhost:5173/agents)", "Every 4 seconds"],
            ["Sprint Monitor & Board", "/sprints (http://localhost:5173/sprints)", "Tasks: 12s · Pipeline: 4s"],
            ["Sidebar AGENT STATUS", "All pages", "Every 4 seconds"],
            ["Floating pipeline panel", "Dashboard & other pages", "Every 4 seconds"],
        ],
        "bullets": [
            "Pipeline tracker shows 6 phases with ACTIVE NOW badge on working agent",
            "Auto-refresh pauses while agent modifies code; resumes immediately when done",
            "Purple top banner indicates Builder/Tester is running — UI polling paused",
            "Sidebar AGENTS section: Sprint Board + Agent Monitor navigation links",
        ],
    },
    {
        "title": "5. Application Must Stay Running",
        "paragraphs": [
            "Agents must start and keep the application running before browser tests or sprint task closure. The watchdog and server health helpers auto-restart crashed services.",
        ],
        "bullets": [
            "Backend FastAPI — port 8000",
            "Frontend Vite — port 5173",
            "Windows launcher: scripts\\start_all_services.bat",
            "Linux/macOS launcher: bash scripts/start_all_services.sh",
            "Watchdog: python scripts/agent_watchdog.py",
            "Sprint watcher: python scripts/run_sprint_watcher.py --interval 60",
            "Health helper: scripts/server_health.py — ensure_servers_running()",
        ],
    },
    {
        "title": "6. Testing & Quality Gates",
        "paragraphs": [
            "Every sprint task triggers dynamic browser test case generation from task title and description. TEST_CASES.xlsx is updated after every test run.",
        ],
        "bullets": [
            "68 pytest unit tests — python -m pytest tests/unit/",
            "46 Playwright browser tests — python -m pytest tests/browser/",
            "Dynamic sprint task tests — tests/browser/test_sprint_task_dynamic.py",
            "Excel matrix — tests/TEST_CASES.xlsx via python tests/generate_test_excel.py",
            "Registry — memory/sprint_test_registry.json",
        ],
    },
    {
        "title": "7. API Endpoints",
        "table": [
            ["Endpoint", "Description"],
            ["GET /api/agents/status", "All agents + pipeline object + agent_working flag"],
            ["GET /api/sprints/agent-working", "Lightweight working flag for frontend polling"],
            ["GET /api/sprints/tasks", "Sprint tasks from Plane API"],
            ["GET /api/health", "Backend health check"],
        ],
    },
    {
        "title": "8. Documentation Sync",
        "paragraphs": [
            "When major features are added, regenerate all documentation artifacts from the shared content module.",
        ],
        "bullets": [
            "python docs/sync_all_documentation.py — replaces PPTX + DOCX in place (use this)",
            "python scripts/sync_documentation.py — checks for stale docs",
            "Source: docs/doc_content.py · User guide: docs/AGENT_PIPELINE_USER_GUIDE.md",
            "Canonical outputs: docs/AgenticOps_AI_Overview.pptx (one file only, overwritten)",
        ],
    },
]

PPTX_SLIDES = [
    (PLATFORM_TITLE, f"{PLATFORM_SUBTITLE}\nFastAPI + React + Autonomous Agent Fleet"),
    ("Core Features", "• Executive Dashboard with KPI cards & charts\n• Warehouse PostgreSQL analytics\n• AI Data Copilot (date-agnostic NLP)\n• Plane Sprint Board integration\n• 6-stage autonomous task pipeline\n• Live Agent Monitor UI (/agents) & Sprint Monitor (/sprints)"),
    ("Agent Fleet", "Orchestrator • Builder • Tester • Sprint Watcher\nGit Agent • Plane Agent • Memory Manager\n(LLM assignments in README — preserved unchanged)"),
    ("Sprint Auto-Pickup", "Add task in Plane → To Do / Unstarted / Triaged\n→ Sprint Watcher picks up automatically\n→ Builder → Tester → Close → Git\n→ Fail: returned to To Do"),
    ("Live Monitor UI", "Agent Monitor /agents — refresh 4s\nSprint Monitor /sprints — tasks 12s, pipeline 4s\nLast updated · countdown · Refresh Now\nACTIVE NOW badge on working agent"),
    ("Application Uptime", "Backend :8000 · Frontend :5173\nstart_all_services.bat / .sh\nagent_watchdog.py · server_health.py"),
    ("Testing", "68 unit + 46 browser tests\nDynamic sprint cases → TEST_CASES.xlsx\npython tests/generate_test_excel.py"),
    ("Documentation", "README · tasks/*.md · docs/\nPPTX + DOCX: python docs/sync_all_documentation.py\ntask_33_automatic_documentation_updates.md"),
    ("Launch", "scripts\\start_all_services.bat\nrun_sprint_watcher.py --interval 60\nhttp://localhost:5173/agents"),
]
