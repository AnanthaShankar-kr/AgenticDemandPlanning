from agents.base_agent import BaseAgent
import pandas as pd
import os

class DataAnalystAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="DataAnalystAgent")
        self.register_tool(self.get_data_summary)
        self.register_tool(self.query_data)
        
        self.sales_data = None
        self.final_plan = None
        self._load_data()

        self.set_system_instruction(
            """
            You are the Data Analyst Agent.
            Your goal is to answer user questions about the sales data and the demand plan.
            You have access to two datasets:
            1. 'sales_data': Historical sales (Date, SKU, Sales, Promo_Flag, Marketing_Spend).
            2. 'final_plan': Future forecast (Date, SKU, Baseline_P50, Plan, Constrained_Plan, Upside, Negotiation_Log).
            
            The 'Negotiation_Log' column in 'final_plan' contains text explanations for any changes or cuts made to the plan (e.g., capacity constraints).
            If the user asks about "affected units", "cuts", "reductions", or "why" a plan is lower, you MUST check the 'Negotiation_Log'.
            
            When a user asks a question:
            1. Understand what they are looking for (e.g., "best selling item", "total forecast", "why was SKU_002 cut?").
            2. Use the 'query_data' tool to execute a Pandas query to get the answer.
            3. Explain the result in plain English.
            
            The 'query_data' tool takes a Python string that evaluates to a result.
            The dataframes are available as `self.sales_data` and `self.final_plan`.
            Example queries:
            - "self.sales_data.groupby('SKU')['Sales'].sum().sort_values(ascending=False).head(1)"
            - "self.final_plan['Constrained_Plan'].sum()"
            - "self.final_plan[self.final_plan['Negotiation_Log'].str.len() > 0][['Date', 'SKU', 'Negotiation_Log']]"
            """
        )

    def _load_data(self):
        try:
            if os.path.exists("data/sales_data.csv"):
                self.sales_data = pd.read_csv("data/sales_data.csv")
            if os.path.exists("data/final_plan.csv"):
                self.final_plan = pd.read_csv("data/final_plan.csv")
        except Exception as e:
            print(f"[{self.name}] Error loading data: {e}")

    def get_data_summary(self) -> str:
        """Returns a summary of the available data columns and types."""
        summary = ""
        if self.sales_data is not None:
            summary += f"Sales Data Columns: {list(self.sales_data.columns)}\n"
        if self.final_plan is not None:
            summary += f"Final Plan Columns: {list(self.final_plan.columns)}\n"
        return summary

    def query_data(self, query_code: str) -> str:
        """
        Executes a single line of Python pandas code inside a Docker container.
        """
        import subprocess
        
        # 1. Create the script content
        # We need to load the data inside the container. 
        # The container will have /data mounted.
        script_content = f"""
import pandas as pd
import os

try:
    sales_data = pd.read_csv('/data/sales_data.csv') if os.path.exists('/data/sales_data.csv') else None
    final_plan = pd.read_csv('/data/final_plan.csv') if os.path.exists('/data/final_plan.csv') else None
    
    if final_plan is not None and 'Negotiation_Log' in final_plan.columns:
        final_plan['Negotiation_Log'] = final_plan['Negotiation_Log'].fillna('').astype(str)
    
    # Define 'self' mock for compatibility with the query string if it uses 'self.sales_data'
    class MockSelf:
        def __init__(self, s, f):
            self.sales_data = s
            self.final_plan = f
    
    self = MockSelf(sales_data, final_plan)
    
    # Execute the query
    result = {query_code}
    print(result)
except Exception as e:
    print(f"Error: {{e}}")
"""
        
        # 2. Write script to a temporary file accessible to Docker
        # We'll use the current directory's 'sandbox' folder
        script_path = os.path.abspath("sandbox/temp_query.py")
        with open(script_path, "w") as f:
            f.write(script_content)
            
        # 3. Run Docker
        # Mount current data dir to /data
        # Mount script to /app/script.py
        data_dir = os.path.abspath("data")
        
        cmd = [
            "docker", "run", "--rm",
            "-v", f"{data_dir}:/data",
            "-v", f"{script_path}:/app/script.py",
            "pandas-sandbox",
            "python", "/app/script.py"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                return f"Error executing in Docker: {result.stderr}"
            return result.stdout.strip()
        except Exception as e:
            return f"System Error: {e}"
