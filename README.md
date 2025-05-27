# mcp-syzkaller

MCP agent for the [syzkaller](https://github.com/google/syzkaller).

Project is in WIP.

## Tools

* ### generate-syzlang
Generate syscall descriptions AKA syzlang of the given source code.

* ### review-crash-report
Review the provided syzkaller crask report link. Analyze the problem.
Attempt to summarize with the suggested patch and details.

## Notes

- Use Context7 MCP server to use the latest Linux kernel git tree
- Use Sequential Thinking MCP server


Some ideas what to test in this project:
* use Context7 MCP server to locate the code only for the specific commit of Linux kernel
* think about the RAG to organize more proper prompt to LLM

## MCP Client

```json
{
  "mcpServers": {

    "sequential-thinking": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-sequential-thinking"
      ]
    },

    "context7": {
      "url": "https://mcp.context7.com/mcp"
    },

    "mcp-syzkaller": {
      "command": "python",
      "args": ["mcp_server.py"]
    }
  }
}
```