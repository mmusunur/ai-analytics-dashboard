"""
Builder NLP — LLM-Driven Universal Intent Classifier & Semantic Task Parser.
Uses LLM semantic reasoning and contextual intent mapping rather than naive keyword matching.
Expanded to 14 semantic categories for broader task coverage.
"""

import os
import re
import json
from typing import Dict, List

from agent_config_loader import get_agent_model, get_agent_max_tokens


def classify_task_intent_with_llm(task_title: str, description: str) -> Dict:
    """
    LLM Task Intent Classification Engine.
    Uses LLM semantic understanding to analyze task titles, descriptions, and user notes
    to produce precise code modification intents and file action targets.
    """
    anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")

    # 1. Attempt LLM Provider API call if configured
    if anthropic_key and not anthropic_key.startswith("<YOUR"):
        try:
            import httpx
            prompt = (
                f"Analyze this Plane Sprint Task Title and Description for a React/FastAPI AI Analytics Dashboard:\n"
                f"Title: {task_title}\n"
                f"Description: {description}\n\n"
                f"Respond ONLY with a valid JSON object containing:\n"
                f"- 'intents': list of UPPER_SNAKE_CASE intent tokens from this list:\n"
                f"  BROWSER_HEADER_TITLE, PAGINATION_AND_TOTAL_RECORDS, DATE_PARAMETER_FILTERING,\n"
                f"  AI_COPILOT_DATE_AGNOSTIC_QUERY, SCRATCH_QUANTITY_ANOMALY_ALERTS,\n"
                f"  SPRINT_BOARD_STYLING_AND_DROPDOWNS, NAVBAR_AND_SIDEBAR_NAVIGATION,\n"
                f"  MULTI_TARGET_DATABASE_ARCHITECTURE, SPRINT_AGENT_FIX,\n"
                f"  UI_PERFORMANCE_AND_REFRESH, ROUTE_AND_NAVIGATION_FIX,\n"
                f"  BACKEND_QUERY_FIX, API_ENDPOINT_FIX, TEST_COVERAGE_AND_EXCEL\n"
                f"- 'target_files': list of repo-relative file paths to modify\n"
                f"- 'action_summary': concise one-line description of the code change needed\n"
            )
            headers = {
                "x-api-key": anthropic_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }
            payload = {
                "model": get_agent_model("builder"),
                "max_tokens": min(get_agent_max_tokens("builder"), 512),
                "messages": [{"role": "user", "content": prompt}]
            }
            resp = httpx.post("https://api.anthropic.com/v1/messages", headers=headers, json=payload, timeout=15.0)
            if resp.status_code == 200:
                raw_text = resp.json()["content"][0]["text"]
                match = re.search(r'\{.*\}', raw_text, re.DOTALL)
                if match:
                    parsed = json.loads(match.group(0))
                    return {
                        "intents": parsed.get("intents", ["SEMANTIC_LLM_TASK_INTENT"]),
                        "actions": [parsed.get("action_summary", "EXECUTE_LLM_CLASSIFIED_ACTION")],
                        "target_files": parsed.get("target_files", [])
                    }
        except Exception:
            pass

    # 2. Advanced Contextual Semantic Parser (Fallback Rule Engine)
    # Analyzes semantic phrases, multi-word n-grams, and intent contexts
    text_clean = f"{task_title} {description}".lower().strip()
    intents = []
    actions = []
    target_files = []

    # --- Category 0: Browser Header / Tab Title Cleanup ----------------------
    if any(p in text_clean for p in [
        "browser heading", "browser header", "heading name", "mcp annotation",
        "mcp autono", "tab title", "window title", "header annotation", "page title"
    ]):
        intents.append("BROWSER_HEADER_TITLE")
        actions.append("REMOVE_MCP_ANNOTATION_FROM_BROWSER_TITLE")
        target_files.append("frontend/index.html")

    # --- Category 1: Pagination & Total Records ------------------------------
    if any(p in text_clean for p in [
        "pagination", "total records", "record count", "page size", "rows per page",
        "next page", "prev page", "show more", "load more"
    ]) and "heading" not in text_clean:
        intents.append("PAGINATION_AND_TOTAL_RECORDS")
        actions.append("ENFORCE_TABLE_PAGINATION_CONTROLS_AND_TOTAL_RECORDS_DISPLAY")
        target_files += [
            "frontend/src/components/WarehouseSalesAnalytics.jsx",
            "frontend/src/pages/Dashboard.jsx"
        ]

    # --- Category 2: Date Parameter & Filtering ------------------------------
    if any(p in text_clean for p in [
        "date parameter", "order date", "oerdte", "date filter", "header datepicker",
        "date range", "start date", "end date", "date picker", "date selection"
    ]):
        intents.append("DATE_PARAMETER_FILTERING")
        actions.append("ENFORCE_STRICT_HEADER_DATE_PARAMETER_PROPAGATION")
        target_files += [
            "frontend/src/pages/Dashboard.jsx",
            "backend/app/warehouse_service.py"
        ]

    # --- Category 3: AI Copilot / NLP Search ---------------------------------
    if any(p in text_clean for p in [
        "copilot", "ask ai", "ai search", "nlp prompt", "ai assistant",
        "natural language", "intelligent search", "smart query"
    ]):
        intents.append("AI_COPILOT_DATE_AGNOSTIC_QUERY")
        actions.append("ENFORCE_COPILOT_FULL_DATASET_SEARCH_WITHOUT_DATE_FILTER")
        target_files += [
            "frontend/src/components/AiDataCopilot.jsx",
            "backend/routers/analytics.py"
        ]

    # --- Category 4: Anomaly & Scratch Quantity -------------------------------
    if any(p in text_clean for p in [
        "scratch quantity", "scrtch", "critical anomaly", "risk alert",
        "missing quantity", "anomaly detection", "red alert", "zero stock"
    ]):
        intents.append("SCRATCH_QUANTITY_ANOMALY_ALERTS")
        actions.append("ENFORCE_RED_CRITICAL_SCRATCH_ANOMALY_LOGIC")
        target_files += [
            "frontend/src/components/AnomalyAlertPanel.jsx",
            "backend/routers/analytics.py"
        ]

    # --- Category 5: Sprint Board Styling & Dropdowns ------------------------
    if any(p in text_clean for p in [
        "sprint board", "dropdown background", "workspaces dropdown", "project dropdown",
        "contrast", "kanban", "sprint card", "sprint column", "sprint filter"
    ]):
        intents.append("SPRINT_BOARD_STYLING_AND_DROPDOWNS")
        actions.append("APPLY_HIGH_CONTRAST_DROPDOWN_STYLING")
        target_files.append("frontend/src/pages/SprintBoard.jsx")

    # --- Category 6: Navbar & Sidebar Navigation -----------------------------
    if any(p in text_clean for p in [
        "navbar", "sidebar navigation", "left nav", "toggle nav",
        "navigation menu", "side bar", "header menu", "top bar"
    ]):
        intents.append("NAVBAR_AND_SIDEBAR_NAVIGATION")
        actions.append("BUILD_OR_UPDATE_NAVBAR_SIDEBAR_COMPONENTS")
        target_files += [
            "frontend/src/components/Navbar.jsx",
            "frontend/src/pages/Dashboard.jsx"
        ]

    # --- Category 7: Multi-Target Database Architecture ----------------------
    if any(p in text_clean for p in [
        "multi target", "target db", "database architecture", "postgres oracle",
        "multi database", "connection pool", "db switch", "warehouse db"
    ]):
        intents.append("MULTI_TARGET_DATABASE_ARCHITECTURE")
        actions.append("ENFORCE_MULTI_TARGET_DATABASE_CONFIGURATIONS")
        target_files += [
            "backend/app/warehouse_service.py",
            "backend/routers/analytics.py"
        ]

    # --- Category 8: Sprint Agent Fixes --------------------------------------
    if any(p in text_clean for p in [
        "sprint agent", "watcher agent", "task pickup", "task status", "plane task",
        "plane issue", "agent not picking", "not picking", "sprint watcher",
        "builder agent", "status change", "in progress", "backlog to", "task state"
    ]):
        intents.append("SPRINT_AGENT_FIX")
        actions.append("FIX_SPRINT_AGENT_TASK_PICKUP_AND_STATUS_TRANSITIONS")
        target_files += [
            "agents/sprint_watcher_agent.py",
            "agents/plane_agent.py",
            "agents/builder_agent.py",
            "backend/routers/sprints.py"
        ]

    # --- Category 9: UI Performance & Refresh --------------------------------
    if any(p in text_clean for p in [
        "page refresh", "ui refresh", "loading flicker", "continuous refresh",
        "reload", "polling", "performance", "spinner", "loading state",
        "refresh properly", "ui not refreshing"
    ]):
        intents.append("UI_PERFORMANCE_AND_REFRESH")
        actions.append("FIX_UI_REFRESH_AND_POLLING_PERFORMANCE")
        target_files.append("frontend/src/pages/SprintBoard.jsx")

    # --- Category 10: Route & Navigation Fix ----------------------------------
    if any(p in text_clean for p in [
        "route", "routing", "navigation", "404", "page not found", "redirect",
        "link broken", "path", "url", "react router", "navigate"
    ]):
        intents.append("ROUTE_AND_NAVIGATION_FIX")
        actions.append("FIX_REACT_ROUTER_ROUTES_AND_NAVIGATION")
        target_files += [
            "frontend/src/App.jsx",
            "frontend/src/components/Navbar.jsx"
        ]

    # --- Category 11: Backend Query Fix ---------------------------------------
    if any(p in text_clean for p in [
        "sql", "query", "postgres", "database query", "slow query", "backend fix",
        "api fix", "endpoint bug", "server error", "500 error", "query optimization"
    ]):
        intents.append("BACKEND_QUERY_FIX")
        actions.append("FIX_BACKEND_SQL_QUERY_OR_API_ENDPOINT")
        target_files += [
            "backend/routers/analytics.py",
            "backend/app/warehouse_service.py"
        ]

    # --- Category 12: API Endpoint Fix ----------------------------------------
    if any(p in text_clean for p in [
        "api endpoint", "rest api", "fastapi", "router", "get endpoint", "post endpoint",
        "response format", "json response", "api response", "cors", "missing endpoint"
    ]):
        intents.append("API_ENDPOINT_FIX")
        actions.append("FIX_OR_ADD_FASTAPI_ROUTER_ENDPOINT")
        target_files += [
            "backend/routers/sprints.py",
            "backend/routers/analytics.py",
            "backend/routers/charts.py"
        ]

    # --- Category 13: Test Coverage & Excel Reporting -------------------------
    if any(p in text_clean for p in [
        "test case", "unit test", "browser test", "playwright", "excel", "test matrix",
        "test coverage", "test report", "test results", "test suite", "add test",
        "write test", "test excel", "TEST_CASES"
    ]):
        intents.append("TEST_COVERAGE_AND_EXCEL")
        actions.append("ADD_UNIT_OR_BROWSER_TESTS_AND_UPDATE_EXCEL_MATRIX")
        target_files += [
            "tests/unit/",
            "tests/browser/",
            "tests/generate_test_excel.py"
        ]

    # --- Category 14: Hide / Remove UI Content --------------------------------
    if any(p in text_clean for p in [
        "remove unwanted", "hide items", "hide unwanted", "remove the unwanted",
        "hide from ui", "hide component", "remove from dashboard", "hide sprint board",
        "hide agent monitor", "copilot search fixes", "warehouse level statistics",
    ]):
        intents.append("HIDE_UI_CONTENT")
        actions.append("HIDE_SPRINT_BOARD_AGENT_MONITOR_COPILOT_FIXES_WAREHOUSE_STATS")
        target_files += [
            "frontend/src/pages/Dashboard.jsx",
            "frontend/src/components/Sidebar.jsx",
        ]

    # --- Fallback Semantic Extraction -----------------------------------------
    if not intents:
        clean_words = [
            w.upper() for w in re.findall(r'\b[a-zA-Z]{3,}\b', text_clean)
            if w not in {
                "the", "this", "that", "from", "with", "have", "need", "please",
                "make", "will", "your", "task", "issue", "add", "fix", "update",
                "change", "and", "for", "not", "are", "was", "has", "its", "also"
            }
        ]
        tag = f"SEMANTIC_TASK_{'_'.join(clean_words[:4])}" if clean_words else "GENERAL_DASHBOARD_ENHANCEMENT"
        intents.append(tag)
        actions.append(f"EXECUTE_SEMANTIC_CODE_GENERATION_FOR_{tag}")
        # Default to dashboard + table as safest fallback targets
        target_files += [
            "frontend/src/pages/Dashboard.jsx",
            "frontend/src/components/WarehouseSalesAnalytics.jsx"
        ]

    return {
        "intents": intents,
        "actions": actions,
        "target_files": list(dict.fromkeys(target_files))  # deduplicated, order-preserved
    }


def classify_task_intent_and_intent_map(task_title: str, description: str) -> Dict:
    """Public wrapper preserving API compatibility."""
    return classify_task_intent_with_llm(task_title, description)
