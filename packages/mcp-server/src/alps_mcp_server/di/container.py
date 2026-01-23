"""Dependency injection container for ALPS MCP Server."""

from typing import Optional

from alps_mcp_server.tools.templates import TemplateController, TemplateService
from alps_mcp_server.tools.documents import DocumentController, DocumentService


class DIContainer:
    def __init__(self):
        self._template_service: Optional[TemplateService] = None
        self._template_controller: Optional[TemplateController] = None
        self._document_service: Optional[DocumentService] = None
        self._document_controller: Optional[DocumentController] = None

    @property
    def template_service(self) -> TemplateService:
        if self._template_service is None:
            self._template_service = TemplateService()
        return self._template_service

    @property
    def template_controller(self) -> TemplateController:
        if self._template_controller is None:
            self._template_controller = TemplateController(self.template_service)
        return self._template_controller

    @property
    def document_service(self) -> DocumentService:
        if self._document_service is None:
            self._document_service = DocumentService()
        return self._document_service

    @property
    def document_controller(self) -> DocumentController:
        if self._document_controller is None:
            self._document_controller = DocumentController(self.document_service)
        return self._document_controller
