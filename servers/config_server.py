from mcp.server.fastmcp import FastMCP
import yaml
import os

# Initialize FastMCP server
mcp = FastMCP("ConfigServer")

def load_config(config_path="config.yaml"):
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        return {}
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def get_policy_config(key: str) -> str:
    """
    Retrieves a specific value from the policy configuration.
    Args:
        key: The configuration key to look up (e.g., 'priorities', 'constraints').
    Returns:
        The value as a string, or 'Not found'.
    """
    config = load_config()
    
    # Flatten config for easier lookup or just return top-level sections
    if key in config:
        return str(config[key])
    
    # Search in sub-dictionaries
    for section in config.values():
        if isinstance(section, dict) and key in section:
            return str(section[key])
            
    return "Not found"

if __name__ == "__main__":
    # Run the server
    mcp.run()
