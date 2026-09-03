"""
agent/executor.py - Executor Agent
=====================================
The Executor is the SECOND step in the agent workflow.

RESPONSIBILITY:
  Take the plan from the Planner and actually EXECUTE it.
  For each step in the plan:
  1. Look at what tool is suggested
  2. Generate the right input for that tool
  3. Run the tool
  4. Collect the result (observation)
"""

import time
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from models.schemas import PlanStep, ToolUsage, AgentStep
from tools.tool_registry import tool_registry
from config import settings
from services.llm_service import get_llm


class ExecutorAgent:
    """
    Executes the research plan by running tools and collecting observations.
    """

    def __init__(self):
        """Initialize the executor with the configured LLM."""
        self.llm = get_llm(temperature=0.1)

        self.tool_input_prompt = """You are a Tool Input Generator.
Given a research plan step and the original user query, generate the precise input 
to pass to the specified tool.

Rules:
- For WikipediaSearch: Return ONLY the core topic (e.g., "machine learning", "quantum computing")
- For Calculator: Return ONLY the math expression (e.g., "sqrt(144) + 2**8")
- For DateTime: Return ONLY what time info is needed (e.g., "current date and time")
- For TextSummarizer: Handled separately, do not generate input for this

Respond with ONLY the tool input — no explanation, no quotes, no extra text."""

    # ──────────────────────────────────────────────────────────────
    # PUBLIC METHOD
    # ──────────────────────────────────────────────────────────────

    def execute_plan(
        self,
        plan: list[PlanStep],
        query: str
    ) -> tuple[list[ToolUsage], list[str], AgentStep]:
        """
        Execute each step in the plan and collect observations.

        Args:
            plan: List of PlanStep objects from the Planner
            query: The original user question

        Returns:
            (tools_used, observations, agent_step)
        """
        start_time = time.time()
        tools_used: list[ToolUsage] = []
        observations: list[str] = []

        agent_step = AgentStep(
            step_number=2,
            step_name="Selecting & Executing Tools",
            status="in_progress",
            summary="Selecting the right tools and gathering information..."
        )

        # Text accumulated from search results (fed into summarizer)
        gathered_text = ""

        # Cleaned query — question words removed for better tool input
        clean_query = self._simplify_query(query)

        for plan_step in plan:
            tool_name = plan_step.tool_suggested

            # Skip steps with no tool assigned
            if not tool_name or tool_name.lower() == "none":
                plan_step.completed = True
                continue

            try:
                # ── Generate tool input ──
                if tool_name == "TextSummarizer":
                    if gathered_text:
                        tool_input = gathered_text
                    else:
                        plan_step.completed = True
                        continue
                else:
                    tool_input = self._generate_tool_input(
                        plan_step.description,
                        tool_name,
                        clean_query
                    )

                # ── Run the tool ──
                tool_output = tool_registry.run_tool(tool_name, tool_input)

                # ── Record the result ──
                tool_usage = ToolUsage(
                    tool_name=tool_name,
                    tool_input=tool_input,
                    tool_output=tool_output,
                    success=not tool_output.startswith("Error")
                )
                tools_used.append(tool_usage)
                observations.append(f"[{tool_name}]: {tool_output}")

                # Accumulate Wikipedia text for potential summarization
                if tool_name == "WikipediaSearch" and tool_usage.success:
                    gathered_text += "\n\n" + tool_output

                plan_step.completed = True

            except Exception as e:
                error_msg = f"Tool '{tool_name}' failed: {str(e)}"
                tools_used.append(ToolUsage(
                    tool_name=tool_name,
                    tool_input=plan_step.description,
                    tool_output=error_msg,
                    success=False
                ))
                observations.append(f"[{tool_name} ERROR]: {error_msg}")
                plan_step.completed = True

        # ── Update step status ──
        duration = round(time.time() - start_time, 2)
        agent_step.status = "completed"
        agent_step.summary = (
            f"Used {len(tools_used)} tool(s). "
            f"Gathered {len(observations)} observation(s)."
        )
        agent_step.duration = f"{duration}s"

        return tools_used, observations, agent_step

    # ──────────────────────────────────────────────────────────────
    # PRIVATE HELPERS
    # ──────────────────────────────────────────────────────────────

    def _simplify_query(self, query: str) -> str:
        """
        Strip question words from a query to get clean search keywords.

        'WHAT IS AGENTIC AI'        → 'agentic AI'
        'Tell me about black holes' → 'black holes'
        'quantum computing'         → 'quantum computing'  (unchanged)
        """
        q = query.strip()
        lower = q.lower()

        prefixes = [
            "what is ", "what are ", "what was ", "what were ",
            "who is ", "who was ", "who are ",
            "tell me about ", "explain ", "describe ",
            "how does ", "how do ", "how is ",
            "give me information about ", "search for ",
            "find information about ", "look up ",
        ]
        for p in prefixes:
            if lower.startswith(p):
                q = q[len(p):].strip()
                break

        return q

    def _generate_tool_input(
        self,
        step_description: str,
        tool_name: str,
        clean_query: str
    ) -> str:
        """
        Use the LLM to generate precise input for a tool.

        Args:
            step_description: What this plan step is trying to do
            tool_name: Which tool will be called
            clean_query: User query with question words removed

        Returns:
            The input string to pass to the tool
        """
        try:
            messages = [
                SystemMessage(content=self.tool_input_prompt),
                HumanMessage(content=(
                    f"User query: {clean_query}\n"
                    f"Plan step: {step_description}\n"
                    f"Tool: {tool_name}\n\n"
                    f"Generate the exact input for {tool_name}:"
                ))
            ]

            response = self.llm.invoke(messages)
            tool_input = response.content.strip()

            # Remove surrounding quotes if present
            tool_input = tool_input.strip('"\'')

            return tool_input if tool_input else clean_query

        except Exception:
            # Fallback: use the cleaned query directly
            return clean_query
