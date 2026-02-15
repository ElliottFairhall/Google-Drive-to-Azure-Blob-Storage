"""Unit tests for the incremental_sync module."""

from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

from incremental_sync import (
    get_files_to_sync,
    get_local_modified_time,
    is_file_updated,
)


class TestIsFileUpdated:
    """Tests for the is_file_updated function."""

    def test_returns_true_when_file_modified_after_sync(self):
        """Test that modified file returns True."""
        mock_service = MagicMock()
        mock_service.files().get().execute.return_value = {"modifiedTime": "2024-01-20T10:00:00Z"}

        last_sync = datetime(2024, 1, 15, 10, 0, 0)
        result = is_file_updated(mock_service, "file123", last_sync)

        assert result is True

    def test_returns_false_when_file_not_modified(self):
        """Test that unmodified file returns False."""
        mock_service = MagicMock()
        mock_service.files().get().execute.return_value = {"modifiedTime": "2024-01-10T10:00:00Z"}

        last_sync = datetime(2024, 1, 15, 10, 0, 0)
        result = is_file_updated(mock_service, "file123", last_sync)

        assert result is False

    def test_returns_false_on_api_error(self):
        """Test that API error returns False."""
        from googleapiclient.errors import HttpError

        mock_service = MagicMock()
        mock_service.files().get().execute.side_effect = HttpError(
            resp=MagicMock(status=404), content=b"Not found"
        )

        last_sync = datetime(2024, 1, 15, 10, 0, 0)
        result = is_file_updated(mock_service, "file123", last_sync)

        assert result is False

    def test_returns_false_when_modified_time_missing(self):
        """Test that missing modifiedTime returns False."""
        mock_service = MagicMock()
        mock_service.files().get().execute.return_value = {}

        last_sync = datetime(2024, 1, 15, 10, 0, 0)
        result = is_file_updated(mock_service, "file123", last_sync)

        assert result is False

    def test_handles_timezone_offset_format(self):
        """Test handling of timezone offset format."""
        mock_service = MagicMock()
        mock_service.files().get().execute.return_value = {
            "modifiedTime": "2024-01-20T10:00:00+00:00"
        }

        last_sync = datetime(2024, 1, 15, 10, 0, 0)
        result = is_file_updated(mock_service, "file123", last_sync)

        assert result is True


class TestGetLocalModifiedTime:
    """Tests for the get_local_modified_time function."""

    def test_returns_datetime_min_for_nonexistent_file(self):
        """Test that nonexistent file returns datetime.min."""
        result = get_local_modified_time("/nonexistent/path/file.txt")
        assert result == datetime.min

    def test_returns_modification_time_for_existing_file(self, tmp_path: Path):
        """Test that existing file returns its modification time."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        result = get_local_modified_time(test_file)

        # Should be a recent timestamp (within last minute)
        assert result > datetime.min
        time_diff = abs((datetime.now() - result).total_seconds())
        assert time_diff < 60  # Within 60 seconds

    def test_accepts_string_path(self, tmp_path: Path):
        """Test that function accepts string path."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        result = get_local_modified_time(str(test_file))

        assert result > datetime.min


class TestGetFilesToSync:
    """Tests for the get_files_to_sync function."""

    def test_returns_empty_list_when_no_files_updated(self):
        """Test that no updated files returns empty list."""
        mock_service = MagicMock()
        mock_service.files().get().execute.return_value = {"modifiedTime": "2024-01-10T10:00:00Z"}

        files = [
            {"id": "file1", "name": "test1.txt"},
            {"id": "file2", "name": "test2.txt"},
        ]
        last_sync = datetime(2024, 1, 15, 10, 0, 0)

        result = get_files_to_sync(mock_service, files, last_sync)

        assert result == []

    def test_returns_only_updated_files(self):
        """Test that only updated files are returned."""
        mock_service = MagicMock()

        # First file is old, second is new
        def mock_get_execute(*args, **kwargs):
            file_id = mock_service.files().get.call_args.kwargs.get(
                "fileId"
            ) or mock_service.files().get.call_args[1].get("fileId")
            if file_id == "file1":
                return {"modifiedTime": "2024-01-10T10:00:00Z"}  # Old
            return {"modifiedTime": "2024-01-20T10:00:00Z"}  # New

        mock_service.files().get().execute.side_effect = mock_get_execute

        files = [
            {"id": "file1", "name": "old.txt"},
            {"id": "file2", "name": "new.txt"},
        ]
        last_sync = datetime(2024, 1, 15, 10, 0, 0)

        with patch("incremental_sync.is_file_updated") as mock_is_updated:
            mock_is_updated.side_effect = [False, True]
            result = get_files_to_sync(mock_service, files, last_sync)

        assert len(result) == 1
        assert result[0]["name"] == "new.txt"

    def test_skips_files_without_id(self):
        """Test that files without ID are skipped."""
        mock_service = MagicMock()

        files = [
            {"name": "no_id.txt"},  # Missing ID
            {"id": "file1", "name": "has_id.txt"},
        ]
        last_sync = datetime(2024, 1, 15, 10, 0, 0)

        with patch("incremental_sync.is_file_updated") as mock_is_updated:
            mock_is_updated.return_value = True
            result = get_files_to_sync(mock_service, files, last_sync)

        # Should only process the file with ID
        assert mock_is_updated.call_count == 1
