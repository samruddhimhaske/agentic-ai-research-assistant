"""
agent/planner.py - Planner Agent
==================================
The Planner is the FIRST step in the agent workflow.

RESPONSIBILITY:
  Take the user's raw question and break it down into a clear,
  step-by-step research plan.

WHY IS PLANNING IMPORTANT?
  Without a plan, the agent would just blindly search for things
  and hope for the best. A good plan:
  - Clarifies what the user actually wants
  - Identifies which tools will be needed
  - Creates an ordered sequence of steps
  - Makes the agent's thinking transparent and explainable

EXAMPLE:
  User query: "What is quantum computing and how fast is a quantum computer?"

  Planner output:
  Step 1: Search Wikipedia for "quantum computing" basics
  Step 2: Search Wikipedia for "quantum computer speed performance"  
  Step 3: Summarize the gathered information
  Step 4: Compile final structured answer

This is the classic "Think before you act" principle in AI systems.
"""

import time
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from models.schemas import PlanStep, AgentStep
from config import settings
from services.llm_service import get_llm


class PlannerAgent:
    """
    Creates a step-by-step research plan from a user query.
    
    The planner uses an LLM (GPT) to understand the user's intent
    and decompose it into actionable steps.
    
    Usage:
        planner = PlannerAgent()
        plan, step_status = planner.create_plan("What is quantum computing?")
    """

    def __init__(self):
        """Initialize the planner with the configured LLM."""
        self.llm = get_llm(temperature=0.3)

        # The system prompt tells the LLM what role it plays
        self.system_prompt = """You are a Research Planning Agent. 
Your job is to analyze a user's question and create a clear, step-by-step research plan.

Available tools you can assign to steps:
- WikipediaSearch: Search for information on any topic
- Calculator: Perform mathematical calculations
- DateTime: Get current date and time information
- TextSummarizer: Summarize long pieces of text

Rules:
1. Break the query into 2-4 clear, specific steps
2. Each step should do ONE thing
3. Assign the most appropriate tool to each step
4. Keep step descriptions short and action-oriented
5. If the query is simple (e.g., just a math problem), 1-2 steps is fine

Respond ONLY with a numbered list in this exact format:
Step 1: [action description] | Tool: [ToolName or None]
Step 2: [action description] | Tool: [ToolName or None]
...

Example for "What is the speed of light?":
Step 1: Search Wikipedia for speed of light definition and value | Tool: WikipediaSearch
Step 2: Summarize the key findings | Tool: TextSummarizer"""

    def create_plan(self, query: str) -> tuple[list[PlanStep], AgentStep]:
        """
        Analyze the user query and create a research plan.
        
        Args:
            query: The user's question
            
        Returns:
            A tuple of:
            - list[PlanStep]: The ordered research steps
            - AgentStep: Status info for the UI dashboard
        """
        start_time = time.time()

        # Create the workflow step object for UI tracking
        agent_step = AgentStep(
            step_number=1,
            step_name="Understanding & Planning",
            status="in_progress",
            summary="Analyzing your question and creating a research plan..."
        )

        try:
            # Ask the LLM to create a plan
            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=f"Create a research plan for this query:\n\n{query}")
            ]

            response = self.llm.invoke(messages)
            plan_text = response.content.strip()

            # Parse the LLM's response into PlanStep objects
            plan_steps = self._parse_plan(plan_text)

            # If parsing fails or returns empty, create a default plan
            if not plan_steps:
                plan_steps = self._create_default_plan(query)

            # Update step status to completed
            duration = round(time.time() - start_time, 2)
            agent_step.status = "completed"
            agent_step.summary = f"Created a {len(plan_steps)}-step research plan for your query."
            agent_step.duration = f"{duration}s"

            return plan_steps, agent_step

        except Exception as e:
            # If the LLM call fails, fall back to a default plan
            duration = round(time.time() - start_time, 2)
            agent_step.status = "completed"
            agent_step.summary = "Created a default research plan."
            agent_step.duration = f"{duration}s"

            fallback_plan = self._create_default_plan(query)
            return fallback_plan, agent_step

    def _parse_plan(self, plan_text: str) -> list[PlanStep]:
        """
        Parse the LLM's text response into structured PlanStep objects.
        
        Expected input format:
        "Step 1: Search Wikipedia for topic | Tool: WikipediaSearch
         Step 2: Summarize findings | Tool: TextSummarizer"
        
        Args:
            plan_text: Raw text from the LLM
            
        Returns:
            List of PlanStep objects
        """
        steps = []
        lines = plan_text.strip().split("\n")

        for line in lines:
            line = line.strip()
            # Skip empty lines
            if not line:
                continue
            # Only process lines that start with "Step"
            if not line.lower().startswith("step"):
                continue

            try:
                # Remove "Step N:" prefix
                # "Step 1: Search Wikipedia | Tool: WikipediaSearch"
                # → "Search Wikipedia | Tool: WikipediaSearch"
                colon_idx = line.index(":")
                content = line[colon_idx + 1:].strip()

                # Split on " | Tool: " to separate action and tool
                if "| Tool:" in content:
                    parts = content.split("| Tool:")
                    description = parts[0].strip()
                    tool_name = parts[1].strip() if len(parts) > 1 else None
                    # Clean up "None" string
                    if tool_name and tool_name.lower() in ("none", "n/a", ""):
                        tool_name = None
                else:
                    description = content
                    tool_name = None

                # Determine step number from position in list
                step_number = len(steps) + 1

                steps.append(PlanStep(
                    step_number=step_number,
                    description=description,
                    tool_suggested=tool_name,
                    completed=False
                ))

            except (ValueError, IndexError):
                # If parsing this line fails, skip it
                continue

        return steps

    def _create_default_plan(self, query: str) -> list[PlanStep]:
        """
        Create a sensible default plan when LLM planning fails.
        
        Analyzes keywords in the query to guess the right tools.
        
        Args:
            query: The user's question
            
        Returns:
            A basic but functional research plan
        """
        query_lower = query.lower()
        steps = []

        # Check if it's a math question
        math_keywords = ["+", "-", "*", "/", "calculate", "compute", "math",
                         "percent", "%", "square root", "sqrt"]
        is_math = any(kw in query_lower for kw in math_keywords)

        # Check if it's a time/date question
        time_keywords = ["date", "time", "today", "day", "week", "month", "year", "current"]
        is_time = any(kw in query_lower for kw in time_keywords)

        if is_math:
            steps.append(PlanStep(
                step_number=1,
                description=f"Calculate the mathematical expression in the query",
                tool_suggested="Calculator"
            ))
        elif is_time:
            steps.append(PlanStep(
                step_number=1,
                description="Get current date and time information",
                tool_suggested="DateTime"
            ))
        else:
            # Default: search Wikipedia
            steps.append(PlanStep(
                step_number=1,
                description=f"Search Wikipedia for information about the topic",
                tool_suggested="WikipediaSearch"
            ))
            steps.append(PlanStep(
                step_number=2,
                description="Summarize the gathered information",
                tool_suggested="TextSummarizer"
            ))

        return steps
