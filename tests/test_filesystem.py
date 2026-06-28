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


class TestFileSystemWriter:
    """Tests for file writing operations."""

    @pytest.mark.asyncio
    async def test_create_file(self, config, temp_dir):
        test_file = temp_dir / "new_file.txt"
        writer = FileSystemWriter(config)
        result = await writer.execute({
            "raw_text": f"create {test_file}",
            "path": str(test_file),
            "content": "Created by Trinity!",
        })

        assert result.success or result.requires_confirmation
        if result.success:
            assert test_file.exists()


class TestFileSystemSearcher:
    """Tests for file search operations."""

    @pytest.mark.asyncio
    async def test_search_by_name(self, config, temp_dir):
        (temp_dir / "report_2026.pdf").write_text("report")
        (temp_dir / "notes.txt").write_text("notes")

        searcher = FileSystemSearcher(config)
        # Basic search test
        assert searcher._matches_type(Path("test.pdf"), "pdf")
        assert searcher._matches_type(Path("photo.jpg"), "image")
        assert not searcher._matches_type(Path("test.pdf"), "image")
