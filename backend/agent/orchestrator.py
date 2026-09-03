"""
agent/orchestrator.py - Agent Orchestrator
============================================
The Orchestrator is the CONDUCTOR of the entire agent workflow.

RESPONSIBILITY:
  Coordinate all 4 agent components in the correct order:
  
  1. PlannerAgent     → Understand the query, create a plan
  2. ExecutorAgent    → Run tools, gather observations
  3. ReflectionAgent  → Review completeness
  4. ResponseGenerator → Write the final answer

WHY AN ORCHESTRATOR?
  Without an orchestrator, each component would need to know about
  the others and call them directly. That creates tight coupling.
  
  The orchestrator pattern means:
  - Each agent only knows how to do ITS job
  - The orchestrator manages the flow and data passing
  - You can easily add/remove steps in the workflow here
  - Error handling is centralized in one place

THIS IS THE CLASS THAT THE FastAPI ENDPOINT CALLS.
  main.py → orchestrator.run() → planner → executor → reflection → generator → response
"""

import time
from datetime import datetime
from models.schemas import (
    AgentRequest, AgentResponse, AgentStep,
    PlanStep, ToolUsage
)
from agent.planner import PlannerAgent
from agent.executor import ExecutorAgent
from agent.reflection import ReflectionAgent
from agent.response_generator import ResponseGeneratorAgent


class AgentOrchestrator:
    """
    Coordinates the full Agentic AI workflow from query to final answer.
    
    This is the main entry point that the API calls.
    It runs all agent components in sequence and builds the final response.
    
    Usage:
        orchestrator = AgentOrchestrator()
        response = await orchestrator.run(AgentRequest(query="What is AI?"))
    """

    def __init__(self):
        """Initialize all agent components."""
        # Create instances of all 4 agent components
        self.planner = PlannerAgent()
        self.executor = ExecutorAgent()
        self.reflector = ReflectionAgent()
        self.response_generator = ResponseGeneratorAgent()

    async def run(self, request: AgentRequest) -> AgentResponse:
        """
        Run the complete agent workflow for a user query.
        
        This is the main method — it orchestrates all steps from
        query understanding to final answer generation.
        
        The workflow:
        Step 1: Planner creates a research plan
        Step 2: Executor runs tools and gathers info
        Step 3: Reflection agent reviews completeness
        Step 4: Response generator writes the final answer
        
        Args:
            request: The AgentRequest with the user's query
            
        Returns:
            AgentResponse with the complete results
        """
        # Record the start time to calculate total processing time
        total_start = time.time()
        query = request.query.strip()

        # These lists will collect data as the workflow progresses
        all_agent_steps: list[AgentStep] = []
        plan: list[PlanStep] = []
        tools_used: list[ToolUsage] = []
        observations: list[str] = []
        reflection = ""
        final_answer = ""

        # ============================================================
        # STEP 1: PLANNING
        # The planner reads the query and creates a research plan
        # ============================================================
        try:
            plan, planning_step = self.planner.create_plan(query)
            all_agent_steps.append(planning_step)
        except Exception as e:
            # If planning completely fails, add an error step and continue
            all_agent_steps.append(AgentStep(
                step_number=1,
                step_name="Understanding & Planning",
                status="failed",
                summary=f"Planning encountered an issue: {str(e)[:100]}"
            ))
            # Use a minimal fallback plan so we can still answer
            plan = [PlanStep(
                step_number=1,
                description="Search for general information about the topic",
                tool_suggested="WikipediaSearch"
            )]

        # ============================================================
        # STEP 2: EXECUTION
        # The executor runs the tools from the plan
        # ============================================================
        try:
            tools_used, observations, execution_step = self.executor.execute_plan(
                plan=plan,
                query=query
            )
            all_agent_steps.append(execution_step)
        except Exception as e:
            all_agent_steps.append(AgentStep(
                step_number=2,
                step_name="Selecting & Executing Tools",
                status="failed",
                summary=f"Tool execution encountered an issue: {str(e)[:100]}"
            ))
            # Continue with empty observations — the response generator handles this

        # ============================================================
        # STEP 3: REFLECTION
        # The reflection agent reviews what was gathered
        # ============================================================
        try:
            tool_names = [t.tool_name for t in tools_used]
            reflection, reflection_step = self.reflector.reflect(
                query=query,
                observations=observations,
                tools_used=tool_names
            )
            all_agent_steps.append(reflection_step)
        except Exception as e:
            all_agent_steps.append(AgentStep(
                step_number=3,
                step_name="Reviewing & Reflecting",
                status="failed",
                summary=f"Reflection encountered an issue: {str(e)[:100]}"
            ))
            reflection = "Unable to perform detailed reflection. Proceeding to generate answer."

        # ============================================================
        # STEP 4: RESPONSE GENERATION
        # The response generator writes the final structured answer
        # ============================================================
        try:
            final_answer, generation_step = self.response_generator.generate(
                query=query,
                plan=plan,
                observations=observations,
                reflection=reflection,
                tools_used=tools_used
            )
            all_agent_steps.append(generation_step)
        except Exception as e:
            all_agent_steps.append(AgentStep(
                step_number=4,
                step_name="Generating Final Answer",
                status="failed",
                summary=f"Answer generation encountered an issue: {str(e)[:100]}"
            ))
            final_answer = (
                f"# Research Results\n\n"
                f"I encountered an issue generating a complete response for: *{query}*\n\n"
                f"**Error:** {str(e)}\n\n"
                f"Please check your API key configuration and try again."
            )

        # ============================================================
        # BUILD THE FINAL RESPONSE
        # Combine everything into the AgentResponse object
        # ============================================================
        total_duration = round(time.time() - total_start, 2)

        response = AgentResponse(
            query=query,
            plan=plan,
            tools_used=tools_used,
            observations=observations,
            reflection=reflection,
            final_answer=final_answer,
            steps=all_agent_steps,
            processing_time=f"{total_duration}s",
            timestamp=datetime.now().isoformat(),
            session_id=request.session_id
        )

        return response


# Create a single global orchestrator instance
# The API imports this: from agent.orchestrator import orchestrator
orchestrator = AgentOrchestrator()
