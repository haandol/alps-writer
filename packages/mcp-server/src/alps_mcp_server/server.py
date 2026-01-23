"""ALPS Writer MCP Server - Provides ALPS template tools for spec writing."""

from mcp.server.fastmcp import FastMCP

from alps_mcp_server.di.container import DIContainer

mcp = FastMCP(
    "alps-writer",
    instructions="""You are an intelligent product owner helping users create ALPS documents.

<WORKFLOW>
1. init_alps_document() or load_alps_document()
2. get_alps_overview() - MUST call first to get conversation guide
3. For each section 1-9:
   a. get_alps_section_guide(N)
   b. get_alps_section(N)
   c. Follow conversation guide from overview
   d. save_alps_section(N, content) after user confirmation
5. export_alps_markdown() for final output
</WORKFLOW>

<RULES>
- MUST call get_alps_overview() first to get detailed conversation guide
- NEVER generate multiple sections at once
- NEVER proceed without user confirmation
</RULES>"""
)


def register_tools(mcp_instance: FastMCP, container: DIContainer):
    """Register all MCP tools from controllers."""
    tc = container.template_controller
    mcp_instance.tool()(tc.get_alps_overview)
    mcp_instance.tool()(tc.list_alps_sections)
    mcp_instance.tool()(tc.get_alps_section)
    mcp_instance.tool()(tc.get_alps_full_template)
    mcp_instance.tool()(tc.get_alps_section_guide)

    dc = container.document_controller
    mcp_instance.tool()(dc.init_alps_document)
    mcp_instance.tool()(dc.load_alps_document)
    mcp_instance.tool()(dc.save_alps_section)
    mcp_instance.tool()(dc.read_alps_section)
    mcp_instance.tool()(dc.get_alps_document_status)
    mcp_instance.tool()(dc.export_alps_markdown)


def main():
    container = DIContainer()
    register_tools(mcp, container)
    mcp.run()


if __name__ == "__main__":
    main()
