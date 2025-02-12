import logging
import sys
from pathlib import Path

def setup_logger(name: str) -> logging.Logger:
    """Configure and return a logger instance"""
    logger = logging.getLogger(name)

    if not logger.handlers:  # Avoid adding handlers multiple times
        logger.setLevel(logging.INFO)

        # Create logs directory if it doesn't exist
        log_dir = Path(__file__).parent.parent / "logs"
        log_dir.mkdir(exist_ok=True)

        # File handler with absolute path
        log_file = log_dir / "app.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(
            logging.Formatter('%(levelname)s: %(message)s')
        )

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger
