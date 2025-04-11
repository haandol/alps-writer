import os

from src.utils.logger import logger


def load_alps_context() -> str:
    """Read the ALPS.md file and return it as a context."""
    try:
        alps_path = os.path.join("./templates", "ALPS.md")
        with open(alps_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        logger.error("Failed to load ALPS context", error=e)
        raise e
