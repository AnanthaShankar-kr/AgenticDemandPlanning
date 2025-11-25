from agents.base_agent import BaseAgent
import pandas as pd

class EventAndScenarioAgent(BaseAgent):
    def __init__(self, policy_context: dict = None):
        super().__init__(name="ScenarioAgent")
        self.policy_context = policy_context or {}
        self.scenarios = None
        
        self.register_tool(self.apply_event_uplift)
        
        self.set_system_instruction(
            """
            You are the Scenario Agent.
            Your job is to layer events onto the baseline forecast to create Plan, Upside, and Downside scenarios.
            You should identify where events happen (simulated here) and apply uplifts using the tool.
            """
        )

    def apply_event_uplift(self, sku: str, week_offset: int, uplift_pct: float) -> str:
        """
        Applies an uplift to a specific SKU and week.
        """
        if self.scenarios is None: return "Error: Scenarios not initialized."
        
        # Find the row
        # Assuming scenarios is sorted by Date
        # We need to find the date corresponding to week_offset (0-indexed from start of forecast)
        
        sku_mask = self.scenarios['SKU'] == sku
        sku_indices = self.scenarios[sku_mask].index
        
        if week_offset >= len(sku_indices):
            return f"Week offset {week_offset} out of bounds for {sku}."
            
        idx = sku_indices[week_offset]
        
        # Check guardrails
        constraints = self.policy_context.get('constraints', {})
        if not isinstance(constraints, dict):
            constraints = {}
            
        max_uplift = constraints.get('max_promo_uplift', 0.5)
        if uplift_pct > max_uplift:
            uplift_pct = max_uplift
            msg = f"Uplift capped at {max_uplift} due to policy."
        else:
            msg = "Uplift applied."
            
        base_plan = self.scenarios.at[idx, 'Plan']
        uplift_val = base_plan * uplift_pct
        
        self.scenarios.at[idx, 'Plan'] += uplift_val
        self.scenarios.at[idx, 'Upside'] += uplift_val * 1.2
        self.scenarios.at[idx, 'Downside'] += uplift_val * 0.8
        
        return f"Applied {uplift_pct} uplift to {sku} at week {week_offset}. {msg}"

    def run(self, baseline_forecasts: pd.DataFrame, prompt: str = None) -> pd.DataFrame:
        self.scenarios = baseline_forecasts.copy()
        self.scenarios['Plan'] = self.scenarios['Baseline_P50']
        self.scenarios['Upside'] = self.scenarios['Baseline_P90']
        self.scenarios['Downside'] = self.scenarios['Baseline_P10']
        
        # Prompt the LLM to simulate events
        # In a real app, we'd pass an event calendar.
        prompt = """
        Please simulate a promotional event for 'SKU_001' in week 4 (offset 4) with a 30% uplift.
        Also simulate a launch for 'SKU_005' in week 1 (offset 1) with a 50% uplift.
        Use the 'apply_event_uplift' tool.
        """
        
        super().run(prompt)
        
        # Fallback for PoC: Check if Plan is identical to Baseline (no events applied)
        if self.scenarios['Plan'].equals(self.scenarios['Baseline_P50']):
             print(f"[{self.name}] FALLBACK: Manually applying events from context.")
             events = self.policy_context.get('events', [])
             if not events:
                 # Default hardcoded if no context events
                 self.apply_event_uplift('SKU_001', 4, 0.3)
                 self.apply_event_uplift('SKU_005', 1, 0.5)
             else:
                 # Apply events from context
                 # We need to calculate week_offset. 
                 # Assuming scenarios is sorted by Date and we can find the index.
                 # But apply_event_uplift takes week_offset.
                 # Let's try to find the date match.
                 for event in events:
                     sku = event['SKU']
                     uplift = event['Uplift']
                     date_str = event['Date']
                     try:
                         event_date = pd.to_datetime(date_str)
                         # Find offset for this SKU
                         sku_data = self.scenarios[self.scenarios['SKU'] == sku]
                         if not sku_data.empty:
                             # Assuming sorted
                             start_date = sku_data['Date'].min()
                             # Calculate offset in weeks
                             days_diff = (event_date - start_date).days
                             offset = int(days_diff / 7)
                             if offset >= 0:
                                 self.apply_event_uplift(sku, offset, uplift)
                     except Exception as e:
                         print(f"Error applying fallback event: {e}")
             
        return self.scenarios

if __name__ == "__main__":
    pass
