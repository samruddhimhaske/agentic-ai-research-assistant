"""
agent/response_generator.py - Response Generator Agent
=========================================================
The Response Generator is the FINAL step in the agent workflow.

RESPONSIBILITY:
  Take everything gathered (plan, observations, reflection) and
  write a clear, structured, well-formatted final answer for the user.

WHY IS A SEPARATE RESPONSE GENERATOR NEEDED?
  The raw tool outputs are messy and unformatted:
  - Wikipedia output is a wall of text
  - Calculator output is just a number
  - DateTime output is a list of facts
  
  The Response Generator transforms all of this into a polished,
  user-friendly answer with:
  - A clear heading
  - Organized sections
  - Bullet points where appropriate
  - A concise summary at the end
  - Proper Markdown formatting

MARKDOWN OUTPUT:
  The final answer uses Markdown formatting because:
  - The frontend renders Markdown as rich HTML
  - It's readable even as plain text
  - Headers, bullets, and bold text make information scannable

This is the "write the report" step after all the research is done.
"""

import time
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from models.schemas import AgentStep, PlanStep, ToolUsage
from config import settings
from services.llm_service import get_llm


class ResponseGeneratorAgent:
    """
    Generates the final structured answer from gathered research.
    
    Takes all the raw information from the executor and reflection agent
    and crafts a polished, well-structured response.
    
    Usage:
        generator = ResponseGeneratorAgent()
        answer, step_status = generator.generate(
            query="What is quantum computing?",
            plan=plan_steps,
            observations=observations,
            reflection="Information is complete.",
            tools_used=tools_used
        )
    """

    def __init__(self):
        """Initialize the response generator with the configured LLM."""
        self.llm = get_llm(temperature=0.5)

        self.system_prompt = """You are a Research Response Writer.
Your job is to write a clear, well-structured, and informative answer based on gathered research.

Formatting rules:
1. Start with a # Main Heading that answers the query directly
2. Use ## Sub-headings to organize different aspects
3. Use bullet points (- item) for lists of facts or features
4. Use **bold** for important terms or key points
5. End with a ## Summary section (3-5 sentences maximum)
6. Write in a clear, beginner-friendly tone
7. If tools were used, briefly mention what sources were consulted
8. Keep the total response under 600 words unless the topic genuinely requires more

Important:
- Base your answer ONLY on the provided observations and your knowledge
- If information is incomplete, honestly note what couldn't be found
- Do NOT include technical agent details (like tool names as code or raw outputs)
- Write as if explaining to a curious student or professional
- Make the response genuinely useful and informative"""

    def generate(
        self,
        query: str,
        plan: list[PlanStep],
        observations: list[str],
        reflection: str,
        tools_used: list[ToolUsage]
    ) -> tuple[str, AgentStep]:
        """
        Generate the final structured response.
        
        Args:
            query: The user's original question
            plan: The research plan that was followed
            observations: All tool outputs collected
            reflection: The reflection agent's assessment
            tools_used: Details of all tool calls made
            
        Returns:
            A tuple of:
            - str: The final answer in Markdown format
            - AgentStep: Status info for the UI dashboard
        """
        start_time = time.time()

        # Create the workflow step status for the UI
        agent_step = AgentStep(
            step_number=4,
            step_name="Generating Final Answer",
            status="in_progress",
            summary="Writing your structured final answer..."
        )

        try:
            # Build the context for the LLM
            context = self._build_context(
                query, plan, observations, reflection, tools_used
            )

            # Ask the LLM to write the final answer
            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=context)
            ]

            response = self.llm.invoke(messages)
            final_answer = response.content.strip()

            # Validate the response has proper structure
            if not final_answer or len(final_answer) < 50:
                final_answer = self._generate_fallback_answer(query, observations)

            # Update step status
            duration = round(time.time() - start_time, 2)
            agent_step.status = "completed"
            agent_step.summary = "Final answer generated successfully."
            agent_step.duration = f"{duration}s"

            return final_answer, agent_step

        except Exception as e:
            # If LLM call fails, generate a basic answer from observations
            duration = round(time.time() - start_time, 2)
            agent_step.status = "completed"
            agent_step.summary = "Answer generated using available information."
            agent_step.duration = f"{duration}s"

            fallback = self._generate_fallback_answer(query, observations)
            return fallback, agent_step

    def _build_context(
        self,
        query: str,
        plan: list[PlanStep],
        observations: list[str],
        reflection: str,
        tools_used: list[ToolUsage]
    ) -> str:
        """
        Build a well-structured prompt context for the LLM.
        
        Combines all the gathered information into a single
        structured prompt that the LLM can use to write the answer.
        """
        # Format the research plan
        plan_text = "\n".join(
            f"  {step.step_number}. {step.description} ({'✓' if step.completed else '○'})"
            for step in plan
        ) if plan else "  No formal plan created."

        # Format tool usage summary
        tools_text = "\n".join(
            f"  - {t.tool_name}: {'Success' if t.success else 'Failed'}"
            for t in tools_used
        ) if tools_used else "  No tools used."

        # Format observations — truncate to avoid token limit issues
        obs_text = self._truncate_observations(observations)

        return (
            f"USER QUERY:\n{query}\n\n"
            f"RESEARCH PLAN FOLLOWED:\n{plan_text}\n\n"
            f"TOOLS USED:\n{tools_text}\n\n"
            f"GATHERED INFORMATION:\n{obs_text}\n\n"
            f"QUALITY ASSESSMENT:\n{reflection}\n\n"
            f"Now write a comprehensive, well-structured answer to: {query}"
        )

    def _truncate_observations(
        self,
        observations: list[str],
        max_total_chars: int = 3000
    ) -> str:
        """
        Format observations while staying within token limits.
        
        Args:
            observations: List of observation strings
            max_total_chars: Max total characters across all observations
            
        Returns:
            Formatted observations string
        """
        if not observations:
            return "  No observations gathered."

        formatted = []
        total_chars = 0

        for i, obs in enumerate(observations, 1):
            # Truncate very long individual observations
            if len(obs) > 1500:
                obs = obs[:1500] + "... [truncated]"

            if total_chars + len(obs) > max_total_chars:
                remaining = len(observations) - i + 1
                formatted.append(f"  [{remaining} more observations truncated]")
                break

            formatted.append(f"  [{i}] {obs}")
            total_chars += len(obs)

        return "\n\n".join(formatted)

    def _generate_fallback_answer(
        self,
        query: str,
        observations: list[str]
    ) -> str:
        """
        Generate a basic answer when the LLM call fails.
        Uses the raw observations formatted cleanly.
        
        Args:
            query: The user's question
            observations: Available tool outputs
            
        Returns:
            A basic but readable answer
        """
        answer_parts = [f"# Research Results\n\n**Query:** {query}\n"]

        if observations:
            answer_parts.append("## Gathered Information\n")
            for i, obs in enumerate(observations, 1):
                # Remove tool prefix like "[WikipediaSearch]: "
                clean_obs = obs
                if "]: " in obs:
                    clean_obs = obs.split("]: ", 1)[1]
                answer_parts.append(f"{clean_obs}\n")
        else:
            answer_parts.append(
                "## Note\n\nI was unable to gather specific information "
                "for this query at this time. Please try rephrasing your "
                "question or check your API configuration.\n"
            )

        answer_parts.append(
            "\n## Summary\n\n"
            f"The above information was gathered in response to your query about: "
            f"*{query}*. "
            "Please review the details above for the most relevant findings."
        )

        return "\n".join(answer_parts)
