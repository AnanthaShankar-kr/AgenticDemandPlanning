from agents.base_agent import BaseAgent
import asyncio
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class PolicyAndGuardrailAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="PolicyAgent")
        
        # We no longer load config directly.
        # We register a tool that calls the MCP server.
        self.register_tool(self.get_policy_value)
        
        self.set_system_instruction(
            """
            You are the Policy and Guardrails Agent.
            Your role is to provide authoritative answers about business priorities and constraints.
            
            **CRITICAL:** You have access to the configuration via the 'get_policy_value' tool.
            You MUST use this tool to retrieve policy information before answering.
            
            **How to use the tool:**
            - For questions about constraints (limits, uplifts, capacity): call get_policy_value("constraints")
            - For questions about priorities: call get_policy_value("priorities")
            - For questions about strategic SKUs: call get_policy_value("strategic_skus")
            
            **Examples:**
            - "What is the max promo uplift?" → call get_policy_value("constraints") → look for max_promo_uplift
            - "What are the strategic SKUs?" → call get_policy_value("strategic_skus")
            - "What is the capacity limit?" → call get_policy_value("constraints") → look for capacity_limit_total
            
            **Important:**
            - Always call the tool FIRST before answering
            - If a value is not found in the returned data, state that clearly
            - Do not make up or assume policy values
            """
        )

    async def _call_mcp_tool(self, key: str) -> str:
        # Define server parameters
        server_params = StdioServerParameters(
            command=sys.executable, # Use current python
            args=["servers/config_server.py"], # Path to server script
            env=None
        )
        
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize
                await session.initialize()
                
                # Call the tool
                result = await session.call_tool("get_policy_config", arguments={"key": key})
                
                # Result is a list of content, we want the text
                if result.content:
                    return result.content[0].text
                return "No content returned."

    def get_policy_value(self, key: str) -> str:
        """
        Retrieves a specific value from the policy configuration via MCP.
        Args:
            key: The configuration key to look up.
        """
        try:
            # Check if we are already in an event loop
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None

            if loop and loop.is_running():
                # We are in a loop (e.g. FastAPI). Run async code in a separate thread.
                from concurrent.futures import ThreadPoolExecutor
                with ThreadPoolExecutor() as pool:
                    future = pool.submit(asyncio.run, self._call_mcp_tool(key))
                    return future.result()
            else:
                # No loop running, use asyncio.run
                return asyncio.run(self._call_mcp_tool(key))
        except Exception as e:
            return f"Error calling MCP server: {e}"

    def run(self, prompt: str = "What are the current strategic priorities?") -> dict:
        """
        Answers a query about policy and returns the context.
        """
        response_text = super().run(prompt)
        
        # For the context, we'll just fetch the main sections to pass downstream
        # This is a bit inefficient (spinning up server again), but fine for PoC
        priorities = self.get_policy_value("priorities")
        constraints = self.get_policy_value("constraints")
        strategic_skus = self.get_policy_value("strategic_skus")
        
        # Parse strings back to dicts/lists if possible, or just pass strings
        # For PoC, let's try to eval safely if they look like python structures
        context = {}
        try:
            context['priorities'] = eval(priorities) if priorities.startswith("{") else priorities
            context['constraints'] = eval(constraints) if constraints.startswith("{") else constraints
            context['strategic_skus'] = eval(strategic_skus) if strategic_skus.startswith("[") else strategic_skus
        except:
            context = {'raw_policy': response_text}

        return {
            "explanation": response_text,
            "policy_context": context
        }

if __name__ == "__main__":
    agent = PolicyAndGuardrailAgent()
    print(agent.run("What is the max allowed promo uplift?"))
