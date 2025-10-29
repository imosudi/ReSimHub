# utils/logger.py
import logging
import os
from logging.handlers import RotatingFileHandler

# Define log directory
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

# Define log file
LOG_FILE = os.path.join(LOG_DIR, "resimhub.log")

# Logging format
LOG_FORMAT = (
    "%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s"
)

# Create handlers
console_handler = logging.StreamHandler()
file_handler = RotatingFileHandler(LOG_FILE, maxBytes=2_000_000, backupCount=5)

# Define formatter
formatter = logging.Formatter(LOG_FORMAT)
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

# Create logger
logger = logging.getLogger("ReSimHub")
logger.setLevel(logging.DEBUG)  # change to INFO in production
logger.addHandler(console_handler)
logger.addHandler(file_handler)

# Optional utility for modules
def get_logger(name: str):
    """Return a module-specific logger instance."""
    return logger.getChild(name)
