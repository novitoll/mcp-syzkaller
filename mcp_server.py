import typing as t
import os
import requests
from pathlib import Path
from datetime import datetime

from mcp.server.fastmcp import FastMCP


OUTPUT_DIR = Path("output")

mcp = FastMCP("mcp-syzkaller", dependencies=[
    "sequential-thinking",
    "context7",
])

def get_prompt_from_tmpl(tmpl_name: str, **kwargs) -> str:
    with open(f"prompts/{tmpl_name}", "r") as f:
        prompt = f.read()
    for key, value in kwargs.items():
        prompt = prompt.replace(f"{{{key}}}", value)
    return prompt

@mcp.tool(description="Update a syzlang file for a given target and Linux kernel C file.")
def update_syzlang(
    subsystem_name: str,
    subsystem_documentation_http_link: str,
    linux_kernel_c_file_http_link: str,
    syzkaller_syzlang_file_http_link: str,
    syzkaller_test_seed_program: str,
    os_target: t.Optional[str] = "linux",
) -> str:
    prompt = get_prompt_from_tmpl(
        "prompt_update_syzlang.txt",
        subsystem_name=subsystem_name,
        subsystem_documentation_http_link=subsystem_documentation_http_link,
        linux_kernel_c_file_http_link=linux_kernel_c_file_http_link,
        syzkaller_syzlang_file_http_link=syzkaller_syzlang_file_http_link,
        syzkaller_test_seed_program=syzkaller_test_seed_program,
        os_target=os_target,
    )

    response = mcp.ask(prompt)

    # Save to file with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"syzlang_{os_target}_{timestamp}.txt"
    output_path = OUTPUT_DIR / filename

    with open(output_path, "w+") as f:
        f.write(response)

    return f"Generated syzlang saved to {output_path}"


if __name__ == "__main__":
    OUTPUT_DIR.mkdir(exist_ok=True)
    mcp.run()
    # update_syzlang(
    #     subsystem_name="j1939",
    #     subsystem_documentation_http_link="https://docs.kernel.org/networking/j1939.html",
    #     linux_kernel_c_file_http_link="https://github.com/torvalds/linux/blob/master/net/can/j1939/transport.c",
    #     syzkaller_syzlang_file_http_link="https://github.com/google/syzkaller/blob/master/sys/linux/socket_can.txt",
    #     syzkaller_test_seed_program="https://github.com/google/syzkaller/blob/master/sys/linux/test/can.c",
    #     os_target="linux",
    # )