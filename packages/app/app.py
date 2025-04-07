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

from src.constant import COMMANDS, SECTIONS
from src.services.llm_cowriter import LLMCowriterService
from src.services.prompt_cache import PromptCacheService
from src.services.web_search import WebSearchService
from src.handlers.file_handler import FileLoadHandler
from src.handlers.image_file_handler import ImageFileLoadHandler
from src.handlers.search_handler import WebSearchHandler
from src.utils.memory import RecentMemoryManager
from src.utils.logger import logger

dotenv.load_dotenv()

# Set environment variables
# disable oauth only for the local test
DISABLE_OAUTH = os.environ.get("DISABLE_OAUTH", "false").lower() == "true"
logger.info(f"DISABLE_OAUTH: {DISABLE_OAUTH}")
AWS_PROFILE_NAME = os.environ.get("AWS_PROFILE_NAME", None)
logger.info(f"AWS_PROFILE_NAME: {AWS_PROFILE_NAME}")
MODEL_ID = os.environ.get("MODEL_ID", None)
logger.info(f"MODEL_ID: {MODEL_ID}")

# Initialize services and handlers
prompt_cache_service = PromptCacheService()
llm_cowriter_service = LLMCowriterService(MODEL_ID)
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
        logger.info(f"Chat resumed: {thread['id']}")
        await cl.context.emitter.set_commands(COMMANDS)

        # restore the message history from the thread
        message_history = []
        for message in (m for m in thread["steps"]):
            # skip messages with exclude_from_history metadata
            if message['metadata'].get('exclude_from_history', False):
                continue

            # skip empty messages
            if message['output'] == "":
                continue

            # skip error messages
            if message["isError"]:
                logger.debug(f"Skip Error message: {message}")
                continue

            if message["type"] == "user_message":
                message_history.append(
                    {"role": "user", "content": message['output']}
                )
            else:
                message_history.append(
                    {"role": "assistant", "content": message["output"]}
                )
        logger.info(f"Restored message_history: {len(message_history)}")

        # Initialize and restore the memory managers
        recent_memory = RecentMemoryManager()
        recent_memory.add_message_history(message_history)
        cl.user_session.set("recent_memory", recent_memory)

        message_history = recent_memory.get_conversation_history()
        logger.info(f"Resumed with chat history #{len(message_history)}")
        if not message_history:
            return

        # Initialize and cache point indices (no restore for resume)
        cache_point_indices = load_cache_point_indices()
        if llm_cowriter_service.prompt_cache.should_create_cache_point(cache_point_indices, message_history):
            # create cache point at the end of the message history
            new_cache_point_indices = llm_cowriter_service.prompt_cache.create_cache_point(
                history_index=len(message_history) - 1,
                cache_point_indices=cache_point_indices,
            )
            save_cache_point_indices(new_cache_point_indices)

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

        logger.info(f"User {default_user.identifier} logged in")
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

**Examples Messages:**
- If you input a todo list, LLM will help you complete the todo list
- If you input the item you want to buy, LLM will search for reviews and prices of the item
    """.format(SECTIONS="\n".join(SECTIONS)).strip()
    await cl.context.emitter.set_commands(COMMANDS)
    await cl.Message(content=welcome_message, metadata={"exclude_from_history": True}).send()
    # Initialize both memory systems
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
        RecentMemoryManager, cl.user_session.get("recent_memory"),
    )

    # Process general messages
    user_message_content = message.content

    cache_point_indices = load_cache_point_indices()
    msg = cl.Message(content="")
    if search_result:
        messages = llm_cowriter_service.build_web_search_messages(
            query=user_message_content,
            web_result=search_result,
        )
        async for chunk in llm_cowriter_service.stream_llm_response(messages):
            if chunk:
                await msg.stream_token(chunk)
    else:
        # Get recent conversation history from recent memory
        recent_history = recent_memory.get_conversation_history()

        # Build messages for ALPS writer
        # Add cache points to history
        cached_recent_history = prompt_cache_service.add_cache_points_to_messages(
            cache_point_indices,
            recent_history,
        )
        messages = llm_cowriter_service.build_alps_messages(
            message_content=user_message_content,
            recent_history=cached_recent_history,
            text_context=text_context,
            image_context=image_context,
        )
        async for chunk in llm_cowriter_service.stream_llm_response(messages):
            if chunk:
                await msg.stream_token(chunk)
    await msg.send()

    # Add AI response to both memory systems
    recent_memory.add_ai_message(user_message_content, msg.content)

    cl.user_session.set("recent_memory", recent_memory)

    # Determine if a cache point should be created based on the entire message history
    new_recent_history = recent_memory.get_conversation_history()
    if prompt_cache_service.should_create_cache_point(cache_point_indices, new_recent_history):
        # Create cache point at the end of the message history
        new_cache_point_indices = prompt_cache_service.create_cache_point(
            history_index=len(new_recent_history) - 1,
            cache_point_indices=cache_point_indices,
        )
        save_cache_point_indices(new_cache_point_indices)


def load_cache_point_indices() -> List[int]:
    return cl.user_session.get("cache_point_indices", [])


def save_cache_point_indices(cache_point_indices: List[int]) -> None:
    cl.user_session.set("cache_point_indices", cache_point_indices or [])
