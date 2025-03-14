import os
import sys
import json
import logging
import traceback
from pathlib import Path
from typing import Optional

import pdfplumber
import chainlit as cl
from chainlit.element import ElementBased

logger = logging.getLogger(__name__)


class FileLoadHandler:
    async def handle(self, file: ElementBased) -> Optional[str | dict]:
        """
        Process uploaded files and return file contents.

        Args:
            file (ElementBased): Chainlit ElementBased message object

        Returns:
            Optional[str]: File content or image information. Returns None if file processing fails
        """
        try:
            file_path = Path(file.path)
            file_ext = file_path.suffix.lower()

            logger.info(f"Start processing the file: {file_path}")
            logger.debug(
                f"File information: size={file_path.stat().st_size}bytes, extension={file_ext}"
            )

            if file_ext == ".pdf":
                return await self._parse_pdf(file_path)
            elif file_ext == ".json":
                return self._parse_json(file_path)
            else:  # .md
                return self._parse_text(file_path)
        except Exception as e:
            self._log_exception("Error occurred while processing the file")
            await cl.Message(
                content=f"Error occurred while processing the file: {str(e)}"
            ).send()
            return None

    async def _parse_pdf(self, file_path: Path) -> str:
        """
        Parse a PDF file and convert it to text.

        Args:
            file_path (Path): PDF file path

        Returns:
            str: Extracted text
        """
        text_parts = []
        pdf_path = str(file_path.absolute())

        logger.info(f"Start parsing the PDF file: {pdf_path}")

        try:
            # Check if the PDF file exists
            if not file_path.exists():
                raise FileNotFoundError(f"Could not found a PDF file: {pdf_path}")

            # Check if the PDF file has read permission
            if not os.access(pdf_path, os.R_OK):
                raise PermissionError(
                    f"No read permission for the PDF file: {pdf_path}"
                )

            with pdfplumber.open(pdf_path) as pdf:
                logger.debug(f"PDF information: {len(pdf.pages)} pages")

                if len(pdf.pages) == 0:
                    logger.warning("No pages found in the PDF file")
                    return "No pages found in the PDF file."

                for page_num, page in enumerate(pdf.pages, 1):
                    logger.debug(f"Processing page {page_num}...")
                    try:
                        text = page.extract_text(layout=True)
                        if text:
                            text_parts.append(f"\n=== Page {page_num} ===\n")
                            text_parts.append(text)
                            logger.debug(
                                f"Page {page_num}: Successfully extracted text ({len(text)} characters)"
                            )

                        tables = page.extract_tables()
                        if tables:
                            logger.debug(f"Page {page_num}: {len(tables)} tables found")
                            text_parts.append(f"\n=== Page {page_num} tables ===\n")
                            for table_num, table in enumerate(tables, 1):
                                text_parts.append(f"\n[Table {table_num}]\n")
                                for row in table:
                                    row_text = " | ".join(
                                        [
                                            str(cell) if cell is not None else ""
                                            for cell in row
                                        ]
                                    )
                                    text_parts.append(row_text)
                                text_parts.append("-" * 40)

                    except Exception as e:
                        self._log_exception(
                            f"Error occurred while processing the page {page_num}"
                        )
                        text_parts.append(
                            f"\n[Error occurred while processing the page {page_num}: {str(e)}]\n"
                        )
                        continue

            if not text_parts:
                logger.warning("Could not extract text from the PDF file")
                return "Could not extract text from the PDF file."

            result = "\n".join(text_parts)
            logger.info(f"PDF parsing completed: {len(result)} characters extracted")
            return result

        except Exception as e:
            self._log_exception("Error occurred while processing the PDF file")
            raise Exception(f"Error occurred while processing the PDF file: {str(e)}")

    def _log_exception(self, message: str) -> None:
        """
        Log exception information in detail.

        Args:
            message (str): log message
        """
        exc_type, exc_value, exc_traceback = sys.exc_info()
        logger.error(f"{message}:")
        logger.error(f"Exception type: {exc_type.__name__}")
        logger.error(f"Exception message: {str(exc_value)}")
        logger.error("Stack trace:")
        for line in traceback.format_tb(exc_traceback):
            logger.error(line.strip())

    def _parse_json(self, file_path: Path) -> str:
        """Parse a JSON file and convert it to a string."""
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)
            return json.dumps(data, ensure_ascii=False, indent=2)

    def _parse_text(self, file_path: Path) -> str:
        """Read a text file (markdown, etc.) and return it."""
        with open(file_path, "r", encoding="utf-8") as file:
            return file.read()
