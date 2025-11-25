# AnalystAgent Evaluations

This directory contains the evaluation suite for the AnalystAgent.

## Files
- `test_chat_analyst.yaml`: The test specifications (Q&A pairs and expectations).
- `eval_runner.py`: The script that runs the tests.
- `llm_judge.py`: The LLM-as-a-Judge implementation.
- `eval_report.md`: Human-readable report (generated).
- `eval_report.json`: Machine-readable report (generated).

## How to Run
From the project root directory:

```bash
python -m evals.eval_runner
```

This will:
1. Run a full planning cycle (Orchestrator) to generate fresh data.
2. Run the tests defined in `test_chat_analyst.yaml`.
3. Generate `eval_report.md` and `eval_report.json`.

## Adding Tests
Edit `test_chat_analyst.yaml` to add new test cases. Follow the existing format.
