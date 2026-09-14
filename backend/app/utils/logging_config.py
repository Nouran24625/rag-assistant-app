import logging
import sys


def setup_logging(log_level: str = "INFO") -> None:
    """Configure application logging."""
    # TODO: Implement structured / standardized logging configuration
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
