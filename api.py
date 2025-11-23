from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import pandas as pd
import os
from orchestrator import OrchestratorAgent
from agents.chart_agent import ChartAgent

app = FastAPI()

# Mount static files for frontend
app.mount("/ui", StaticFiles(directory="ui"), name="ui")

# Global state
orchestrator = OrchestratorAgent()
chart_agent = ChartAgent()
final_plan = None
sales_data = None

class ChatRequest(BaseModel):
    message: str

class ChartRequest(BaseModel):
    query: str

@app.get("/")
async def read_root():
    return FileResponse('ui/index.html')

@app.get("/api/init")
async def init_system():
    global final_plan, sales_data
    try:
        # Load data
        sales_data = pd.read_csv("data/sales_data.csv")
        
        # Check if final plan exists, if not run orchestrator
        if os.path.exists("data/final_plan.csv"):
            final_plan = pd.read_csv("data/final_plan.csv")
            return {"status": "Loaded existing plan"}
        else:
            # In a real app, we might trigger a run here, but it takes time.
            # For now, let's assume the user runs main.py first or we trigger it.
            # Let's trigger a quick run (mock mode likely if no key)
            final_plan, _ = orchestrator.run()
            return {"status": "Generated new plan"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/dashboard")
async def get_dashboard_data():
    global final_plan, sales_data
    if final_plan is None or sales_data is None:
        await init_system()
        
    # 1. Historical Sales (Last 12 weeks)
    last_date = pd.to_datetime(sales_data['Date']).max()
    start_date = last_date - pd.Timedelta(weeks=12)
    hist_df = sales_data[pd.to_datetime(sales_data['Date']) > start_date]
    hist_sales = hist_df.groupby('Date')['Sales'].sum().reset_index()
    
    # 2. Forecast (Next 12 weeks)
    forecast_df = final_plan.groupby('Date')['Constrained_Plan'].sum().reset_index()
    
    # 3. Top 5 Products (by Forecast Volume)
    top_products = final_plan.groupby('SKU')['Constrained_Plan'].sum().sort_values(ascending=False).head(5).reset_index()
    
    # Handle NaNs for JSON serialization
    # fillna("") is safer than where(pd.notnull) for mixed types going to JSON
    hist_sales = hist_sales.fillna("")
    forecast_df = forecast_df.fillna("")
    top_products = top_products.fillna("")
    
    return {
        "historical": hist_sales.to_dict(orient='records'),
        "forecast": forecast_df.to_dict(orient='records'),
        "top_products": top_products.to_dict(orient='records')
    }

@app.get("/api/table")
async def get_table_data():
    global final_plan
    if final_plan is None:
        await init_system()
    
    try:
        # Return full plan for the table
        # Replace NaNs with empty string for text columns or None for others
        # fillna("") is the most robust way to ensure valid JSON for a frontend table
        df_clean = final_plan.fillna("")
        return df_clean.to_dict(orient='records')
    except Exception as e:
        print(f"Error in get_table_data: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing table data: {str(e)}")

@app.post("/api/chat")
async def chat(request: ChatRequest):
    # Use the Orchestrator to route the request to the right agent
    response = orchestrator.route_request(request.message)
    
    # If response is a dict (from our previous refactor), extract text
    if isinstance(response, dict):
        return {"response": response.get("explanation", str(response))}
    return {"response": response}

@app.post("/api/chart")
async def generate_chart(request: ChartRequest):
    global final_plan, sales_data
    if final_plan is None or sales_data is None:
        await init_system()
        
    # Combine data for the agent
    # We want a single view of history + forecast
    # sales_data: Date, SKU, Sales
    # final_plan: Date, SKU, Constrained_Plan, Baseline_P50, Upside, etc.
    
    # Ensure dates are datetime
    sales_data['Date'] = pd.to_datetime(sales_data['Date'])
    final_plan['Date'] = pd.to_datetime(final_plan['Date'])
    
    # Select relevant columns from sales to match structure if needed, or just concat
    # We'll just concat and let pandas handle the NaNs (Sales will be NaN in future, Plan NaN in past)
    combined_df = pd.concat([sales_data, final_plan], ignore_index=True)
    
    # Sort by Date
    combined_df = combined_df.sort_values('Date')
    
    # Use ChartAgent with combined data
    config = chart_agent.run(request.query, combined_df)
    print(f"[API] Chart Config Generated: {config}")
    return {"config": config}

@app.post("/api/run_planning")
async def run_planning():
    global final_plan
    try:
        # Run the orchestrator
        final_plan_df, result = orchestrator.run()
        
        # Update global state
        final_plan = final_plan_df
        
        # Return logs and status
        return {
            "status": "success",
            "logs": result.get("logs", []),
            "report": result.get("explanations", ["No report generated."])[0]
        }
    except Exception as e:
        print(f"[API] Error running planning: {e}")
        raise HTTPException(status_code=500, detail=str(e))

from utils.memory_store import MemoryStore

# ... (existing imports)

# Initialize Memory Store
memory_store = MemoryStore()

# ... (existing code)

@app.get("/api/history")
async def get_history():
    return memory_store.get_all_interactions()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
