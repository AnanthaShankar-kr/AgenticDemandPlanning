# Agentic Demand Planning PoC: A Day in the Life

This document outlines a narrative-driven test plan to demonstrate the capabilities of the Agentic Demand Planning system.

## The Story
You are a **Demand Planner** at a retail company. It's Monday morning, and you need to finalize the demand plan for the upcoming quarter. You have a new AI-powered assistant to help you.

## Test Case 1: The Morning Briefing (Policy & Strategy)
**Goal**: Verify the agent understands business rules via MCP.

1.  **Action**: Open the Web UI (`http://localhost:8000`).
2.  **Chat**: Ask: *"What are our strategic priorities for this quarter?"*
3.  **Expected Result**:
    *   The **Policy Agent** responds.
    *   It cites "Revenue Weight" or "Strategic SKUs" (fetched via the new MCP Config Server).
    *   *Behind the scenes*: The agent connects to `servers/config_server.py` to get this data.

## Test Case 2: Data Deep Dive (Analyst & Docker)
**Goal**: Analyze sales data securely.

1.  **Chat**: Ask: *"Which SKU had the highest sales last year?"*
2.  **Expected Result**:
    *   The **Analyst Agent** takes over.
    *   It generates Python code to query the data.
    *   It executes this code inside a **Docker Container** (check your terminal for Docker logs if interested).
    *   It returns the exact SKU and sales figure.

## Test Case 3: The Planning Cycle (Orchestration)
**Goal**: Run the full end-to-end planning process.

1.  **Terminal**: Run `python main.py` (or trigger via UI if implemented, currently backend-driven).
2.  **Observation**: Watch the logs.
    *   **Policy**: Retrieves constraints.
    *   **Data**: Cleans anomalies (fixing the 'SKU' issue we solved).
    *   **Segmentation**: Classifies items (Seasonal vs Promo).
    *   **Forecast**: Generates P50/P90 forecasts.
    *   **Scenarios**: Simulates events.
    *   **Negotiation**: Checks capacity (10,000 units).
3.  **UI**: Refresh the Dashboard.
    *   See the **Forecast Chart** populated.
    *   See the **Data Table** with monthly aggregates.

## Test Case 4: Memory & History
**Goal**: Verify the agent remembers past insights.

1.  **Chat**: Ask: *"Save an insight: SKU_005 is a critical launch item."*
2.  **Chat**: Click **"Load History"**.
3.  **Expected Result**:
    *   The previous conversation appears.
    *   The agent (via `MemoryStore`) retains this context for future queries.

## Summary of Features
- **Multi-Agent Orchestration**: 7 specialized agents working in harmony.
- **MCP Integration**: Decoupled configuration fetching.
- **Docker Sandboxing**: Secure code execution for data analysis.
- **Interactive UI**: Chat, Charts, and Data Grid.
