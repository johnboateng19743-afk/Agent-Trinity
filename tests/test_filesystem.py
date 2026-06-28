"""
Trinity Tests — File System Skill Tests.
"""

import pytest
import tempfile
from pathlib import Path
from trinity.skills.filesystem.reader import FileSystemReader
from trinity.skills.filesystem.writer import FileSystemWriter
from trinity.skills.filesystem.deleter import FileSystemDeleter
from trinity.skills.filesystem.searcher import FileSystemSearcher


@pytest.fixture
def config():
    return {"trinity": {"data_dir": "~/.trinity"}}


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


class TestFileSystemReader:
    """Tests for file reading operations."""

    @pytest.mark.asyncio
    async def test_list_dir(self, config, temp_dir):
        # Create test files
        (temp_dir / "test.txt").write_text("hello")
        (temp_dir / "subdir").mkdir()

        reader = FileSystemReader(config)
        result = await reader.execute({
            "raw_text": f"what's in {temp_dir}",
            "path": str(temp_dir),
        })

        assert result.success
        assert "test.txt" in result.response
        assert "subdir" in result.response

    @pytest.mark.asyncio
    async def test_read_text_file(self, config, temp_dir):
        test_file = temp_dir / "hello.txt"
        test_file.write_text("Hello, Trinity!")

        reader = FileSystemReader(config)
        result = await reader.execute({
            "raw_text": f"read {test_file}",
            "path": str(test_file),
        })

        assert result.success
        assert "Hello, Trinity!" in result.response

    @pytest.mark.asyncio
    async def test_read_nonexistent_file(self, config):
        reader = FileSystemReader(config)
        result = await reader.execute({
            "raw_text": "read nonexistent_file_12345.txt",
            "path": "nonexistent_file_12345.txt",
        })

        assert not result.success

    @pytest.mark.asyncio
    async def test_list_nonexistent_dir(self, config):
        reader = FileSystemReader(config)
        result = await reader.execute({
            "raw_text": "list /nonexistent_dir_12345",
            "path": "/nonexistent_dir_12345",
        })

        assert not result.success


class TestFileSystemWriter:
    """Tests for file writing operations."""

    @pytest.mark.asyncio
    async def test_create_file(self, config, temp_dir):
        test_file = temp_dir / "new_file.txt"
        writer = FileSystemWriter(config)
        result = await writer.create_file({
            "raw_text": f"create {test_file}",
            "path": str(test_file),
            "content": "Created by Trinity!",
        })

        assert result.success
        assert test_file.exists()
        assert test_file.read_text() == "Created by Trinity!"

    @pytest.mark.asyncio
    async def test_create_dir(self, config, temp_dir):
        test_dir = temp_dir / "new_folder"
        writer = FileSystemWriter(config)
        result = await writer.create_dir({
            "raw_text": f"create {test_dir}",
            "path": str(test_dir),
        })

        assert result.success
        assert test_dir.is_dir()

    @pytest.mark.asyncio
    async def test_edit_file(self, config, temp_dir):
        test_file = temp_dir / "edit_me.txt"
        test_file.write_text("Hello World")

        writer = FileSystemWriter(config)
        result = await writer.edit_file({
            "raw_text": f"edit {test_file}",
            "path": str(test_file),
            "find": "World",
            "replace": "Trinity",
        })

        assert result.success
        assert test_file.read_text() == "Hello Trinity"
        # Backup should exist
        assert test_file.with_suffix(test_file.suffix + ".trinity-backup").exists()


class TestFileSystemSearcher:
    """Tests for file search operations."""

    def test_matches_type(self, config):
        searcher = FileSystemSearcher(config)
        assert searcher._matches_type(Path("test.pdf"), "pdf")
        assert searcher._matches_type(Path("photo.jpg"), "image")
        assert not searcher._matches_type(Path("test.pdf"), "image")

    def test_format_size(self, config):
        reader = FileSystemReader(config)
        assert "B" in reader._format_size(100)
        assert "KB" in reader._format_size(2048)
        assert "MB" in reader._format_size(5 * 1024 * 1024)
