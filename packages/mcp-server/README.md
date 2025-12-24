# ALPS Writer MCP Server

MCP server that provides ALPS (Agentic Lean Prototyping Specification) template tools.

## Installation

```bash
cd packages/mcp-server
uv sync
```

## Usage

### Run as stdio server

```bash
uv run alps-mcp-server
```

### Configure in Claude Desktop / Cursor

Add to your MCP config:

```json
{
  "mcpServers": {
    "alps-writer": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/alps-writer/packages/mcp-server",
        "run",
        "alps-mcp-server"
      ]
    }
  }
}
```

## Available Tools

| Tool                     | Description                            |
| ------------------------ | -------------------------------------- |
| `get_alps_overview`      | Get the ALPS template overview         |
| `list_alps_sections`     | List all available sections            |
| `get_alps_section`       | Get a specific section by number (1-9) |
| `get_alps_full_template` | Get the complete template              |

## Template Structure

```
src/alps_mcp_server/
├── __init__.py
├── server.py
└── templates/
    ├── overview.md           # Template overview
    └── chapters/
        ├── 01-overview.md
        ├── 02-mvp-goals.md
        ├── 03-demo-scenario.md
        ├── 04-architecture.md
        ├── 05-design-spec.md
        ├── 06-requirements.md
        ├── 07-feature-spec.md
        ├── 08-mvp-metrics.md
        └── 09-out-of-scope.md
```
