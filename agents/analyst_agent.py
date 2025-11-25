from agents.base_agent import BaseAgent
import pandas as pd
import os
from servers.config_server import load_config

class DataAnalystAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="DataAnalystAgent")
        self.register_tool(self.get_data_summary)
        self.register_tool(self.query_data)
        
        self.sales_data = None
        self.final_plan = None
        self._load_data()
        
        # Load policy for context injection
        policy = load_config("config.yaml")
        constraints = policy.get('constraints', {})
        
        self.set_system_instruction(
            f"""
            You are the Data Analyst Agent.
            Your goal is to answer user questions about the sales data, demand plan, and business policies.
            
            You have access to three datasets:
            1. 'sales_data': Historical sales (Date, SKU, Sales, Promo_Flag, Marketing_Spend).
            2. 'final_plan': Future forecast (Date, SKU, Baseline_P50, Plan, Constrained_Plan, Upside, Negotiation_Log).
            3. 'segmentation': SKU segmentation (SKU, Segment).
            
            **Policy Context**:
            - Max Promo Uplift: {constraints.get('max_promo_uplift', 'Unknown')}
            - Capacity Limit: {constraints.get('capacity_limit_total', 'Unknown')}
            
            **Guidelines**:
            1. **Cuts/Reductions**: If asked about cuts, calculate `Cut = Plan - Constrained_Plan`. 
               - If a cut exists, you MUST explain that it was due to the **Capacity Limit** ({constraints.get('capacity_limit_total', 'Unknown')}) and cite the 'Negotiation_Log'.
            2. **Comparisons**: When comparing plans (e.g., Baseline vs Final), analyze the *aggregate* difference (sum of columns) to see the overall trend.
            3. **Segments**: Join 'final_plan' or 'sales_data' with 'segmentation' on 'SKU' to answer segment-related questions.
            4. **Policy**: Use the Policy Context above to answer questions about limits or guardrails.
            
            **Tool Usage**:
            - Use 'query_data' to execute Python pandas code.
            - The dataframes are available as `self.sales_data`, `self.final_plan`, and `self.segmentation`.
            - RETURN ONLY THE CODE STRING.
            - **CRITICAL**: After the tool runs, you MUST generate a text response summarizing the result. Do not stop after the tool call.
            
            **Example Queries**:
            - "self.sales_data.groupby('SKU')['Sales'].sum().sort_values(ascending=False).head(1)"
            - "self.final_plan['Constrained_Plan'].sum()"
            - "self.final_plan.merge(self.segmentation, on='SKU')[['SKU', 'Segment']].drop_duplicates()"
            - "self.final_plan.assign(Cut=self.final_plan['Plan']-self.final_plan['Constrained_Plan']).groupby('SKU')['Cut'].sum().sort_values(ascending=False).head(3)"
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
    segmentation = pd.read_csv('/data/segmentation.csv') if os.path.exists('/data/segmentation.csv') else None
    
    if final_plan is not None and 'Negotiation_Log' in final_plan.columns:
        final_plan['Negotiation_Log'] = final_plan['Negotiation_Log'].fillna('').astype(str)
    
    # Define 'self' mock for compatibility with the query string if it uses 'self.sales_data'
    class MockSelf:
        def __init__(self, s, f, seg):
            self.sales_data = s
            self.final_plan = f
            self.segmentation = seg
    
    self = MockSelf(sales_data, final_plan, segmentation)
    
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
    
    def run(self, prompt: str) -> str:
        """
        Override base run() to handle multi-turn tool execution.
        The agent may call query_data, and we need to feed the result back for interpretation.
        """
        if not self.client:
            return "Error: GOOGLE_API_KEY not set."

        print(f"[{self.name}] Thinking...")
        
        from google.genai import types
        
        # Prepare tools
        tool_list = [func for func in self.tools.values()] if self.tools else None
        
        # Create chat session
        chat = self.client.chats.create(
            model=self.model_name,
            config=types.GenerateContentConfig(
                temperature=self.model_config.get('temperature', 0.2),
                max_output_tokens=self.model_config.get('max_output_tokens', 2048),
                tools=tool_list,
                system_instruction=self.system_instruction
            ),
            history=self.history
        )

        try:
            # First turn: Send user question
            response = chat.send_message(prompt)
            
            # Check for valid response
            if not response.candidates or not response.candidates[0].content:
                print(f"[{self.name}] Warning: Empty response from model.")
                return "Error: Model returned empty content."
            
            candidate = response.candidates[0]
            
            # Check if model called query_data tool
            tool_results = []
            for part in candidate.content.parts:
                if part.function_call:
                    func_name = part.function_call.name
                    args = part.function_call.args
                    
                    print(f"[{self.name}] Tool Call: {func_name}")
                    
                    if func_name in self.tools:
                        try:
                            tool_args = self._to_python_types(args)
                            result = self.tools[func_name](**tool_args)
                            tool_results.append({
                                "name": func_name,
                                "result": str(result)
                            })
                        except Exception as e:
                            print(f"[{self.name}] Tool Execution Error: {e}")
                            tool_results.append({
                                "name": func_name,
                                "result": f"Error: {e}"
                            })
            
            # If tools were called, send results back and get final answer
            if tool_results:
                # Build function response
                function_response_parts = []
                for tr in tool_results:
                    function_response_parts.append(
                        types.Part(function_response=types.FunctionResponse(
                            name=tr["name"],
                            response={"result": tr["result"]}
                        ))
                    )
                
                # Send tool results back
                response2 = chat.send_message(
                    types.Content(parts=function_response_parts)
                )
                
                if response2.candidates and response2.candidates[0].content:
                    text_response = response2.text
                else:
                    # Fallback: just return the tool result
                    text_response = tool_results[0]["result"]
            else:
                # No tool call, just return text
                text_response = response.text if response.text else "Error: No response generated."
            
            # Update history
            self.history.append(types.Content(role="user", parts=[types.Part(text=prompt)]))
            self.history.append(types.Content(role="model", parts=[types.Part(text=text_response)]))
            
            # Log to memory
            self.memory_store.log_interaction(prompt, text_response, self.name)
            
            print(f"[{self.name}] Response: {text_response[:100]}...")
            return text_response

        except Exception as e:
            print(f"[{self.name}] Error during generation: {e}")
            return f"Error: {e}"
    
    def _to_python_types(self, obj):
        """Recursively converts Protobuf Map/List to native Python dict/list."""
        if hasattr(obj, 'items'): # MapComposite
            return {k: self._to_python_types(v) for k, v in obj.items()}
        elif hasattr(obj, '__iter__') and not isinstance(obj, (str, bytes)): # RepeatedComposite
            return [self._to_python_types(v) for v in obj]
        else:
            return obj
