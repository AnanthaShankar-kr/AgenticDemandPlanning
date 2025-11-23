from agents.chart_agent import ChartAgent
import pandas as pd
import os

# Create dummy weekly data
dates = pd.date_range(start='2024-01-01', periods=12, freq='W-MON')
df = pd.DataFrame({
    'Date': dates,
    'SKU': ['SKU_001'] * 12,
    'Sales': [100] * 12  # 100 per week
})

agent = ChartAgent()
query = "show me monthly sales for SKU_001"

print("--- Running ChartAgent with Aggregation ---")
try:
    # We want to see if the data passed to the prompt (and thus the chart) is aggregated.
    # Since we can't easily inspect the internal variable, we'll check the output config.
    # If aggregated, we expect fewer data points (3 months vs 12 weeks) and higher values (approx 400-500).
    
    # Actually, let's just run it and print the result.
    result = agent.run(query, df)
    print("\n--- Result ---")
    print(result)
except Exception as e:
    print(f"\n--- Error ---")
    print(e)
