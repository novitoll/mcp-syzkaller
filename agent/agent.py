import asyncio
import os
import sys
from datetime import datetime
from mcp_agent.app import MCPApp
from mcp_agent.agents.agent import Agent
from mcp_agent.workflows.orchestrator.orchestrator import Orchestrator
from mcp_agent.workflows.llm.augmented_llm import RequestParams
from mcp_agent.workflows.llm.augmented_llm_openai import OpenAIAugmentedLLM
from mcp_agent.workflows.llm.augmented_llm_anthropic import AnthropicAugmentedLLM
from mcp_agent.workflows.evaluator_optimizer.evaluator_optimizer import (
    EvaluatorOptimizerLLM,
    QualityRating,
)

OUTPUT_DIR = "data"
MCP_SERVER_FS = "filesystem"

mcp_app = MCPApp(name="mcp-syzkaller-syzlang-generator", human_input_callback=None,)


async def main():
    # Create output directory and set up file paths
    os.makedirs(OUTPUT_DIR, exist_ok=True)
 
    async with mcp_app.run() as app:
        ctx, logger = app.context, app.logger

        if MCP_SERVER_FS in ctx.config.mcp.servers:
            ctx.config.mcp.servers[MCP_SERVER_FS].args.extend([os.getcwd()])
            logger.info("%s server configured", MCP_SERVER_FS)

        syzlang_generator = Agent(
            name="syzlang-generator",
            instruction=f"""
            """,
            server_names=[MCP_SERVER_FS]
        )

        review_evaluator = Agent(
            name="reporter",
            instruction=f"""You are an expert research evaluator specializing in syzlang data quality.

            For each criterion, provide a rating:
            - EXCELLENT: Exceeds requirements, highly reliable
            - GOOD: Meets all requirements, reliable
            - FAIR: Missing some elements but usable
            - POOR: Missing critical information, not usable
            """,
            server_names=[MCP_SERVER_FS]
        )

        report_writer = Agent(
            name="reporter",
            instruction=f"""
            """,
            server_names=[]
        )

        logger.info("Initializing the syzkaller workflow")

        quality_controller = EvaluatorOptimizerLLM(
            optimizer=syzlang_generator,
            evaluator=review_evaluator,
            llm_factory=AnthropicAugmentedLLM,
            min_rating=QualityRating.EXCELLENT,
        )

        orchestrator = Orchestrator(
            llm=AnthropicAugmentedLLM,
            available_agents=[
                quality_controller,
                report_writer,
            ],
            plan_type="full",
        )

        # Run the orchestrator
        logger.info("Starting the stock analysis workflow")
        try:
            await orchestrator.generate_str(
                message=task, request_params=RequestParams(model="gpt-4o")
            )

            # Check if report was successfully created
            if os.path.exists(OUTPUT_DIR):
                logger.info(f"Report successfully generated: {OUTPUT_DIR}")
                return True
            else:
                logger.error(f"Failed to create report at {OUTPUT_DIR}")
                return False

        except Exception as e:
            logger.error(f"Error during workflow execution: {str(e)}")
            return False

if __name__ == "__main__":
    asyncio.run(main())
