# Refinement Suggestions for AnalystAgent

Based on the evaluation run (2/7 Passed), here are suggestions to improve the agent's performance.

## 1. Test: `explain_cut_sku_002` (FAIL)
**Issue**: The agent returned a "Warning: Candidate content is empty" error, likely due to a `MALFORMED_FUNCTION_CALL`. This suggests the agent tried to call a tool (likely `query_data`) but the arguments were invalid or the model hallucinated a tool name.
**Suggestion**:
- **System Prompt**: Explicitly provide examples of valid `query_data` calls in the system prompt.
- **Tool Definition**: Ensure the `query_data` tool schema is robust and the agent understands it must pass valid Python code.
- **Error Handling**: Implement a retry mechanism or a clearer error message when the model generates malformed tool calls.

## 2. Test: `compare_baseline_vs_final_sku_001` (FAIL)
**Issue**: The agent provided a table but the explanation was considered "inaccurate" by the judge. It claimed the plan was "significantly higher" only in the last week, whereas the ground truth showed it was generally higher.
**Suggestion**:
- **System Prompt**: Add an instruction to "analyze the trend across the entire period" when comparing columns, not just the last data point.
- **Prompt Engineering**: Encourage the agent to calculate aggregate differences (e.g., "Total Baseline vs Total Plan") before generating the text explanation.

## 3. Test: `explain_segment_sku_005` (FAIL)
**Issue**: The agent claimed it "cannot answer... because the available tools lack the functionality to determine the segment".
**Suggestion**:
- **Data Availability**: The `segmentation` data is likely not in `final_plan.csv` or `sales_data.csv`. We should ensure the `SegmentationAgent`'s output is saved to a file (e.g., `data/segmentation.csv`) and accessible to the `AnalystAgent`.
- **System Prompt**: Update the prompt to tell the agent where to look for segmentation info (e.g., "Join with segmentation data" or "Infer from volatility").

## 4. Test: `explain_policy_promo_uplift` (FAIL)
**Issue**: The agent hallucinated a value ("1567.46") instead of using the correct policy ("0.5" or "50%"). This happened because the `AnalystAgent` does not have access to the `PolicyAgent`'s tools or the `config.yaml`.
**Suggestion**:
- **Tool Integration**: Give the `AnalystAgent` access to the `get_policy_config` tool (via MCP) so it can look up ground truth policy values.
- **Context Injection**: Alternatively, inject the key policy constraints into the `AnalystAgent`'s system prompt at startup.

## 5. Test: `list_top_cuts` (FAIL)
**Issue**: The agent stated "There were no cuts", but the logs show cuts were made.
**Suggestion**:
- **Data Engineering**: Ensure the `Negotiation_Log` or a `Cut_Amount` column is explicitly preserved in `final_plan.csv`. If the column is empty or missing, the agent cannot see the cuts.
- **System Prompt**: explicitly guide the agent to calculate `Cut = Plan - Constrained_Plan` if a direct "Cut" column doesn't exist.
