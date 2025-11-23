from agents.chart_agent import ChartAgent
import pandas as pd
import numpy as np

# Create dummy data: 2 years (2024-2025)
# 2024 is History (Sales), 2025 is Forecast (Plan)
dates = pd.date_range(start='2024-01-01', end='2025-12-31', freq='W-MON')
df = pd.DataFrame({
    'Date': dates,
    'SKU': ['SKU_001'] * len(dates),
    'Sales': [100 if d.year == 2024 else np.nan for d in dates],
    'Constrained_Plan': [np.nan if d.year == 2024 else 120 for d in dates]
})

agent = ChartAgent()

print("--- Test 1: Last 6 Months (should be late 2024) ---")
query1 = "show me sales for the last 6 months"
# We expect data from July 2024 to Dec 2024
# Since we can't see the internal DF, we rely on the output config labels.
try:
    result1 = agent.run(query1, df.copy())
    print("Result generated.")
    if "2024-07" in result1 or "2024-08" in result1:
        print("SUCCESS: Found late 2024 dates.")
    else:
        print("FAILURE: Did not find expected dates.")
        print(result1[:200]) # Print start of result
except Exception as e:
    print(f"Error: {e}")

print("\n--- Test 2: Next 6 Months (should be early 2025) ---")
query2 = "show me forecast for the next 6 months"
try:
    result2 = agent.run(query2, df.copy())
    print("Result generated.")
    if "2025-01" in result2 or "2025-02" in result2:
        print("SUCCESS: Found early 2025 dates.")
    else:
        print("FAILURE: Did not find expected dates.")
        print(result2[:200])
except Exception as e:
    print(f"Error: {e}")
