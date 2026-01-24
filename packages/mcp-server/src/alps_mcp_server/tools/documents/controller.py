"""Document controller - MCP interface for ALPS document management."""

from .service import DocumentService


class DocumentController:
    def __init__(self, service: DocumentService):
        self.service = service

    def init_alps_document(self, project_name: str, output_path: str) -> str:
        """Initialize a new ALPS document file.
        
        Creates an XML-based document for reliable section parsing.
        
        Args:
            project_name: Name of the project
            output_path: File path for the document (e.g., ~/Documents/my-project.alps.xml)
        
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
            doc_path: Path to the .alps.xml file
        
        Returns:
            Document status summary.
        """
        return self.service.load_document(doc_path)

    def save_alps_section(self, section: int, subsection_id: str, title: str, content: str) -> str:
        """Save content to a subsection in the ALPS document.
        
        ⚠️ BEFORE CALLING THIS TOOL:
        1. 작성 완료된 내용을 사용자에게 먼저 출력하세요
        2. "수정할 내용이 있으신가요?" 라고 확인을 요청하세요
        3. 사용자가 확인한 후에만 이 도구를 호출하세요
        
        Args:
            section: Section number (1-9)
            subsection_id: Subsection ID within the section (e.g., "1" for X.1, "1.2" for X.1.2)
            title: Title of the subsection
            content: Content for the subsection (markdown)
        
        Returns:
            Confirmation message.
        
        Examples:
            save_alps_section(1, "1", "Purpose", "This project aims to...")
            save_alps_section(7, "1.3", "Edge Cases", "- Empty input\\n- Network timeout")
        """
        return self.service.save_section(section, subsection_id, title, content)

    def read_alps_section(self, section: int, subsection_id: str | None = None) -> str:
        """Read the current content of a section or subsection.
        
        Args:
            section: Section number (1-9)
            subsection_id: Subsection ID (e.g., "1" for X.1). If omitted, returns entire section.
        
        Returns:
            Current content of the section/subsection.
        """
        return self.service.read_section(section, subsection_id)

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
