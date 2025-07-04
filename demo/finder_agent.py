import asyncio
import os

from mcp_agent.app import MCPApp
from mcp_agent.agents.agent import Agent
from mcp_agent.workflows.llm.augmented_llm_openai import OpenAIAugmentedLLM
from mcp_agent.workflows.llm.augmented_llm import RequestParams

app = MCPApp(name="mcp-linux-kernel")

async def example_usage():
    async with app.run() as mcp_agent_app:
        logger = mcp_agent_app.logger
        crash_analyzer = Agent(
            name="syzkaller_crash_report_analyzer",
            instruction="""
You are an expert at reviewing the Linux kernel crash reports submitted by syzkaller.
Your speciality is understanding the rootcause of the crash and providing your analysis.
You will also need to provide the patch to fix the crash report.
Make sure that your patch code is elegant and corresponds to the Linux kernel development style.
You will be provided with the HTTP link of the crash report. You will analyze the report carefully.
It has necessary starting entrypoints of your analysis like "Call Trace" where the crash has happened.
Crash reports have a title in the beginning like "KASAN:" which should indicate the type of the crash.
You need to find the rootcause of why it has happened.
You are very careful to avoid reporting false positives.
You write down a detailed, step by step, description of the code paths from the entry points in the code up to the point where the crash occurs.
Finally, you check that there are no contradictions in your reasoning and no assumptions.
You can read local files or fetch URLs.
Return the requested information when asked.""",
            server_names=["fetch"], # MCP servers this Agent can use
        )

        async with crash_analyzer:
            # Automatically initializes the MCP servers and adds their tools for LLM use
            tools = await crash_analyzer.list_tools()
            logger.info(f"Tools available:", data=tools)

            # Attach an OpenAI LLM to the agent (defaults to GPT-4o)
            llm = await crash_analyzer.attach_llm(OpenAIAugmentedLLM)

            result = await llm.generate_str(
                request_params=RequestParams(maxTokens=10240, temperature=0.7, max_iterations=10),
                message="""
Hello,

syzbot found the following issue on:

HEAD commit:    785cdec46e92 Merge tag 'x86-core-2025-05-25' of git://git...
git tree:       upstream
console output: https://syzkaller.appspot.com/x/log.txt?x=13e47df4580000
kernel config:  https://syzkaller.appspot.com/x/.config?x=d7ed3189f3c3d3f3
dashboard link: https://syzkaller.appspot.com/bug?extid=9afaf6749e3a7aa1bdf3
compiler:       gcc (Debian 12.2.0-14) 12.2.0, GNU ld (GNU Binutils for Debian) 2.40
syz repro:      https://syzkaller.appspot.com/x/repro.syz?x=17ad26d4580000
C reproducer:   https://syzkaller.appspot.com/x/repro.c?x=157f3170580000

Here is the HTTP link with the crash report happened in Linux kernel upstream tree:
https://syzkaller.appspot.com/text?tag=CrashReport&x=17e47df4580000
"""
            )
            logger.info(f"!!!!!! Analyze syzkaller crash report: {result}")

if __name__ == "__main__":
    asyncio.run(example_usage())
