#!/usr/bin/env python3
"""Quick test to verify AnalystAgent works with valid API key"""
import sys
sys.path.append('.')

from agents.analyst_agent import DataAnalystAgent

# Test the agent
agent = DataAnalystAgent()

# Test 1: Simple policy question (no tool needed)
print("=" * 60)
print("Test 1: Policy Question")
print("=" * 60)
response1 = agent.run("What is the maximum allowed promo uplift?")
print(f"Response: {response1}")
print()

# Test 2: Data query (requires query_data tool)
print("=" * 60)
print("Test 2: Data Query")
print("=" * 60)
response2 = agent.run("Show me the sales history for SKU_001")
print(f"Response: {response2}")
print()

# Test 3: Explain cuts (requires query_data tool)
print("=" * 60)
print("Test 3: Explain Cuts")
print("=" * 60)
response3 = agent.run("Why was the plan for SKU_002 reduced?")
print(f"Response: {response3}")
print()

print("=" * 60)
print("All tests completed!")
print("=" * 60)
