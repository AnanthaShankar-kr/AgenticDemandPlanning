from agents.base_agent import BaseAgent
import pandas as pd
import json
from typing import List, Dict, Any
import math

class ChartAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="ChartAgent")
        self.register_tool(self.generate_chart_config)
        
        self.set_system_instruction(
            """
            You are the Chart Agent.
            Your goal is to visualize data for the user.
            You will receive a query and a data summary.
            You must decide on the best chart type (line, bar, pie, etc.) and call 'generate_chart_config'.
            The config must be valid JSON compatible with Chart.js.
            """
        )

    def generate_chart_config(self, title: str, chart_type: str, labels: List[str], datasets: List[Dict[str, Any]]) -> str:
        """
        Generates a Chart.js configuration.
        Args:
            title: Title of the chart.
            chart_type: 'line', 'bar', 'pie', 'doughnut'.
            labels: List of labels for the X-axis.
            datasets: List of dictionaries, each containing 'label' and 'data' (list of numbers).
                      Example: [{'label': 'Sales', 'data': [10, 20, 30]}]
        """
        # Clean NaNs from datasets to ensure valid JSON
        for dataset in datasets:
            cleaned_data = []
            for x in dataset['data']:
                # Check for NaN (x != x) or Inf
                if isinstance(x, float) and (x != x or x == float('inf') or x == float('-inf')):
                    cleaned_data.append(None)
                else:
                    cleaned_data.append(x)
            dataset['data'] = cleaned_data

        config = {
            "type": chart_type,
            "data": {
                "labels": labels,
                "datasets": datasets
            },
            "options": {
                "responsive": True,
                "plugins": {
                    "title": {
                        "display": True,
                        "text": title
                    },
                    "legend": {
                        "position": 'top',
                    }
                }
            }
        }
        return json.dumps(config)

    def run(self, query: str, data_context: pd.DataFrame) -> str:
        """
        Analyzes the data and generates a chart config based on the query.
        """
        # 1. Pre-filter data if specific SKU is mentioned
        # Simple heuristic to find SKU_XXX
        import re
        sku_match = re.search(r'(SKU_\d+)', query, re.IGNORECASE)
        if sku_match:
            sku = sku_match.group(1).upper()
            # Filter for this SKU
            if 'SKU' in data_context.columns:
                filtered_df = data_context[data_context['SKU'] == sku]
                if not filtered_df.empty:
                    data_context = filtered_df
        
        # 1.5 Date Filtering
        if 'Date' in data_context.columns:
            data_context['Date'] = pd.to_datetime(data_context['Date'])
            
            # Determine "Current Date" (Split between History and Forecast)
            # We assume 'Sales' indicates history.
            if 'Sales' in data_context.columns and data_context['Sales'].notna().any():
                current_date = data_context[data_context['Sales'].notna()]['Date'].max()
            else:
                # If no sales data, maybe we are only looking at forecast?
                # Or maybe it's all history?
                # Let's default to the middle of the dataset or the start?
                # Safer to default to today's actual date? Or the dataset max?
                # Let's use the dataset min as a fallback for "next" and max for "last" if ambiguous.
                # But for this PoC, let's assume current_date is the last date of the dataset if Sales is missing.
                current_date = data_context['Date'].max()

            # Filter by Year (e.g., "2025")
            year_match = re.search(r'\b(202[0-9])\b', query)
            if year_match:
                year = int(year_match.group(1))
                print(f"[{self.name}] Filtering for Year: {year}")
                data_context = data_context[data_context['Date'].dt.year == year]

            # Filter "Last N Months"
            last_month_match = re.search(r'last (\d+) month', query, re.IGNORECASE)
            if last_month_match:
                n_months = int(last_month_match.group(1))
                print(f"[{self.name}] Filtering for Last {n_months} Months")
                start_date = current_date - pd.DateOffset(months=n_months)
                data_context = data_context[(data_context['Date'] >= start_date) & (data_context['Date'] <= current_date)]

            # Filter "Next N Months"
            next_month_match = re.search(r'next (\d+) month', query, re.IGNORECASE)
            if next_month_match:
                n_months = int(next_month_match.group(1))
                print(f"[{self.name}] Filtering for Next {n_months} Months")
                end_date = current_date + pd.DateOffset(months=n_months)
                data_context = data_context[(data_context['Date'] > current_date) & (data_context['Date'] <= end_date)]
        
        # 2. Aggregation Logic
        # Check for aggregation keywords
        if 'Date' in data_context.columns:
            data_context['Date'] = pd.to_datetime(data_context['Date'])
            
            if 'monthly' in query.lower() or 'month' in query.lower():
                print(f"[{self.name}] Aggregating data to Monthly frequency.")
                # Resample to Month Start (MS) or Month End (M)
                # Select numeric columns for aggregation
                numeric_cols = data_context.select_dtypes(include=['number']).columns
                # Group by Date (resampled) and sum
                data_context = data_context.set_index('Date').resample('MS')[numeric_cols].sum().reset_index()
                
            elif 'quarterly' in query.lower() or 'quarter' in query.lower():
                print(f"[{self.name}] Aggregating data to Quarterly frequency.")
                numeric_cols = data_context.select_dtypes(include=['number']).columns
                data_context = data_context.set_index('Date').resample('QS')[numeric_cols].sum().reset_index()

        # 3. Convert dataframe to JSON
        # Increase limit to allow for full history (104 weeks is ~2 years)
        # 500 rows is safe for a single SKU (104 rows)
        data_str = data_context.head(500).to_json(orient='records')
        
        prompt = f"""
        User Query: "{query}"
        
        Data (first 500 rows):
        {data_str}
        
        Instructions:
        1. Analyze the data and query.
        2. Use the 'generate_chart_config' tool to create the chart configuration.
        3. IMPORTANT: Your final response MUST be ONLY the JSON string returned by the tool. Do not add any explanation or markdown formatting.
        """
        
        response = super().run(prompt)
        
        # Fallback for PoC if LLM fails or no key
        if "{" not in response and "}" not in response:
             print(f"[{self.name}] FALLBACK: Generating default chart.")
             # Default to a simple line chart of the first numeric column
             numeric_cols = data_context.select_dtypes(include=['number']).columns
             if len(numeric_cols) > 0:
                 col = numeric_cols[0]
                 return self.generate_chart_config(
                     title=f"{col} Overview",
                     chart_type="line",
                     labels=data_context['Date'].astype(str).tolist() if 'Date' in data_context.columns else list(range(len(data_context))),
                     datasets=[{'label': col, 'data': data_context[col].tolist()}]
                 )
        
        # Extract JSON from response if it's embedded in text
        # This is a simple heuristic; a real agent would return structured output directly.
        try:
            # Find the first '{' and last '}'
            start = response.find('{')
            end = response.rfind('}') + 1
            if start != -1 and end != -1:
                return response[start:end]
        except:
            pass
            
        return response

if __name__ == "__main__":
    pass
