import sys
from pathlib import Path
from typing import Literal

from loguru import logger


def setup_logging(
    level: Literal['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'] = 'INFO',
    log_file: Path | None = None,
    rotation: str = '10 MB',
    retention: str = '7 days',
):
    """Configure loguru logger with console and optional file output.

    Args:
        level: Log level for console output (DEBUG, INFO, WARNING, ERROR).
        log_file: Optional path for file logging.
        rotation: File rotation size or time (e.g., "10 MB", "1 day").
        retention: How long to keep rotated files.
    """

    logger.remove()

    logger.add(
        sys.stderr,
        level=level,
        format=(
            '<green>{time:HH:mm:ss}</green> | '
            '<level>{level: <8}</level> | '
            '<cyan>{name}</cyan>:<cyan>{line}</cyan> - '
            '<level>{message}</level>'
        ),
        colorize=True,
    )

    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        logger.add(
            log_file,
            level=level,
            format='{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{line} - {message}',
            rotation=rotation,
            retention=retention,
            encoding='utf-8',
        )
