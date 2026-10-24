"""Context managers for logging operations and atomic file writing."""

from contextlib import contextmanager
import logging
from pathlib import Path
from time import perf_counter
from typing import IO, Iterator

from experiment_importer.exceptions import DataExportError

logger = logging.getLogger(__name__)


@contextmanager
def logged_operation(operation: str) -> Iterator[None]:
    """Context manager to measure and log duration of operations with error logging."""
    logger.info("%s started", operation)
    start_time = perf_counter()
    try:
        yield
    except Exception:
        logger.exception("%s failed", operation)
        raise
    else:
        elapsed = perf_counter() - start_time
        logger.info("%s finished successfully in %.6f s", operation, elapsed)


@contextmanager
def atomic_write(
    target_path: Path,
    mode: str = "w",
    encoding: str = "utf-8",
) -> Iterator[IO[str]]:
    """Context manager providing atomic file writing via temporary file replacement.

    If an error occurs while writing inside the context, the temporary file
    is cleaned up and the original target file remains untouched.
    """
    target_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = target_path.with_suffix(target_path.suffix + ".tmp")

    file: IO[str] | None = None
    try:
        file = temp_path.open(mode, encoding=encoding)
        yield file
        file.flush()
        file.close()
        file = None
        temp_path.replace(target_path)
    except Exception as error:
        if file is not None and not file.closed:
            file.close()
        temp_path.unlink(missing_ok=True)
        raise DataExportError(f"Atomic write to '{target_path}' failed: {error}") from error
