import os
import logging

# Service name for log records
SERVICE_NAME = "UI"

# Determine log file path. Default to app/logs/combined.log inside the container.
current_dir = os.path.dirname(__file__)
parent_dir = os.path.dirname(current_dir)  # Go up one level from app/ to backend/
log_dir = os.path.join(parent_dir, "logs")
log_file_path = os.path.join(log_dir, "combined.log")

# Ensure the logs directory exists
os.makedirs(log_dir, exist_ok=True)

# Allow override via environment variable
log_file = os.environ.get("LOG_FILE", log_file_path)

# Configure logging once
if not logging.getLogger(SERVICE_NAME).handlers:
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format='[%(asctime)s] [%(name)s] %(message)s'
    )

# Exposed logger instance
logger = logging.getLogger(SERVICE_NAME)
