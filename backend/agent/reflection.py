"""
agent/reflection.py - Reflection Agent
=========================================
The Reflection Agent is the THIRD step in the agent workflow.

RESPONSIBILITY:
  Review everything collected so far and decide:
  1. Is the information complete enough to answer the user's question?
  2. Are there any gaps or missing details?
  3. Should we do more research, or is this sufficient?
  4. What is the quality of what we've gathered?

WHY IS REFLECTION IMPORTANT?
  Without reflection, an agent might give an incomplete answer
  and not even realize it. Reflection adds "self-awareness":
  
  - "I searched for quantum computing but didn't find anything 
     about its speed. The user asked about speed too. I should note this."
     
  - "The math calculation succeeded. The answer is complete."
  
  - "The search returned useful information. Ready to write the final answer."

This mirrors how a good researcher works:
  After gathering sources, they step back and ask:
  "Do I have enough to write a complete, accurate answer?"

IN AGENTIC AI:
  Reflection is what separates simple chatbots from true agents.
  It's the "metacognition" — thinking about your own thinking.
"""

import time
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from models.schemas import AgentStep
from config import settings
from services.llm_service import get_llm


class ReflectionAgent:
    """
    Reviews gathered information and assesses completeness.
    
    The reflection agent acts like a quality checker — it reads the
    observations and decides if the agent is ready to write the final answer.
    
    Usage:
        reflector = ReflectionAgent()
        reflection_text, step_status = reflector.reflect(
            query="What is quantum computing?",
            observations=["[WikipediaSearch]: Quantum computing is..."],
            tools_used=["WikipediaSearch"]
        )
    """

    def __init__(self):
        """Initialize the reflection agent with the configured LLM."""
        self.llm = get_llm(temperature=0.2)

        self.system_prompt = """You are a Research Quality Reviewer Agent.
Your job is to review the gathered research and assess whether it fully answers the user's question.

You will receive:
1. The original user query
2. The observations/results gathered by the research tools

Your task:
- Determine if the gathered information fully answers the query
- Identify any gaps or missing information
- Rate the completeness (Complete / Mostly Complete / Incomplete)
- Write 2-3 sentences summarizing your assessment

Keep your response concise (2-4 sentences max).
Be honest but constructive — focus on what WAS gathered, then note any gaps.
Do NOT include raw tool output or technical details in your reflection.
Write in a professional, readable tone."""

    def reflect(
        self,
        query: str,
        observations: list[str],
        tools_used: list[str]
    ) -> tuple[str, AgentStep]:
        """
        Reflect on the gathered information and assess completeness.
        
        Args:
            query: The original user question
            observations: List of tool outputs gathered by the executor
            tools_used: Names of tools that were used
            
        Returns:
            A tuple of:
            - str: The reflection text (assessment of completeness)
            - AgentStep: Status info for the UI dashboard
        """
        start_time = time.time()

        # Create the workflow step status for the UI
        agent_step = AgentStep(
            step_number=3,
            step_name="Reviewing & Reflecting",
            status="in_progress",
            summary="Reviewing the gathered information for completeness..."
        )

        # Handle the case where no observations were gathered
        if not observations:
            duration = round(time.time() - start_time, 2)
            agent_step.status = "completed"
            agent_step.summary = "No tool observations available — will generate answer from knowledge."
            agent_step.duration = f"{duration}s"
            return (
                "No external information was gathered. "
                "The response will be based on general knowledge.",
                agent_step
            )

        try:
            # Format observations for the LLM to review
            # Truncate each observation to avoid hitting token limits
            formatted_obs = self._format_observations(observations)
            tools_list = ", ".join(set(tools_used)) if tools_used else "none"

            # Ask the LLM to assess the gathered information
            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=(
                    f"User Query: {query}\n\n"
                    f"Tools Used: {tools_list}\n\n"
                    f"Gathered Information:\n{formatted_obs}\n\n"
                    f"Assess whether this information is sufficient to answer the query."
                ))
            ]

            response = self.llm.invoke(messages)
            reflection_text = response.content.strip()

            # Update step status
            duration = round(time.time() - start_time, 2)
            agent_step.status = "completed"
            agent_step.summary = "Information reviewed. Quality assessment complete."
            agent_step.duration = f"{duration}s"

            return reflection_text, agent_step

        except Exception as e:
            # Fallback reflection if LLM call fails
            duration = round(time.time() - start_time, 2)
            agent_step.status = "completed"
            agent_step.summary = "Review completed with default assessment."
            agent_step.duration = f"{duration}s"

            fallback = self._generate_fallback_reflection(query, observations, tools_used)
            return fallback, agent_step

    def _format_observations(self, observations: list[str], max_chars: int = 2000) -> str:
        """
        Format and truncate observations for the LLM.
        
        We limit the total character count to avoid using too many tokens,
        which would make the API call expensive.
        
        Args:
            observations: List of raw observation strings
            max_chars: Maximum total characters to include
            
        Returns:
            Formatted string with all observations
        """
        formatted = []
        total_chars = 0

        for i, obs in enumerate(observations, 1):
            # Truncate individual observations that are very long
            if len(obs) > 800:
                obs = obs[:800] + "... [truncated]"

            # Check if adding this observation would exceed our limit
            if total_chars + len(obs) > max_chars:
                formatted.append(f"[{i}] [Additional observations truncated to save space]")
                break

            formatted.append(f"[{i}] {obs}")
            total_chars += len(obs)

        return "\n\n".join(formatted)

    def _generate_fallback_reflection(
        self,
        query: str,
        observations: list[str],
        tools_used: list[str]
    ) -> str:
        """
        Generate a basic reflection without using the LLM.
        Used as a fallback when the API call fails.
        
        Args:
            query: The user's question
            observations: Tool outputs
            tools_used: Tools that were used
            
        Returns:
            A simple assessment string
        """
        num_observations = len(observations)
        tools_str = ", ".join(set(tools_used)) if tools_used else "no tools"
        has_errors = any("Error" in obs or "error" in obs for obs in observations)

        if has_errors:
            return (
                f"Research gathered {num_observations} observation(s) using {tools_str}. "
                "Some tools encountered errors, but partial information was collected. "
                "The response will be based on available data."
            )
        elif num_observations > 0:
            return (
                f"Research complete. Gathered {num_observations} piece(s) of information "
                f"using {tools_str}. The collected data appears sufficient to answer the query."
            )
        else:
            return (
                "No external data was gathered. "
                "The response will be generated from the model's general knowledge."
            )
