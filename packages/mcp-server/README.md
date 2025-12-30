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

### Template Tools
| Tool                     | Description                            |
| ------------------------ | -------------------------------------- |
| `get_alps_overview`      | Get the ALPS template overview         |
| `list_alps_sections`     | List all available sections            |
| `get_alps_section`       | Get a specific section by number (1-9) |
| `get_alps_full_template` | Get the complete template              |
| `get_alps_section_guide` | Get conversation guide for a section   |

### Document Management Tools
| Tool                       | Description                                        |
| -------------------------- | -------------------------------------------------- |
| `init_alps_document`       | Create new ALPS document (.alps.md file)           |
| `load_alps_document`       | Load existing document to resume editing           |
| `save_alps_section`        | Save content to a specific section                 |
| `read_alps_section`        | Read current content of a section                  |
| `get_alps_document_status` | Get status of all sections                         |
| `export_alps_markdown`     | Export as clean markdown (without XML tags)        |

## Document Format

The ALPS document uses XML tags for reliable section parsing:

```markdown
# Project Name ALPS

<section id="1">
## Section 1. Overview

Content here...
</section>

<section id="2">
## Section 2. MVP Goals and Key Metrics

Content here...
</section>

...
```

Use `export_alps_markdown()` to get a clean markdown version without XML tags.

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
