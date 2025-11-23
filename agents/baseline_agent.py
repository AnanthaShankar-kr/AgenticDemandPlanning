from agents.base_agent import BaseAgent
import pandas as pd
import numpy as np
from statsmodels.tsa.holtwinters import ExponentialSmoothing

class BaselineForecastAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="BaselineAgent")
        self.forecasts = []
        
        self.register_tool(self.run_forecast_model)
        
        self.set_system_instruction(
            """
            You are the Baseline Forecast Agent.
            Your goal is to generate probabilistic forecasts for each SKU based on its assigned playbook.
            You will be given the playbook and data.
            For each SKU, decide which model to run (ETS, Croston, or Regression) and call 'run_forecast_model'.
            """
        )

    def run_forecast_model(self, sku: str, model_family: str, horizon: int = 12) -> str:
        """
        Runs the specified forecasting model for a SKU.
        """
        # We need access to the data here. In a real system, we might fetch from a store.
        # Here we rely on the state injected via `run`.
        if not hasattr(self, 'df'): return "Error: Data not loaded."
        
        sku_data = self.df[self.df['SKU'] == sku].sort_values('Date')
        series = sku_data['Sales_Cleaned'].values
        
        try:
            if model_family == 'ETS':
                # Check if enough data for seasonal
                if len(series) < 52 * 2:
                     model = ExponentialSmoothing(series, trend='add').fit()
                else:
                     model = ExponentialSmoothing(series, seasonal='add', seasonal_periods=52).fit()
                pred = model.forecast(horizon)
            elif model_family == 'Croston':
                mean_val = np.mean(series[series > 0]) if np.sum(series > 0) > 0 else 0
                pred = np.full(horizon, mean_val * 0.5)
            else:
                pred = np.full(horizon, np.mean(series))
            
            # Bounds
            std_resid = np.std(series - np.mean(series))
            p50 = pred
            p10 = pred - 1.28 * std_resid
            p90 = pred + 1.28 * std_resid
            
            last_date = sku_data['Date'].max()
            future_dates = [last_date + pd.Timedelta(weeks=i+1) for i in range(horizon)]
            
            sku_forecast = pd.DataFrame({
                'Date': future_dates,
                'SKU': sku,
                'Baseline_P10': np.maximum(p10, 0),
                'Baseline_P50': np.maximum(p50, 0),
                'Baseline_P90': np.maximum(p90, 0)
            })
            self.forecasts.append(sku_forecast)
            return f"Forecast generated for {sku} using {model_family}."
            
        except Exception as e:
            return f"Error forecasting {sku}: {e}"

    def run(self, df: pd.DataFrame, playbooks: dict, horizon: int = 12, prompt: str = None) -> pd.DataFrame:
        self.df = df
        self.forecasts = []
        
        # We can iterate through SKUs and ask the LLM to forecast each, 
        # or ask it to iterate. For efficiency in PoC, we'll ask it to iterate.
        
        # Construct a prompt with the playbooks
        playbook_summary = "\n".join([f"{sku}: {details['model_family']}" for sku, details in playbooks.items()])
        
        prompt = f"""
        Here are the playbooks for the SKUs:
        {playbook_summary}
        
        Please run the forecast for each SKU using the 'run_forecast_model' tool.
        The horizon is {horizon}.
        """
        
        super().run(prompt)
        
        # Fallback for PoC
        if not self.forecasts:
            print(f"[{self.name}] FALLBACK: Manually running forecasts.")
            for sku, details in playbooks.items():
                self.run_forecast_model(sku, details['model_family'], horizon)
        
        if self.forecasts:
            return pd.concat(self.forecasts, ignore_index=True)
        return pd.DataFrame()

if __name__ == "__main__":
    pass
