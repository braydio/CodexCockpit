import logging
import os
from typing import Optional

_configured = False


def configure_logging(level: Optional[str] = None) -> None:
  """
  Configure a simple console logger for the backend.

  Uvicorn brings its own logger, but we want consistent formatting and a single
  place to tune verbosity. Calling this repeatedly is safe.
  """
  global _configured
  if _configured:
    return

  level_name = level or os.getenv("LOG_LEVEL", "INFO").upper()
  log_level = logging.getLevelName(level_name)
  if isinstance(log_level, str):
    log_level = logging.INFO

  formatter = logging.Formatter(
      fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
      datefmt="%Y-%m-%d %H:%M:%S",
  )

  handler = logging.StreamHandler()
  handler.setFormatter(formatter)

  root = logging.getLogger()
  root.setLevel(log_level)
  root.addHandler(handler)

  # Align uvicorn loggers with our level/format for consistency.
  for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    if not logger.handlers:
      logger.addHandler(handler)

  # Reduce noisy deps while keeping error visibility.
  logging.getLogger("httpx").setLevel(logging.WARNING)
  logging.getLogger("asyncio").setLevel(logging.INFO)

  _configured = True
