import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta

def generate_synthetic_data(
    num_skus=10,
    weeks=104,
    start_date="2024-01-01",
    output_path="data/sales_data.csv"
):
    """
    Generates synthetic SKU-week sales data with seasonality, trend, and noise.
    Also injects some anomalies and external signals.
    """
    np.random.seed(42)
    
    dates = [datetime.strptime(start_date, "%Y-%m-%d") + timedelta(weeks=i) for i in range(weeks)]
    skus = [f"SKU_{i:03d}" for i in range(1, num_skus + 1)]
    
    data = []
    
    for sku in skus:
        # Random base level
        base_level = np.random.randint(100, 1000)
        
        # Random trend
        trend = np.linspace(0, np.random.uniform(-0.5, 0.5), weeks) * base_level
        
        # Seasonality (sine wave)
        seasonality = np.sin(np.linspace(0, 2 * np.pi, weeks)) * (base_level * 0.2)
        
        # Noise
        noise = np.random.normal(0, base_level * 0.1, weeks)
        
        # Combine components
        sales = base_level + trend + seasonality + noise
        sales = np.maximum(sales, 0) # Ensure non-negative
        
        # Inject anomalies
        if np.random.random() < 0.3: # 30% chance of having anomalies
            anomaly_idx = np.random.randint(0, weeks, 2)
            sales[anomaly_idx] *= np.random.choice([0.1, 3.0]) # Drop or spike
            
        # External signals
        promo_flag = np.random.choice([0, 1], size=weeks, p=[0.9, 0.1])
        # Add promo effect
        sales += promo_flag * (base_level * 0.5)
        
        for i, date in enumerate(dates):
            data.append({
                "Date": date,
                "SKU": sku,
                "Sales": int(sales[i]),
                "Promo_Flag": promo_flag[i],
                "Marketing_Spend": np.random.randint(1000, 5000) if promo_flag[i] else np.random.randint(0, 500)
            })
            
    df = pd.DataFrame(data)
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    df.to_csv(output_path, index=False)
    print(f"Generated data saved to {output_path}")
    return df

if __name__ == "__main__":
    generate_synthetic_data()
