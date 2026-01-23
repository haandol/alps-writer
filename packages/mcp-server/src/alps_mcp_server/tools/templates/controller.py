"""Template controller - MCP interface for ALPS templates."""

from .service import TemplateService


class TemplateController:
    def __init__(self, service: TemplateService):
        self.service = service

    def get_alps_overview(self) -> str:
        """Get the ALPS template overview with all section descriptions.
        
        IMPORTANT: After calling this, you MUST call get_alps_section_guide(1) 
        to start the interactive Q&A process. Never auto-generate sections.
        """
        content = self.service.get_overview()
        return content + """

---
## Next Step

**REQUIRED**: Call `get_alps_section_guide(1)` to begin interactive writing.
Do NOT write any section without going through the guide's Q&A process first."""

    def list_alps_sections(self) -> list[dict]:
        """List all available ALPS template sections.
        
        Returns:
            List of sections with section number and filename.
        """
        return self.service.list_sections()

    def get_alps_section(self, section: int) -> str:
        """Get a specific ALPS template section by number.
        
        Args:
            section: Section number (1-9)
        
        Returns:
            The section template content.
        """
        return self.service.get_section(section)

    def get_alps_full_template(self) -> str:
        """Get the complete ALPS template with all sections combined."""
        return self.service.get_full_template()

    def get_alps_section_guide(self, section: int) -> str:
        """Get conversation guide for writing a specific ALPS section.
        
        Use this before starting each section to guide the interactive conversation.
        Returns questions to ask, completion criteria, and important notes.
        For sections with dependencies, includes required review instructions.
        
        Args:
            section: Section number (1-9)
        
        Returns:
            Conversation guide with questions and completion criteria.
        """
        return self.service.get_section_guide(section)
