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

| Tool                       | Description                                 |
| -------------------------- | ------------------------------------------- |
| `init_alps_document`       | Create new ALPS document (.alps.md file)    |
| `load_alps_document`       | Load existing document to resume editing    |
| `save_alps_section`        | Save content to a specific section          |
| `read_alps_section`        | Read current content of a section           |
| `get_alps_document_status` | Get status of all sections                  |
| `export_alps_markdown`     | Export as clean markdown (without XML tags) |

## Project Structure

```
src/alps_mcp_server/
├── __init__.py
├── server.py              # MCP server entry point + tool registration
├── di/
│   └── container.py       # Dependency injection container
├── tools/
│   ├── templates/         # Template tools
│   │   ├── controller.py  # MCP interface (docstrings)
│   │   └── service.py     # Business logic
│   └── documents/         # Document management tools
│       ├── controller.py
│       └── service.py
├── interfaces/
│   └── constants.py       # SECTION_TITLES, SECTION_REFERENCES, paths
├── guides/                # Section guides (01.md ~ 09.md)
└── templates/
    ├── overview.md
    └── chapters/
        └── 01-overview.md ~ 09-out-of-scope.md
```

## Document Format

The ALPS document uses XML format for storage and reliable section parsing:

```xml
<alps-document>
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
</alps-document>
```

- Storage format: `.alps.xml` (XML with section tags)
- Output format: Clean markdown via `export_alps_markdown()`

## Development

```bash
# Run tests
uv run pytest

# Run tests with verbose output
uv run pytest -v
```
