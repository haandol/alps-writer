import os
import structlog


def setup_logger(name: str = "alps_writer") -> structlog.BoundLogger:
    """
    Setup and configure structured logger for the application.

    Args:
        name (str): Name of the logger. Defaults to "alps_writer"

    Returns:
        structlog.BoundLogger: Configured structured logger instance
    """
    # Configure processors
    processors = [
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    # Add different processors for development and production
    if os.getenv("ENVIRONMENT", "local") == "local":
        # Development: Console output in colored format
        processors.extend([
            structlog.dev.ConsoleRenderer(colors=True)
        ])
    else:
        # Production: JSON format
        processors.extend([
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer()
        ])

    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        wrapper_class=structlog.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Create logger instance
    return structlog.get_logger(name)


# Create default logger instance
logger = setup_logger()
