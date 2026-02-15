"""Unit tests for the state module."""

import json
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

import state


@pytest.fixture
def temp_state_file(tmp_path: Path):
    """Create a temporary state file for testing."""
    state_file = tmp_path / "sync_state.json"
    with patch.object(state, "STATE_FILE", state_file):
        yield state_file


class TestLoadState:
    """Tests for the load_state function."""

    def test_returns_empty_dict_when_file_missing(self, temp_state_file: Path):
        """Test that missing state file returns empty dict."""
        with patch.object(state, "STATE_FILE", temp_state_file):
            result = state.load_state()
            assert result == {}

    def test_loads_valid_json(self, temp_state_file: Path):
        """Test loading valid JSON state file."""
        test_data = {"last_sync_time": "2024-01-15T10:30:00"}
        temp_state_file.write_text(json.dumps(test_data))

        with patch.object(state, "STATE_FILE", temp_state_file):
            result = state.load_state()
            assert result == test_data

    def test_returns_empty_dict_on_invalid_json(self, temp_state_file: Path):
        """Test that invalid JSON returns empty dict."""
        temp_state_file.write_text("not valid json")

        with patch.object(state, "STATE_FILE", temp_state_file):
            result = state.load_state()
            assert result == {}


class TestSaveState:
    """Tests for the save_state function."""

    def test_saves_sync_time(self, temp_state_file: Path):
        """Test saving sync time to state file."""
        sync_time = datetime(2024, 1, 15, 10, 30, 0)

        with patch.object(state, "STATE_FILE", temp_state_file):
            result = state.save_state(sync_time)
            assert result is True

            # Verify file contents
            saved_data = json.loads(temp_state_file.read_text())
            assert saved_data["last_sync_time"] == "2024-01-15T10:30:00"

    def test_preserves_existing_state(self, temp_state_file: Path):
        """Test that save_state preserves other state data."""
        existing_data = {"other_key": "other_value"}
        temp_state_file.write_text(json.dumps(existing_data))

        sync_time = datetime(2024, 1, 15, 10, 30, 0)

        with patch.object(state, "STATE_FILE", temp_state_file):
            state.save_state(sync_time)

            saved_data = json.loads(temp_state_file.read_text())
            assert saved_data["other_key"] == "other_value"
            assert "last_sync_time" in saved_data


class TestGetLastSyncTime:
    """Tests for the get_last_sync_time function."""

    def test_returns_datetime_min_when_no_state(self, temp_state_file: Path):
        """Test that missing state returns datetime.min."""
        with patch.object(state, "STATE_FILE", temp_state_file):
            result = state.get_last_sync_time()
            assert result == datetime.min

    def test_returns_datetime_min_when_no_sync_time(self, temp_state_file: Path):
        """Test that missing last_sync_time returns datetime.min."""
        temp_state_file.write_text(json.dumps({"other_key": "value"}))

        with patch.object(state, "STATE_FILE", temp_state_file):
            result = state.get_last_sync_time()
            assert result == datetime.min

    def test_parses_valid_iso_timestamp(self, temp_state_file: Path):
        """Test parsing valid ISO timestamp."""
        test_data = {"last_sync_time": "2024-01-15T10:30:00"}
        temp_state_file.write_text(json.dumps(test_data))

        with patch.object(state, "STATE_FILE", temp_state_file):
            result = state.get_last_sync_time()
            assert result == datetime(2024, 1, 15, 10, 30, 0)

    def test_returns_datetime_min_for_invalid_timestamp(self, temp_state_file: Path):
        """Test that invalid timestamp returns datetime.min."""
        test_data = {"last_sync_time": "not-a-valid-timestamp"}
        temp_state_file.write_text(json.dumps(test_data))

        with patch.object(state, "STATE_FILE", temp_state_file):
            result = state.get_last_sync_time()
            assert result == datetime.min


class TestClearState:
    """Tests for the clear_state function."""

    def test_removes_state_file(self, temp_state_file: Path):
        """Test that clear_state removes the state file."""
        temp_state_file.write_text(json.dumps({"last_sync_time": "2024-01-15T10:30:00"}))

        with patch.object(state, "STATE_FILE", temp_state_file):
            result = state.clear_state()
            assert result is True
            assert not temp_state_file.exists()

    def test_succeeds_when_file_missing(self, temp_state_file: Path):
        """Test that clear_state succeeds when file doesn't exist."""
        with patch.object(state, "STATE_FILE", temp_state_file):
            result = state.clear_state()
            assert result is True


class TestRoundTrip:
    """Integration tests for state persistence."""

    def test_save_and_load_round_trip(self, temp_state_file: Path):
        """Test saving and loading state round trip."""
        original_time = datetime(2024, 6, 15, 14, 30, 45)

        with patch.object(state, "STATE_FILE", temp_state_file):
            # Save state
            state.save_state(original_time)

            # Load state
            loaded_time = state.get_last_sync_time()

            # Compare (ignore microseconds)
            assert loaded_time.replace(microsecond=0) == original_time.replace(microsecond=0)
