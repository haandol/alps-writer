import os
import datetime
import traceback
from typing import Dict, List
from pathlib import Path

import chainlit as cl
from strands.types.content import Message

from src.services.section_printer import SectionPrinterService
from src.utils.logger import logger


class SaveHandler:
    def __init__(self, section_printer_service: SectionPrinterService):
        self.section_printer_service = section_printer_service
        self.section_groups = [
            (
                "Section 1",
                "Section 2",
                "Section 3",
                "Section 4",
                "Section 5",
                "Section 6",
            ),
            ("Section 7",),
            ("Section 8", "Section 9"),
        ]

    async def handle_save_command(
        self, message: cl.Message, recent_history: List[Message]
    ) -> None:
        """
        Handle the /save command to generate and save a document in the specified locale.

        Args:
            message (cl.Message): The user message containing the /save command
        """
        # Extract locale from the message
        locale = message.content.replace("/save", "").strip()
        if not locale:
            locale = "English"  # Default to English if no locale specified

        document_sections = {}
        async with cl.Step(name="Generating document", type="tool") as step:
            try:
                # Generate the document in batches using section groups
                for section_group in self.section_groups:
                    group_name = ", ".join(section_group)

                    # Create a step to show progress
                    async with cl.Step(name=group_name, type="tool") as each_step:
                        each_step.input = f"Generating {group_name} in {locale}"

                        # Build messages for section printer
                        messages = (
                            self.section_printer_service.build_section_printer_messages(
                                recent_history=recent_history,
                                section=section_group,
                                locale=locale,
                            )
                        )

                        # Collect section content
                        section_content = ""
                        try:
                            async for (
                                chunk
                            ) in self.section_printer_service.stream_llm_response(
                                messages,
                                system_prompt=self.section_printer_service.get_system_prompt(),
                            ):
                                section_content += chunk
                                await each_step.stream_token(chunk)
                            logger.info(
                                "Generated section",
                                group_name=group_name,
                                locale=locale,
                                length=len(section_content),
                            )
                        except Exception as e:
                            logger.error("Error on streaming LLM response", error=e)
                            step.output = (
                                f"An error occurred while saving the document: {str(e)}"
                            )
                            return

                        # check if the section is complete, heuristic: if the section is less than 100 words, it is incomplete
                        if len(section_content.strip()) < 100:
                            logger.info(
                                "Incomplete section",
                                group_name=group_name,
                                locale=locale,
                                length=len(section_content),
                            )
                            step.output = f"{group_name} is incomplete. Stopping..."
                            return

                        # Store the section in the document_sections dictionary
                        document_sections[section_group] = section_content

                async with cl.Step(name="Save document", type="tool"):
                    # Combine all sections into a final document
                    final_document = self._combine_document_sections(document_sections)

                    # Save the document to a file
                    file_path = await self._save_document_to_file(
                        final_document, locale
                    )

                    # Create a downloadable file
                    file = cl.File(name=os.path.basename(file_path), path=file_path)

                    # Send the message with the document link, exclude the message from the history
                    await cl.Message(
                        content=f"Document has been generated in {locale}. Click the attachment to download.",
                        elements=[file],
                        metadata={"exclude_from_history": True},
                    ).send()

            except Exception as e:
                logger.error(
                    "Error on generating document", traceback=traceback.format_exc()
                )
                step.output = f"An error occurred while saving the document: {str(e)}"

    def _combine_document_sections(self, document_sections: Dict[str, str]) -> str:
        """
        Combines all document sections into a single document.

        Args:
            document_sections (Dict[str, str]): Dictionary of section IDs to their content

        Returns:
            str: The combined document
        """
        combined_document = "# ALPS Document\n\n"

        # Add sections in order
        for key in document_sections:
            combined_document += document_sections[key] + "\n\n"

        return combined_document

    async def _save_document_to_file(self, document_content: str, locale: str) -> str:
        """
        Saves the document content to a file.

        Args:
            document_content (str): The document content
            locale (str): The document locale

        Returns:
            str: The path to the saved file
        """
        # Create the output directory if it doesn't exist
        output_dir = Path("./output")
        output_dir.mkdir(exist_ok=True)

        # Generate a filename with timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        locale_slug = locale.replace(" ", "_").lower()
        file_name = f"alps_document_{locale_slug}_{timestamp}.md"
        file_path = output_dir / file_name

        # Write the content to the file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(document_content)

        return str(file_path)
