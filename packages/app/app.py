import logging
import traceback
from pathlib import Path
from decimal import Decimal
from typing import cast, Optional

import boto3
import dotenv
import chainlit as cl
import chainlit.data as cl_data
from chainlit.data.dynamodb import DynamoDBDataLayer
from chainlit.types import ThreadDict
from chainlit.logger import logger as cl_logger

dotenv.load_dotenv()  # noqa: E402

from src.config import config
from src.handlers.save_handler import SaveHandler
from src.handlers.search_handler import WebSearchHandler
from src.handlers.image_file_handler import ImageFileLoadHandler
from src.handlers.file_handler import FileLoadHandler
from src.services.section_printer import SectionPrinterService
from src.services.web_search import WebSearchService
from src.services.prompt_cache import PromptCacheService
from src.services.alps_cowriter import ALPSCowriterService
from src.constant import COMMANDS, SECTIONS
from src.utils.chainlit_patch import patch_chainlit_json
from src.utils.session import create_latest_cache_point, load_cache_point_indices
from src.utils.memory import RecentMemoryManager
from src.utils.logger import logger


# Patch Chainlit JSON serialization to handle Decimal values
patch_chainlit_json()

# Initialize services and handlers
alps_cowriter_service = ALPSCowriterService(config.llm_backend, config.model_id)
section_printer_service = SectionPrinterService(config.llm_backend, config.model_id)
prompt_cache_service = PromptCacheService(config.llm_backend)
web_search_service = WebSearchService()

file_handler = FileLoadHandler()
image_file_handler = ImageFileLoadHandler()
search_handler = WebSearchHandler(web_search_service)
save_handler = SaveHandler(section_printer_service)


def init_history_persistent_layer():
    """Initialize the history persistent layer for the ChainLit defaults."""
    if not config.history_table_name:
        logger.warning(
            "HISTORY_TABLE_NAME is not set, skipping history persistent layer initialization"
        )
        return

    # set history persistent db layer
    session = boto3.Session(profile_name=config.aws_profile)
    cl_data._data_layer = DynamoDBDataLayer(
        table_name=config.history_table_name,
        client=session.client("dynamodb", region_name=config.aws_default_region),
    )
    cl_logger.getChild("DynamoDB").setLevel(logging.INFO)


if not config.disable_oauth:
    init_history_persistent_layer()

    @cl.on_chat_resume
    async def on_chat_resume(thread: ThreadDict):
        logger.info("Chat resumed", thread_id=thread["id"])
        await cl.context.emitter.set_commands(COMMANDS)

        # Function to recursively convert Decimal to float in a dictionary
        def convert_decimal_in_dict(obj):
            if isinstance(obj, dict):
                return {k: convert_decimal_in_dict(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_decimal_in_dict(item) for item in obj]
            elif isinstance(obj, Decimal):
                return float(obj)
            else:
                return obj

        # Convert any Decimal values in the thread dictionary
        thread = convert_decimal_in_dict(thread)

        # restore the message history from the thread
        message_history = []
        for message in (m for m in thread["steps"]):
            # skip messages with exclude_from_history metadata
            if message["metadata"].get("exclude_from_history", False):
                continue

            # skip empty messages
            if message["output"] == "":
                continue

            # skip error messages
            if message["isError"]:
                logger.debug("Skipping error message", message=message)
                continue

            if message["type"] == "user_message":
                message_history.append({"role": "user", "content": message["output"]})
            elif message["type"] == "assistant_message":
                message_history.append(
                    {"role": "assistant", "content": message["output"]}
                )
            else:
                logger.debug(
                    "Skipping message with unknown type",
                    message_type=message["type"],
                    output=message["output"][:50],
                )
                continue
        logger.info("Restored message history", count=len(message_history))

        # Initialize and restore the memory managers
        recent_memory = RecentMemoryManager()
        recent_memory.add_message_history(message_history)
        cl.user_session.set("recent_memory", recent_memory)

        # create cache point at the end of the message history
        cl.user_session.set("cache_point_indices", [])
        create_latest_cache_point(cl.user_session, prompt_cache_service)

        await cl.context.emitter.send_toast("Chat Resumed", "success")

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
            "OAuth callback received",
            provider_id=provider_id,
            token_length=len(token) if token else 0,
            raw_user_data=raw_user_data,
            id_token_length=len(id_token) if id_token else 0,
        )
        logger.info("User logged in", user_id=default_user.identifier)
        return default_user


