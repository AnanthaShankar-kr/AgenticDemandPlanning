import json
import os
import sys

# Add parent directory to path to import agents
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.base_agent import BaseAgent

class LLMJudge(BaseAgent):
    def __init__(self):
        super().__init__(name="LLMJudge")
        self.set_system_instruction(
            """
            You are an impartial LLM Judge.
            Your task is to evaluate the response of an AI Agent against a set of expectations.
            
            You will be given:
            1. The User Input (Question).
            2. The Agent's Answer.
            3. A set of Expectations (must mention, should mention, must not mention).
            4. Optional Ground Truth context.
            
            You must output your judgment in strict JSON format:
            {
                "result": "PASS" or "FAIL",
                "reason": "A concise explanation of why it passed or failed."
            }
            
            Criteria for PASS:
            - The answer is factually correct based on the Ground Truth (if provided).
            - The answer addresses the User Input.
            - ALL 'must_mention' phrases/concepts are present or clearly implied.
            - NONE of the 'must_not_mention' phrases/concepts are present.
            
            Criteria for FAIL:
            - The answer is factually incorrect.
            - The answer misses a 'must_mention' concept.
            - The answer includes a 'must_not_mention' concept (hallucination).
            - The answer is irrelevant to the question.
            """
        )

    def judge_response(self, test_spec, user_input, answer, ground_truth=None) -> dict:
        prompt = f"""
        **Test ID**: {test_spec.get('id')}
        **Description**: {test_spec.get('description')}
        
        **User Input**: "{user_input}"
        
        **Agent Answer**: 
        "{answer}"
        
        **Expectations**:
        - Type: {test_spec['expectations'].get('type')}
        - Must Mention: {test_spec['expectations'].get('must_mention', [])}
        - Should Mention: {test_spec['expectations'].get('should_mention', [])}
        - Must NOT Mention: {test_spec['expectations'].get('must_not_mention', [])}
        
        **Ground Truth**:
        {json.dumps(ground_truth, indent=2) if ground_truth else "None provided."}
        
        Evaluate the answer now. Return ONLY the JSON.
        """
        
        response_text = self.run(prompt)
        
        # Clean up response to ensure it's valid JSON
        response_text = response_text.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
            
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            return {
                "result": "FAIL",
                "reason": f"Judge failed to produce valid JSON. Raw output: {response_text}"
            }

if __name__ == "__main__":
    # Test the judge
    judge = LLMJudge()
    res = judge.judge_response(
        {"id": "test", "description": "test", "expectations": {"must_mention": ["foo"]}},
        "Say foo",
        "This is foo",
        None
    )
    print(res)
