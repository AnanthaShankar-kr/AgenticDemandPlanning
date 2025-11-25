from agents.policy_agent import PolicyAndGuardrailAgent
from agents.data_agent import DataAndSignalAgent
from agents.segmentation_agent import SegmentationAndPlaybookAgent
from agents.baseline_agent import BaselineForecastAgent
from agents.scenario_agent import EventAndScenarioAgent
from agents.negotiation_agent import MicroNegotiationAgent
from agents.monitor_agent import MonitorExplainLearnAgent
from agents.analyst_agent import DataAnalystAgent
import pandas as pd
import os

class OrchestratorAgent:
    def __init__(self):
        self.policy_agent = PolicyAndGuardrailAgent()
        self.data_agent = DataAndSignalAgent()
        self.segmentation_agent = SegmentationAndPlaybookAgent()
        self.baseline_agent = BaselineForecastAgent()
        self.scenario_agent = EventAndScenarioAgent()
        self.negotiation_agent = MicroNegotiationAgent()
        self.monitor_agent = MonitorExplainLearnAgent()
        self.analyst_agent = DataAnalystAgent()

    def route_request(self, user_message: str) -> str:
        """
        Routes the user message to the appropriate agent based on intent.
        """
        msg_lower = user_message.lower()
        
        # Simple keyword-based routing for PoC
        # In a real system, we'd use an LLM to classify intent.
        
        if any(k in msg_lower for k in ["policy", "strategy", "rule", "guardrail", "priority"]):
            return self.policy_agent.run(user_message)
            
        if any(k in msg_lower for k in ["data", "sales", "sell", "sold", "forecast", "plan", "sku", "trend", "volume", "how many", "how much"]):
            # This is likely a data question
            return self.analyst_agent.run(user_message)
            
        # Default to Policy/General agent for generic questions
        return self.policy_agent.run(user_message)

    def run(self):
        import io
        import contextlib
        import sys

        logs = []
        
        def log(msg):
            logs.append(msg)
            sys.__stdout__.write(msg + "\n")

        def run_step(step_name, func, *args, **kwargs):
            log(f"[Orchestrator] {step_name}...")
            f = io.StringIO()
            result = None
            try:
                with contextlib.redirect_stdout(f):
                    result = func(*args, **kwargs)
            except Exception as e:
                print(f"Error in {step_name}: {e}")
            
            output = f.getvalue()
            if output:
                for line in output.splitlines():
                    if line.strip():
                        logs.append(line)
                        sys.__stdout__.write(line + "\n")
            return result

        log("[Orchestrator] Starting Demand Planning Cycle...")
        
        # 1. Policy & Guardrails
        policy_context = run_step("Step 1: Retrieving Policy & Guardrails", self.policy_agent.run, "Retrieve current policies and guardrails.")
        
        # Handle Policy Context
        if isinstance(policy_context, dict) and 'policy_context' in policy_context:
             policy_context = policy_context['policy_context']
        elif not isinstance(policy_context, dict):
             policy_context = {'strategic_skus': ['SKU_001', 'SKU_005'], 'constraints': {'max_promo_uplift': 0.5}}
        
        log(f"[Orchestrator] Policy Context Loaded: {list(policy_context.keys())}")
        
        # Inject context
        self.segmentation_agent.policy_context = policy_context
        self.scenario_agent.policy_context = policy_context
        self.negotiation_agent.policy_context = policy_context
        
        # 2. Data & Signals
        clean_data_df = run_step("Step 2: Processing Data & Signals", self.data_agent.run, prompt="Load data, detect anomalies, and clean if necessary.")
        if clean_data_df is None: clean_data_df = pd.DataFrame()
        log(f"[Orchestrator] Data Loaded. Shape: {clean_data_df.shape}")
        
        # 3. Segmentation
        res = run_step("Step 3: Running Segmentation", self.segmentation_agent.run, clean_data_df, prompt="Calculate volatility and assign segments to SKUs.")
        if res:
            playbooks, metrics = res
            log(f"[Orchestrator] Segmentation Complete.")
            
            # Save segmentation to disk for AnalystAgent
            try:
                # playbooks is dict {sku: segment}
                seg_df = pd.DataFrame(list(playbooks.items()), columns=['SKU', 'Segment'])
                seg_df.to_csv("data/segmentation.csv", index=False)
            except Exception as e:
                log(f"[Orchestrator] Error saving segmentation: {e}")
        else:
            playbooks, metrics = {}, {}
        
        # 4. Baseline Forecast
        baseline_forecast = run_step("Step 4: Generating Baseline Forecast", self.baseline_agent.run, clean_data_df, playbooks, prompt="Generate baseline forecasts for all SKUs.")
        if baseline_forecast is None: baseline_forecast = pd.DataFrame()
        log(f"[Orchestrator] Baseline Forecast Generated.")
        
        # 5. Events & Scenarios
        scenario_plan = run_step("Step 5: Applying Scenarios & Events", self.scenario_agent.run, baseline_forecast, prompt="Apply event uplifts and create scenarios.")
        if scenario_plan is None: scenario_plan = pd.DataFrame()
        log(f"[Orchestrator] Scenarios Applied.")
        
        # 6. Micro-Negotiation
        final_plan = run_step("Step 6: Optimizing & Negotiating", self.negotiation_agent.run, scenario_plan, prompt="Check capacity constraints and adjust plan if needed.")
        if final_plan is None: final_plan = pd.DataFrame()
        log(f"[Orchestrator] Final Plan Optimized.")
        
        # Save to disk so AnalystAgent can see it
        try:
            final_plan.to_csv("data/final_plan.csv", index=False)
            log(f"[Orchestrator] Final Plan Saved to Disk.")
        except Exception as e:
            log(f"[Orchestrator] Error saving plan: {e}")

        # 7. Monitor & Explain
        final_report = run_step("Step 7: Generating Final Report", self.monitor_agent.run, final_plan, prompt="Review the final plan and generate a summary report.")
        if final_report is None: final_report = "Error generating report."
        log(f"[Orchestrator] Report Generated.")
        
        log("[Orchestrator] Cycle Complete.")
        
        # Format the report for the UI
        formatted_report = ""
        if isinstance(final_report, dict):
            # Extract explanation (LLM text)
            if 'explanations' in final_report and final_report['explanations']:
                formatted_report += final_report['explanations'][0]
            
            # Append metrics
            if 'metrics' in final_report and isinstance(final_report['metrics'], dict):
                formatted_report += "\n\n**Key Metrics:**\n"
                for k, v in final_report['metrics'].items():
                    # Format numbers nicely
                    val = v
                    if isinstance(v, float):
                        val = f"{v:,.2f}"
                    formatted_report += f"- **{k}**: {val}\n"
        else:
            formatted_report = str(final_report)

        return final_plan, {
            "metrics": {"status": "success"},
            "explanations": [formatted_report],
            "learnings": ["System ran successfully."],
            "logs": logs
        }

if __name__ == "__main__":
    orchestrator = OrchestratorAgent()
    orchestrator.run()
