import os
import boto3
import logging
from pathlib import Path
from typing import cast, Optional, List

import dotenv
import chainlit as cl
import chainlit.data as cl_data
from chainlit.logger import logger as cl_logger
from chainlit.types import ThreadDict
from chainlit.data.dynamodb import DynamoDBDataLayer

from src.constant import COMMANDS
from src.services.llm_cowriter import LLMCowriterService
from src.services.web_search import WebSearchService
from src.handlers.file_handler import FileLoadHandler
from src.handlers.image_file_handler import ImageFileLoadHandler
from src.handlers.search_handler import WebSearchHandler

dotenv.load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Set environment variables
# disable oauth only for the local test
DISABLE_OAUTH = os.environ.get("DISABLE_OAUTH", "false").lower() == "true"
logger.info(f"DISABLE_OAUTH: {DISABLE_OAUTH}")
AWS_PROFILE_NAME = os.environ.get("AWS_PROFILE_NAME", None)
logger.info(f"AWS_PROFILE_NAME: {AWS_PROFILE_NAME}")


# Initialize services and handlers
llm_cowriter_service = LLMCowriterService()
web_search_service = WebSearchService()
file_handler = FileLoadHandler()
image_file_handler = ImageFileLoadHandler()
search_handler = WebSearchHandler(web_search_service)


def init_history_persistent_layer():
    """Initialize the history persistent layer for the ChainLit defaults."""
    HISTORY_TABLE_NAME = os.environ.get("HISTORY_TABLE_NAME", "")
    assert HISTORY_TABLE_NAME, "HISTORY_TABLE_NAME environment variable not set"

    AWS_DEFAULT_REGION = os.environ.get("AWS_DEFAULT_REGION", None)
    logger.info(f"AWS_DEFAULT_REGION: {AWS_DEFAULT_REGION}")

    # set history persistent db layer
    session = boto3.Session(profile_name=AWS_PROFILE_NAME)
    cl_data._data_layer = DynamoDBDataLayer(
        table_name=HISTORY_TABLE_NAME,
        client=session.client("dynamodb", region_name=AWS_DEFAULT_REGION),
    )
    cl_logger.getChild("DynamoDB").setLevel(logging.INFO)


if not DISABLE_OAUTH:
    init_history_persistent_layer()

    @cl.on_chat_resume
    async def on_chat_resume(thread: ThreadDict):
        logger.info(f"Chat resumed: {thread}")
        # restore the message history from the thread
        message_history = cl.user_session.get("message_history", [])
        root_messages = [m for m in thread["steps"] if m["parentId"] is None]
        for message in root_messages:
            # skip the message if the metadata indicates that the history should be skipped
            if message["metadata"].get("skip_history", False):
                continue

            if message["type"] == "user_message":
                message_history.append(
                    {"role": "user",
                        "content": f"<user>{message['output']}</user>"}
                )
            else:
                message_history.append(
                    {"role": "assistant", "content": message["output"]}
                )
        logger.info(f"Restored message_history: {len(message_history)}")
        cl.user_session.set("message_history", message_history)

    @cl.oauth_callback
    async def oauth_callback(
        provider_id: str,
        token: str,
        raw_user_data: dict[str, str],
        default_user: cl.User,
        id_token: Optional[str] = None,
    ) -> Optional[cl.User]:
        """Callback for Cognito OAuth providers."""

        logger.debug(
            f"OAuth callback for provider {provider_id}, "
            f"token: {token}, "
            f"raw_user_data: {raw_user_data}, "
            f"id_token: {id_token}"
        )
        return default_user


@cl.on_chat_start
async def start():
    welcome_message = """
Hello! I'm ALPS Writer. I can help you write a technical specification for your product/service.

Note:
- If you want to modify an existing document, please attach a markdown (.md) or PDF (.pdf) file.
- If you want to write a new document, please describe the features of the MVP you want to create.

Available Commands:
- `/search <query>`: Reflect the web search results in the conversation

Examples Messages:
- If you input a todo list, LLM will help you complete the todo list
- If you input the item you want to buy, LLM will search for reviews and prices of the item
    """.strip()
    await cl.context.emitter.set_commands(COMMANDS)
    await cl.Message(content=welcome_message).send()
    # Initialize the message history
    cl.user_session.set("message_history", [])


@cl.on_message
async def main(message: cl.Message):
    search_result = None
    # Process commands
    if message.command == "search":
        search_result = await search_handler.handle(message)

    # Process file uploads
    text_context = None
    image_context = None
    elements = message.elements
    if elements:
        # Process only the first file
        element = elements[0]
        text_file_ext = [".json", ".md", ".pdf"]
        image_file_ext = [".jpg", ".jpeg", ".png", ".gif", ".webp"]
        available_file_extensions = text_file_ext + image_file_ext
        if element.path:
            if Path(element.path).suffix.lower() not in available_file_extensions:
                await cl.Message(
                    content=f"file format is not supported.\n**supported file formats:** {available_file_extensions}"
                ).send()
                return

            if Path(element.path).suffix.lower() in text_file_ext:
                text_context = await file_handler.handle(element)
            elif Path(element.path).suffix.lower() in image_file_ext:
                image_context = await image_file_handler.handle(element)

    # Process general messages
    message_history = cast(List, cl.user_session.get("message_history", []))
    if text_context:
        message_history.append(
            {
                "role": "user",
                "content": f"<user><context>{text_context}</context>\n---\n{message.content}</user>",
            }
        )
    elif image_context:
        message_history.append(
            {
                "role": "user",
                "content": f"<user>{message.content}</user>",
                "image": image_context,
            }
        )
    else:
        message_history.append(
            {"role": "user", "content": f"<user>{message.content}</user>"}
        )
    cl.user_session.set("message_history", message_history)

    msg = cl.Message(content="")
    if search_result:
        async for chunk in llm_cowriter_service.answer_question_stream(
            message.content, search_result
        ):
            if chunk:
                await msg.stream_token(chunk)
    else:
        async for chunk in llm_cowriter_service.cowrite_alps_template_stream(
            message_history
        ):
            if chunk:
                await msg.stream_token(chunk)
    await msg.send()

    message_history.append({"role": "assistant", "content": msg.content})
    cl.user_session.set("message_history", message_history)
