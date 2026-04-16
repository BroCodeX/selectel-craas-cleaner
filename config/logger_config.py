from loguru import logger
import sys

def setup_logging():
    logger.remove()
    try:
        logger.level("HEADER", no=21, color="<magenta><bold>")
    except ValueError:
        pass  # already registered (e.g. multiple test modules call setup_logging)
    logger.add(
        sys.stderr,
        format="<level>{time:HH:mm:ss}</level> | <level>{message}</level>",
        colorize=True
    )
