"""Logging configuration."""

import io
import logging
import sys


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        # Wrap stdout in a UTF-8 TextIOWrapper so multi-byte characters
        # (e.g. em-dash in action strings) are not garbled on Windows
        # default code pages (CP1252 / CP850).
        try:
            utf8_stdout = io.TextIOWrapper(
                sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True
            )
        except AttributeError:
            # sys.stdout may not have .buffer in some environments (e.g. pytest capture)
            utf8_stdout = sys.stdout
        handler = logging.StreamHandler(utf8_stdout)
        handler.setFormatter(
            logging.Formatter("%(asctime)s [%(name)s] %(levelname)s: %(message)s")
        )
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger
