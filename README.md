<<<<<<< HEAD
# AgenticDemandPlanning
Building a Strategy-Guided, Multi-Agent System for Data Quality, Forecasting, Scenarios and Learning
=======
# Agentic Demand Planning PoC

## 🎯 Goal
The goal of this project is to demonstrate an **Autonomous Agentic System** for Supply Chain Demand Planning. We aim to move beyond traditional, static planning tools by creating a system where specialized AI agents collaborate to:
1.  Ingest and clean sales data.
2.  Apply business policies and guardrails.
3.  Generate baseline forecasts.
4.  Simulate scenarios (promotions, events).
5.  Negotiate constraints (capacity, budget).
6.  Explain the "Why" behind the plan to human planners.

## 🚀 What This PoC Shows
This Proof of Concept (PoC) showcases a **vertical slice** of the end-to-end planning process. It demonstrates how a "Team of Agents" can be orchestrated to solve a complex business problem that typically requires multiple human roles.

Key highlights:
*   **Orchestration**: A central Orchestrator managing the workflow between specialized agents.
*   **Tool Use**: Agents using Python tools (Pandas, etc.) to perform rigorous data analysis.
*   **Transparency**: Full visibility into agent logs and reasoning (e.g., "Why was this SKU cut?").
*   **Interactive UI**: A chat-based interface combined with rich data visualizations (Charts, Tables).

## ⚡ Capabilities
The current system includes the following specialized agents:

1.  **Policy Agent**: Retrieves and enforces business rules (e.g., "Max promo uplift is 50%").
2.  **Data Agent**: Loads, cleans, and detects anomalies in historical sales data.
3.  **Segmentation Agent**: Analyzes volatility to classify SKUs (e.g., High/Low Volatility).
4.  **Baseline Agent**: Generates statistical baseline forecasts.
5.  **Scenario Agent**: Layers business events (promotions, launches) onto the baseline.
6.  **Negotiation Agent**: Checks capacity constraints and makes "cuts" to the plan where necessary, logging the reasons.
7.  **Monitor Agent**: Reviews the final plan and generates a summary report.
8.  **Analyst Agent**: A chat-based agent that can query the data to answer ad-hoc user questions (e.g., "Show me sales for SKU_001", "Why was this cut?").

## 🔮 Future Vision (Enhancements)
A full-fledged production system would include:

*   **Advanced Models**: Integration with enterprise-grade forecasting models (Prophet, ARIMA, Transformer-based models).
*   **Real-time Integration**: Direct connectors to ERP (SAP, Oracle) and CRM systems.
*   **Human-in-the-Loop Workflow**: Approval workflows where humans can reject or adjust specific agent decisions.
*   **Multi-Objective Optimization**: Using solvers (LP/MIP) for the Negotiation Agent to optimize for margin/revenue rather than just cutting low-priority items.
*   **Scalability**: Moving from local CSVs to a cloud data warehouse (BigQuery, Snowflake).

## 🛠️ How to Run

### Prerequisites
*   Python 3.10+
*   Docker (for the sandboxed code execution environment)
*   Google Gemini API Key (or compatible LLM key)

### Installation
1.  **Clone the repository**:
    ```bash
    git clone <repo-url>
    cd AgenticDemandPlanning
    ```

2.  **Create and activate a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Build the Docker Sandbox**:
    ```bash
    cd sandbox
    docker build -t pandas-sandbox .
    cd ..
    ```

5.  **Set up Environment Variables**:
    Export your API key:
    ```bash
    export GOOGLE_API_KEY="your_api_key_here"
    ```

### Running the Application
Start the backend API and frontend server:
```bash
uvicorn api:app --reload
```
Open your browser and navigate to: `http://127.0.0.1:8000`

## 🏗️ Architecture
The system follows a **Hub-and-Spoke** architecture:
*   **Orchestrator**: The "Manager" that maintains state and calls other agents in sequence.
*   **Agents**: Stateless workers that perform specific tasks. They receive context (DataFrames, Policy Dicts) and return updated artifacts.
*   **Shared State**: Data is passed between agents as Pandas DataFrames, ensuring consistency.
>>>>>>> 97a2a94 (Initial commit: Agentic Demand Planning PoC)