@cl.on_chat_start
async def start():
    welcome_message = """
Hello! I'm ALPS Writer. I can help you write a technical specification for your product/service.

**Here is the section list:**
{SECTIONS}

**Note:**
- If you want to modify an existing document, please attach a markdown (.md) or PDF (.pdf) file.
- If you want to write a new document, please describe the features of the MVP you want to create.

**Available Commands:**
- `/search <query>`: Reflect the web search results in the conversation
- `/save <locale>`: Save the current document in the requested locale

**Examples Messages:**
- If you input a todo list, LLM will help you complete the todo list
- If you input the item you want to buy, LLM will search for reviews and prices of the item
    """.format(SECTIONS="\n".join(SECTIONS)).strip()
    await cl.context.emitter.set_commands(COMMANDS)
    await cl.Message(
        content=welcome_message,
        metadata={"exclude_from_history": True},
    ).send()

    recent_memory = RecentMemoryManager()
    cl.user_session.set("recent_memory", recent_memory)
    cl.user_session.set("cache_point_indices", [])

    logger.info("New chat started")


@cl.on_message
async def main(message: cl.Message):
    search_result = None
    # Process commands
    if message.command == "search":
        search_result = await search_handler.handle(message)
    elif message.command == "save":
        # Exclude the /save command from the history
        message.metadata["exclude_from_history"] = True
        await message.update()

        recent_memory = cast(
            RecentMemoryManager,
            cl.user_session.get("recent_memory"),
        )
        recent_history = recent_memory.get_conversation_history()
        if not recent_history:
            await cl.Message(
                content="No conversation history found. Please start a conversation first.",
                metadata={"exclude_from_history": True},
            ).send()
            return

        # Create a cache point at the end of the message history before saving
        create_latest_cache_point(cl.user_session, prompt_cache_service)

        # Add cache points to history
        cache_point_indices = load_cache_point_indices(cl.user_session)
        cached_recent_history = prompt_cache_service.add_cache_points_to_messages(
            cache_point_indices,
            recent_history,
        )
        logger.info(
            "cache_point_indices for save command",
            cache_point_indices=cache_point_indices,
        )
        await save_handler.handle_save_command(message, cached_recent_history)
        return

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

    # Get memory managers from user session
    recent_memory = cast(
        RecentMemoryManager,
        cl.user_session.get("recent_memory"),
    )

    # Process general messages
    user_message_content = message.content

    cache_point_indices = load_cache_point_indices(cl.user_session)
    msg = cl.Message(content="")
    if search_result:
        messages = alps_cowriter_service.build_web_search_messages(
            query=user_message_content,
            web_result=search_result,
        )
        try:
            async for chunk in alps_cowriter_service.stream_llm_response(
                messages,
                system_prompt=alps_cowriter_service.get_system_prompt_for_web_qa(),
            ):
                if chunk:
                    await msg.stream_token(chunk)
            await msg.send()
        except Exception as e:
            logger.error(
                "Error streaming LLM response",
                traceback=traceback.format_exc(),
            )
            await cl.context.emitter.send_toast(
                f"Error streaming LLM response: {str(e)}", "error"
            )
            return
    else:
        # Get recent conversation history from recent memory
        recent_history = recent_memory.get_conversation_history()

        # Add cache points to history
        cached_recent_history = prompt_cache_service.add_cache_points_to_messages(
            cache_point_indices,
            recent_history,
        )
        # Build messages for ALPS writer
        messages = alps_cowriter_service.build_alps_messages(
            message_content=user_message_content,
            recent_history=cached_recent_history,
            text_context=text_context,
            image_context=image_context,
        )
        try:
            async for chunk in alps_cowriter_service.stream_llm_response(
                messages,
                system_prompt=alps_cowriter_service.get_system_prompt_for_alps(),
            ):
                if chunk:
                    await msg.stream_token(chunk)
            await msg.send()
        except Exception as e:
            logger.error(
                "Error streaming LLM response",
                traceback=traceback.format_exc(),
            )
            await cl.context.emitter.send_toast(
                f"Error streaming LLM response: {str(e)}", "error"
            )
            return

    # add AI response to memory systems
    recent_memory.add_ai_message(user_message_content, msg.content)
    cl.user_session.set("recent_memory", recent_memory)
    # update cache points
    create_latest_cache_point(cl.user_session, prompt_cache_service)
