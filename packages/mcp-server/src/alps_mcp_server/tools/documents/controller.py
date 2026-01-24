"""Document controller - MCP interface for ALPS document management."""

from .service import DocumentService


class DocumentController:
    def __init__(self, service: DocumentService):
        self.service = service

    def init_alps_document(self, project_name: str, output_path: str) -> str:
        """Initialize a new ALPS document file.
        
        Args:
            project_name: Name of the project
            output_path: File path for the document (e.g., ~/Documents/my-project.alps.md)
        
        Returns:
            Confirmation with file path.
        """
        return self.service.init_document(project_name, output_path)

    def load_alps_document(self, doc_path: str) -> str:
        """Load an existing ALPS document to resume editing.
        
        ⚠️ CRITICAL: After loading, you MUST follow the conversation guide:
        1. Call get_alps_section_guide(N) for the section you want to work on
        2. Ask 1-2 focused questions at a time - DO NOT auto-generate content
        3. Wait for user response before proceeding
        4. Get explicit confirmation before saving each section
        
        NEVER auto-fill sections based on existing content without user Q&A.
        
        Args:
            doc_path: Path to the .alps.md file
        
        Returns:
            Document status summary.
        """
        return self.service.load_document(doc_path)

    def save_alps_section(self, section: int, content: str, subsection: int | None = None) -> str:
        """Save content to a specific section in the ALPS document.
        
        ⚠️ CRITICAL FOR SECTION 7:
        Section 7 uses subsections (7.1, 7.2, 7.3...) for each feature.
        You MUST use the `subsection` parameter when saving Section 7 content.
        - save_alps_section(7, content, subsection=1) → saves to 7.1
        - save_alps_section(7, content, subsection=2) → saves to 7.2
        
        DO NOT call save_alps_section(7, content) without subsection parameter.
        This will overwrite ALL existing subsections!
        
        Args:
            section: Section number (1-9)
            content: Markdown content for the section (without header)
            subsection: Subsection number. REQUIRED for Section 7 (1 for 7.1, 2 for 7.2, etc.)
        
        Returns:
            Confirmation message.
        """
        return self.service.save_section(section, content, subsection)

    def read_alps_section(self, section: int) -> str:
        """Read the current content of a specific section.
        
        Args:
            section: Section number (1-9)
        
        Returns:
            Current content of the section.
        """
        return self.service.read_section(section)

    def get_alps_document_status(self) -> str:
        """Get the status of all sections in the current document.
        
        Returns:
            Status summary showing which sections are completed/in-progress/not-started.
        """
        return self.service.get_status()

    def export_alps_markdown(self, output_path: str | None = None) -> str:
        """Export the ALPS document as clean markdown (without XML tags).
        
        Args:
            output_path: Optional output file path. If not provided, returns the content.
        
        Returns:
            Clean markdown content or confirmation message.
        """
        return self.service.export_markdown(output_path)
