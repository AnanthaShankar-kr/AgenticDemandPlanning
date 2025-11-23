from orchestrator import OrchestratorAgent
import pandas as pd

def main():
    print("=== Agentic Demand Planning PoC ===")
    orchestrator = OrchestratorAgent()
    final_plan, report = orchestrator.run()
    
    print("\n=== Final Report ===")
    print("Metrics:")
    for k, v in report['metrics'].items():
        print(f"  {k}: {v}")
        
    print("\nExplanations:")
    for exp in report['explanations']:
        print(f"  - {exp}")
        
    print("\nLearnings:")
    for learn in report['learnings']:
        print(f"  - {learn}")
        
    # Save outputs
    final_plan.to_csv("data/final_plan.csv", index=False)
    print("\nFinal plan saved to data/final_plan.csv")

if __name__ == "__main__":
    main()
