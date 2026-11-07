"""Tests that main() only advances the sync state when every file succeeded."""

from unittest.mock import MagicMock, patch

import pytest

import main as sync_main

FILES = [{"id": "1", "name": "a.txt"}, {"id": "2", "name": "b.txt"}]


@pytest.fixture
def patched(monkeypatch: pytest.MonkeyPatch):
    """Patch every external dependency of main() and return the save_state mock."""
    monkeypatch.setenv("AZURE_STORAGE_CONNECTION_STRING", "x")
    monkeypatch.setenv("AZURE_CONTAINER", "c")
    monkeypatch.setenv("FOLDER_ID", "f")
    monkeypatch.setenv("INCREMENTAL_SYNC_ENABLED", "true")
    save = MagicMock()
    with (
        patch.object(sync_main, "get_credentials"),
        patch.object(sync_main, "build"),
        patch.object(sync_main, "is_folder", return_value=True),
        patch.object(sync_main, "get_folder_files", return_value=FILES),
        patch.object(sync_main, "is_file_updated", return_value=True),
        patch.object(sync_main, "save_state", save),
    ):
        yield save


def test_state_saved_when_all_files_succeed(patched: MagicMock):
    """A fully successful run advances the sync timestamp."""
    with patch.object(sync_main, "sync_file", return_value=True):
        assert sync_main.main() == 0
    patched.assert_called_once()


def test_state_kept_when_any_file_fails(patched: MagicMock):
    """A partial failure keeps the old timestamp so failed files are retried."""
    with patch.object(sync_main, "sync_file", side_effect=[True, False]):
        assert sync_main.main() == 1
    patched.assert_not_called()
