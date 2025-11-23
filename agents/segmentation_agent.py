from agents.base_agent import BaseAgent
import pandas as pd

class SegmentationAndPlaybookAgent(BaseAgent):
    def __init__(self, policy_context: dict = None):
        super().__init__(name="SegmentationAgent")
        self.policy_context = policy_context or {}
        self.sku_metrics = None
        self.playbooks = {}
        
        self.register_tool(self.calculate_metrics)
        self.register_tool(self.assign_segment)
        
        self.set_system_instruction(
            """
            You are the Segmentation Agent.
            Your goal is to classify SKUs into segments (stable_seasonal, intermittent, promo_sensitive) based on their volatility (CV) and zero-sales proportion.
            1. Calculate metrics first.
            2. Then assign a segment to each SKU.
            3. Use the policy context to identify strategic SKUs.
            """
        )

    def calculate_metrics(self, df_summary: str) -> str:
        """
        Calculates volatility (CV) and intermittency.
        (Note: In a real agent, we'd pass the full DF, but for LLM context limits, we might pass a summary or handle this in Python).
        Here we assume the agent calls this to trigger the calculation on the internal DF state passed via `run`.
        """
        # This tool is a bit "meta" - it operates on the state injected during `run`
        if self.sku_metrics is None:
            return "Error: Data not provided to agent yet."
            
        return self.sku_metrics.to_string()

    def assign_segment(self, sku: str, segment: str) -> str:
        """Assigns a segment to a SKU and creates a playbook."""
        is_strategic = sku in self.policy_context.get('strategic_skus', [])
        
        self.playbooks[sku] = {
            'segment': segment,
            'is_strategic': is_strategic,
            'model_family': 'ETS' if segment == 'stable_seasonal' else 'Croston' if segment == 'intermittent' else 'Regression',
            'features': ['Promo_Flag', 'Season'] if segment == 'promo_sensitive' else ['Season']
        }
        return f"Assigned {sku} to {segment}."

    def run(self, df: pd.DataFrame, prompt: str = None) -> tuple:
        """
        Runs the segmentation process.
        """
        # Pre-calculate metrics in Python to save tokens/complexity, 
        # but let the LLM "decide" the segmentation logic based on those metrics.
        
        self.sku_metrics = df.groupby('SKU').agg({
            'Sales_Cleaned': ['mean', 'std', lambda x: (x == 0).mean()]
        })
        self.sku_metrics.columns = ['mean_sales', 'std_sales', 'zero_proportion']
        self.sku_metrics['cv'] = self.sku_metrics['std_sales'] / self.sku_metrics['mean_sales']
        
        # Convert metrics to a readable string for the LLM
        metrics_str = self.sku_metrics.to_string()
        
        prompt = f"""
        Here are the metrics for the SKUs:
        {metrics_str}
        
        Please assign a segment to each SKU using the 'assign_segment' tool.
        Rules:
        - If zero_proportion > 0.5 -> 'intermittent'
        - If cv < 0.3 -> 'stable_seasonal'
        - Otherwise -> 'promo_sensitive'
        """
        
        super().run(prompt)
        
        # Fallback for PoC
        if not self.playbooks:
            print(f"[{self.name}] FALLBACK: Manually assigning segments.")
            # Simple heuristic
            for sku, row in self.sku_metrics.iterrows():
                if row['zero_proportion'] > 0.5: seg = 'intermittent'
                elif row['cv'] < 0.3: seg = 'stable_seasonal'
                else: seg = 'promo_sensitive'
                self.assign_segment(sku, seg)
                
        return self.playbooks, self.sku_metrics

if __name__ == "__main__":
    pass
