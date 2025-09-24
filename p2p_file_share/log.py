import logging
import sys

def setup_logger(
    name: str = __name__,
    level: int = logging.INFO,
) -> logging.Logger:
    """
    Configure and return a logger.
    - name: logger name (use __name__ in modules)
    - level: logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)

    # Log format
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger
