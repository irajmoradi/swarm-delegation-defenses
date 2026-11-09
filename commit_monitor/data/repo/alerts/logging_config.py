"""Logging setup shared by the services."""
import logging

DEFAULT_FORMAT = "%(asctime)s %(name)s %(levelname)s %(message)s"


def setup_logging(level="INFO", fmt=DEFAULT_FORMAT):
    logging.basicConfig(level=getattr(logging, level), format=fmt)
    return logging.getLogger()
