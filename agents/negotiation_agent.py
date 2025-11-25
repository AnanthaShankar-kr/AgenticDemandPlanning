from agents.base_agent import BaseAgent
import pandas as pd

class MicroNegotiationAgent(BaseAgent):
    def __init__(self, policy_context: dict = None):
        super().__init__(name="NegotiationAgent")
        self.policy_context = policy_context or {}
        self.constrained_plan = None
        
        self.register_tool(self.check_capacity)
        self.register_tool(self.cut_allocation)
        
        self.set_system_instruction(
            """
            You are the Micro-Negotiation Agent.
            Your goal is to ensure the demand plan respects capacity constraints.
            1. Check capacity for each week.
            2. If capacity is exceeded, identify which SKUs to cut based on priority.
            3. Use 'cut_allocation' to reduce the plan.
            Strategic SKUs (in policy) should be protected if possible.
            """
        )

    def check_capacity(self, week_date: str) -> str:
        """Checks if total demand exceeds capacity for a given week."""
        if self.constrained_plan is None: return "Error: Plan not loaded."
        
        # Parse date
        try:
            date = pd.to_datetime(week_date)
        except:
            return "Invalid date format."
            
        # Filter for week
        # Exact match might be tricky with strings, so let's assume the agent iterates through unique dates provided in prompt
        # Or simpler: we check ALL weeks and return the ones with issues.
        pass 

    def check_all_weeks(self) -> str:
        """Checks all weeks for capacity violations."""
        capacity_limit = self.policy_context.get('constraints', {}).get('capacity_limit_total', 10000)
        
        issues = []
        for date, group in self.constrained_plan.groupby('Date'):
            total_demand = group['Constrained_Plan'].sum()
            if total_demand > capacity_limit:
                shortage = total_demand - capacity_limit
                issues.append(f"Week {date.date()}: Demand {total_demand:.0f} > Cap {capacity_limit}. Shortage: {shortage:.0f}")
        
        if not issues:
            return "No capacity violations found."
        return "\n".join(issues)

    def cut_allocation(self, sku: str, week_date: str, amount: float) -> str:
        """Cuts the allocation for a SKU in a specific week."""
        # Implementation similar to previous logic but triggered by LLM
        # For PoC simplicity, let's assume the LLM calls this with specific instructions
        
        try:
            date = pd.to_datetime(week_date)
            mask = (self.constrained_plan['Date'] == date) & (self.constrained_plan['SKU'] == sku)
            
            if not mask.any():
                return f"SKU {sku} not found in week {week_date}."
                
            current_plan = self.constrained_plan.loc[mask, 'Constrained_Plan'].values[0]
            new_plan = max(0, current_plan - amount)
            
            self.constrained_plan.loc[mask, 'Constrained_Plan'] = new_plan
            self.constrained_plan.loc[mask, 'Negotiation_Log'] += f" Cut {amount} by Agent."
            
            return f"Cut {sku} by {amount} in week {week_date}. New plan: {new_plan}."
            
        except Exception as e:
            return f"Error cutting allocation: {e}"

    def run(self, scenarios: pd.DataFrame, prompt: str = None) -> pd.DataFrame:
        self.constrained_plan = scenarios.copy()
        self.constrained_plan['Constrained_Plan'] = self.constrained_plan['Plan']
        self.constrained_plan['Negotiation_Log'] = ""
        
        # Register the bulk check tool instead of single week for efficiency
        self.tools = {} # Reset tools to avoid confusion
        self.register_tool(self.check_all_weeks)
        self.register_tool(self.cut_allocation)
        
        prompt = f"""
        Please check all weeks for capacity violations using 'check_all_weeks'.
        If there are violations, decide which SKUs to cut to resolve the shortage.
        Strategic SKUs: {self.policy_context.get('strategic_skus', [])}
        Use 'cut_allocation' to apply cuts.
        """
        
        super().run(prompt)
        
        # Fallback for PoC
        if (self.constrained_plan['Negotiation_Log'] == "").all():
             print(f"[{self.name}] FALLBACK: Manually checking and cutting capacity violations.")
             capacity_limit = self.policy_context.get('constraints', {}).get('capacity_limit_total', 10000)
             strategic_skus = self.policy_context.get('strategic_skus', [])
             
             # Check each week and cut if needed
             for date, group in self.constrained_plan.groupby('Date'):
                 total_demand = group['Constrained_Plan'].sum()
                 if total_demand > capacity_limit:
                     shortage = total_demand - capacity_limit
                     print(f"[{self.name}] Week {date.date()}: Demand {total_demand:.0f} > Cap {capacity_limit}. Cutting {shortage:.0f} units.")
                     
                     # Sort SKUs by priority (non-strategic first, then by volume)
                     week_data = group.copy()
                     week_data['is_strategic'] = week_data['SKU'].isin(strategic_skus)
                     week_data = week_data.sort_values(['is_strategic', 'Constrained_Plan'], ascending=[True, False])
                     
                     # Cut from lowest priority SKUs
                     remaining_to_cut = shortage
                     for idx, row in week_data.iterrows():
                         if remaining_to_cut <= 0:
                             break
                         
                         sku = row['SKU']
                         current_plan = row['Constrained_Plan']
                         cut_amount = min(current_plan, remaining_to_cut)
                         
                         if cut_amount > 0:
                             # Apply the cut
                             self.constrained_plan.at[idx, 'Constrained_Plan'] -= cut_amount
                             self.constrained_plan.at[idx, 'Negotiation_Log'] = f"Cut {cut_amount:.0f} due to capacity limit"
                             remaining_to_cut -= cut_amount
             
        return self.constrained_plan

if __name__ == "__main__":
    pass
