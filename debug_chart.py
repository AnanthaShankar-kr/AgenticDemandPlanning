from agents.chart_agent import ChartAgent
import pandas as pd
import os

# Mock data loading
if os.path.exists("data/final_plan.csv"):
    df = pd.read_csv("data/final_plan.csv")
else:
    print("No final_plan.csv found. Creating dummy data.")
    df = pd.DataFrame({
        'Date': ['2025-01-01', '2025-01-08'],
        'SKU': ['SKU_001', 'SKU_001'],
        'Constrained_Plan': [100, 120],
        'Baseline_P50': [90, 110],
        'Upside': [110, 130]
    })

agent = ChartAgent()
query = "create a line chart showing the the future forecast for SKU_001 for the next one year. show the baseline and the upside forecasts in different colors."

print("--- Running ChartAgent ---")
try:
    result = agent.run(query, df)
    print("\n--- Result ---")
    print(result)
    print("\n--- Type ---")
    print(type(result))
except Exception as e:
    print(f"\n--- Error ---")
    print(e)
