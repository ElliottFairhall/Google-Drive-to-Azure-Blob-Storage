"""Sync state persistence for incremental synchronization.

This module manages the state file that tracks the last successful
synchronization time, enabling incremental sync operations.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

STATE_FILE = Path("sync_state.json")


def load_state() -> dict[str, Any]:
    """Load the sync state from the JSON state file.

    Reads and parses the state file if it exists. Returns an empty
    dictionary if the file doesn't exist or cannot be parsed.

    Returns:
        Dictionary containing the sync state, or empty dict if unavailable.

    Example:
        >>> state = load_state()
        >>> print(state.get("last_sync_time"))
    """
    if not STATE_FILE.exists():
        return {}

    try:
        with STATE_FILE.open("r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.warning("Failed to parse state file: %s", e)
        return {}
    except OSError as e:
        logger.warning("Failed to read state file: %s", e)
        return {}


def save_state(last_sync_time: datetime) -> bool:
    """Save the last sync time to the state file.

    Updates the state file with the provided timestamp, preserving
    any other existing state data.

    Args:
        last_sync_time: The datetime of the completed sync operation.

    Returns:
        True if the state was saved successfully, False otherwise.

    Example:
        >>> from datetime import datetime
        >>> save_state(datetime.utcnow())
        True
    """
    state = load_state()
    state["last_sync_time"] = last_sync_time.isoformat()

    try:
        with STATE_FILE.open("w", encoding="utf-8") as f:
            json.dump(state, f, indent=4)
        logger.debug("Sync state saved: %s", last_sync_time.isoformat())
        return True
    except OSError as e:
        logger.error("Failed to save state: %s", e)
        return False


def get_last_sync_time() -> datetime:
    """Retrieve the last sync time as a datetime object.

    Reads the last sync time from the state file and converts it
    to a datetime object. Returns datetime.min if no valid sync
    time is found.

    Returns:
        The datetime of the last successful sync, or datetime.min
        if no previous sync has been recorded.

    Example:
        >>> last_sync = get_last_sync_time()
        >>> if last_sync > datetime.min:
        ...     print(f"Last sync: {last_sync}")
    """
    state = load_state()
    last_sync_str = state.get("last_sync_time")

    if not last_sync_str:
        return datetime.min

    try:
        return datetime.fromisoformat(last_sync_str)
    except ValueError as e:
        logger.warning("Invalid last_sync_time format: %s", e)
        return datetime.min


def clear_state() -> bool:
    """Clear the sync state file.

    Removes the state file to force a full sync on the next run.

    Returns:
        True if the state was cleared successfully, False otherwise.

    Example:
        >>> clear_state()
        True
    """
    try:
        if STATE_FILE.exists():
            STATE_FILE.unlink()
            logger.info("Sync state cleared")
        return True
    except OSError as e:
        logger.error("Failed to clear state: %s", e)
        return False
