import io
import base64
import traceback
from typing import Optional
from pathlib import Path

import chainlit as cl
from chainlit.element import ElementBased
from PIL import Image

from src.utils.logger import logger


class ImageFileLoadHandler:
    async def handle(self, file: ElementBased) -> Optional[str | dict]:
        """
        Process uploaded image files and return file contents.

        Args:
            file (ElementBased): Chainlit ElementBased message object

        Returns:
            Optional[dict]: File content or image information. Returns None if file processing fails
        """
        try:
            file_path = Path(file.path)
            file_ext = file_path.suffix.lower()

            logger.info("Start processing the file",
                        file_path=file_path)
            logger.debug("File information",
                         size=file_path.stat().st_size,
                         extension=file_ext)

            # Process image files
            if file_ext in [".jpg", ".jpeg", ".png", ".gif", ".webp"]:
                return await self._process_image(file_path)
            else:
                return None
        except Exception as e:
            logger.error("Error occurred while processing the file",
                         traceback=traceback.format_exc())
            await cl.context.emitter.send_toast(
                f"Error occurred while processing the file: {str(e)}",
                "error"
            ).send()
            return None

    async def _process_image(self, file_path: Path) -> dict:
        """
        Process image files and convert them to a base64 encoded string.

        Args:
            file_path (Path): Image file path

        Returns:
            dict: Dictionary containing image information
        """
        try:
            # Open the image file
            with Image.open(file_path) as img:
                # Convert the image to bytes
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format=img.format)
                img_byte_arr = img_byte_arr.getvalue()

                # Encode the image to base64
                base64_img = base64.b64encode(img_byte_arr).decode("utf-8")

                return {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "mediaType": f"image/{img.format.lower()}",
                        "data": base64_img
                    }
                }
        except Exception as e:
            logger.error("Error occurred while processing the image",
                         traceback=traceback.format_exc())
            raise Exception(f"Failed to process the image: {str(e)}")
