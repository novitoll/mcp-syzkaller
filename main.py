import asyncio
import os
import logging
import typing as t

from mcp_agent.app import MCPApp
from mcp_agent.server.app_server import create_mcp_server_for_app
from mcp_agent.agents.agent import Agent
from mcp_agent.workflows.llm.augmented_llm import RequestParams
from mcp_agent.workflows.llm.llm_selector import ModelPreferences
from mcp_agent.workflows.llm.augmented_llm_anthropic import AnthropicAugmentedLLM
from mcp_agent.workflows.llm.augmented_llm_openai import OpenAIAugmentedLLM
from mcp_agent.executor.workflow import Workflow, WorkflowResult

from mcp_agent.human_input.handler import console_input_callback

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


app = MCPApp(
    name="mcp-syzkaller",
    description="MCP for the syzkaller",
    human_input_callback=console_input_callback,
)


@app.workflow
class BasicAgentWorkflow(Workflow[str]):

    def get_prompt_from_tmpl(self, tmpl_name: str, ctx: dict, vars: t.List[str]) -> str:
        with open(f"prompts/{tmpl_name}", "r") as f:
            prompt = f.read()

        for key in vars:
            prompt = prompt.replace(f"{{key}}", ctx.get(key, None))
        return prompt

    @app.workflow_run
    async def run(self, input: str) -> WorkflowResult[str]:
        logger = app.logger
        context = app.context

        logger.info("Current config:", data=context.config.model_dump())
        logger.info("Received input", input)

        # Add the current directory to the filesystem server's args
        context.config.mcp.servers["filesystem"].args.extend([os.getcwd()])

        syzlang_generator = Agent(
            name="syzlang_generator",
            instruction=lambda ctx: self.get_prompt_from_tmpl(ctx, [
                "subsystem_name",
                "linux_kernel_c_file_http_link",
                "syzkaller_syzlang_file_http_link",
                "syzkaller_test_seed_program",
            ]),
            server_names=["fetch", "filesystem", "context7"],
        )

        async with syzlang_generator:
            logger.info("syzlang_generator: Connected to server, calling list_tools...")
            result = await syzlang_generator.list_tools()
            logger.info("Tools available:", data=result.model_dump())

            llm = await syzlang_generator.attach_llm(OpenAIAugmentedLLM)

            result = await llm.generate_str(
                message=input,
                request_params=RequestParams(
                    # See https://modelcontextprotocol.io/docs/concepts/sampling#model-preferences for more details
                    modelPreferences=ModelPreferences(
                        costPriority=0.1,
                        speedPriority=0.2,
                        intelligencePriority=0.7,
                    ),
                    model="o3",
                ),
            )
            logger.info(f"Input: {input}, Result: {result}")

            return WorkflowResult(value=result)


async def main():
    async with app.run() as agent_app:
        context = agent_app.context
        if "filesystem" in context.config.mcp.servers:
            context.config.mcp.servers["filesystem"].args.extend([os.getcwd()])

        logger.info(f"Creating MCP server for {agent_app.name}")

        logger.info("Registered workflows:")
        for workflow_id in agent_app.workflows:
            logger.info(f"  - {workflow_id}")

        # Create the MCP server that exposes the workflow and agent configurations
        mcp_server = create_mcp_server_for_app(agent_app)

        # Run the server
        await mcp_server.run_stdio_async()


if __name__ == "__main__":
    asyncio.run(main())