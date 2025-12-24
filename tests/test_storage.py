"""Unit tests for the StorageService."""

from datetime import datetime
from pathlib import Path

import pytest

from app.models.weather import WeatherData
from app.services.storage import LocalFileStorage, StorageService


class TestLocalFileStorage:
    """Tests for LocalFileStorage class."""

    def test_generate_filename(self, temp_data_dir):
        """Test filename generation format."""
        storage = LocalFileStorage(base_path=temp_data_dir)
        timestamp = datetime(2024, 1, 15, 12, 30, 45)
        
        filename = storage._generate_filename("London", timestamp)
        
        assert filename == "london_20240115_123045.json"

    def test_generate_filename_with_spaces(self, temp_data_dir):
        """Test filename generation with city name containing spaces."""
        storage = LocalFileStorage(base_path=temp_data_dir)
        timestamp = datetime(2024, 1, 15, 12, 0, 0)
        
        filename = storage._generate_filename("New York", timestamp)
        
        assert filename == "new_york_20240115_120000.json"

    @pytest.mark.asyncio
    async def test_save_creates_file(self, temp_data_dir, sample_weather_data):
        """Test saving weather data creates a file."""
        storage = LocalFileStorage(base_path=temp_data_dir)
        
        file_path = await storage.save(sample_weather_data)
        
        assert Path(file_path).exists()
        assert file_path.endswith(".json")

    @pytest.mark.asyncio
    async def test_save_content_is_valid_json(self, temp_data_dir, sample_weather_data):
        """Test saved file contains valid JSON."""
        storage = LocalFileStorage(base_path=temp_data_dir)
        
        file_path = await storage.save(sample_weather_data)
        
        content = Path(file_path).read_text()
        assert "London" in content
        assert "temperature" in content

    @pytest.mark.asyncio
    async def test_load_existing_file(self, temp_data_dir, sample_weather_data):
        """Test loading an existing weather file."""
        storage = LocalFileStorage(base_path=temp_data_dir)
        file_path = await storage.save(sample_weather_data)
        
        loaded_data = await storage.load(file_path)
        
        assert loaded_data is not None
        assert loaded_data.city == sample_weather_data.city
        assert loaded_data.temperature == sample_weather_data.temperature

    @pytest.mark.asyncio
    async def test_load_nonexistent_file(self, temp_data_dir):
        """Test loading a nonexistent file returns None."""
        storage = LocalFileStorage(base_path=temp_data_dir)
        
        loaded_data = await storage.load("/nonexistent/path/file.json")
        
        assert loaded_data is None


class TestStorageService:
    """Tests for StorageService class."""

    @pytest.mark.asyncio
    async def test_save_weather_data(self, storage_service, sample_weather_data):
        """Test saving weather data through service."""
        file_path = await storage_service.save_weather_data(sample_weather_data)
        
        assert file_path is not None
        assert Path(file_path).exists()

    @pytest.mark.asyncio
    async def test_load_weather_data(self, storage_service, sample_weather_data):
        """Test loading weather data through service."""
        file_path = await storage_service.save_weather_data(sample_weather_data)
        
        loaded_data = await storage_service.load_weather_data(file_path)
        
        assert loaded_data is not None
        assert loaded_data.city == sample_weather_data.city

    @pytest.mark.asyncio
    async def test_load_nonexistent_returns_none(self, storage_service):
        """Test loading nonexistent file returns None."""
        result = await storage_service.load_weather_data("/fake/path.json")
        
        assert result is None

