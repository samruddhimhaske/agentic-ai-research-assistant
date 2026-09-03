"""
tools/tool_registry.py - Tool Registry
========================================
The Tool Registry is a central directory of ALL available tools.

Think of it like a toolbox:
  - The agent looks in this registry to find available tools
  - It picks the right tool for the job
  - It calls the tool and gets a result

WHY USE A REGISTRY?
  Instead of the agent knowing about each tool individually,
  the registry lets you add new tools in ONE place and the
  agent automatically knows about them.

  Want to add a new tool later? Just:
  1. Create the tool file in /tools/
  2. Register it here — that's it!
"""

from tools.calculator import CalculatorTool
from tools.search import WikipediaSearchTool
from tools.datetime_tool import DateTimeTool
from tools.summarizer import TextSummarizerTool


class ToolRegistry:
    """
    Central registry for all agent tools.
    
    The executor agent uses this to find and run tools.
    
    Usage:
        registry = ToolRegistry()
        
        # List all available tools
        tools = registry.get_all_tools()
        
        # Run a specific tool
        result = registry.run_tool("Calculator", "2 + 2")
        
        # Get descriptions for the LLM to choose from
        descriptions = registry.get_tool_descriptions()
    """

    def __init__(self):
        """
        Initialize the registry with all available tools.
        Each tool is stored by its name for easy lookup.
        """
        # Create instances of all tools
        calculator = CalculatorTool()
        search = WikipediaSearchTool()
        datetime_tool = DateTimeTool()
        summarizer = TextSummarizerTool()

        # Store tools in a dictionary: {tool_name: tool_instance}
        # The key is the tool's name — this is what the agent uses to select a tool
        self._tools = {
            "Calculator": calculator,
            "WikipediaSearch": search,
            "DateTime": datetime_tool,
            "TextSummarizer": summarizer,
        }

    def get_tool(self, tool_name: str):
        """
        Get a tool instance by name.
        
        Args:
            tool_name: The name of the tool (must match a registered tool)
            
        Returns:
            The tool instance, or None if not found
        """
        return self._tools.get(tool_name)

    def run_tool(self, tool_name: str, tool_input: str) -> str:
        """
        Find and run a tool by name.
        
        Args:
            tool_name: Which tool to use
            tool_input: What to pass to the tool
            
        Returns:
            The tool's output as a string
        """
        tool = self.get_tool(tool_name)

        if not tool:
            available = ", ".join(self._tools.keys())
            return (
                f"Tool '{tool_name}' not found. "
                f"Available tools: {available}"
            )

        try:
            # Call the tool's run() method with the input
            result = tool.run(tool_input)
            return result
        except Exception as e:
            return f"Error running {tool_name}: {str(e)}"

    def get_all_tools(self) -> list:
        """Return a list of all tool instances."""
        return list(self._tools.values())

    def get_tool_names(self) -> list[str]:
        """Return a list of all tool names."""
        return list(self._tools.keys())

    def get_tool_descriptions(self) -> str:
        """
        Return a formatted string describing all tools.
        
        This is passed to the LLM so it knows what tools are available
        and can choose the most appropriate one.
        
        Example output:
            - Calculator: Performs safe mathematical calculations...
            - WikipediaSearch: Searches Wikipedia for information...
            - DateTime: Provides current date and time...
            - TextSummarizer: Summarizes long text...
        """
        descriptions = []
        for name, tool in self._tools.items():
            descriptions.append(f"- {name}: {tool.description}")
        return "\n".join(descriptions)

    def get_tools_metadata(self) -> list[dict]:
        """
        Return metadata for all tools as a list of dictionaries.
        Used for the API response and documentation.
        """
        metadata = []
        for name, tool in self._tools.items():
            if hasattr(tool, 'get_tool_info'):
                metadata.append(tool.get_tool_info())
            else:
                metadata.append({
                    "name": name,
                    "description": tool.description
                })
        return metadata

    def register_tool(self, tool_instance) -> None:
        """
        Add a new tool to the registry dynamically.
        
        This is how you'd add a new tool at runtime.
        The tool must have a 'name' attribute and a 'run' method.
        
        Args:
            tool_instance: An instantiated tool object
        """
        if not hasattr(tool_instance, 'name'):
            raise ValueError("Tool must have a 'name' attribute")
        if not hasattr(tool_instance, 'run'):
            raise ValueError("Tool must have a 'run' method")

        self._tools[tool_instance.name] = tool_instance


# Create a single global registry instance
# Import this in other files: from tools.tool_registry import tool_registry
tool_registry = ToolRegistry()
