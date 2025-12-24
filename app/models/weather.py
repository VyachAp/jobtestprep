"""Pydantic models for weather data."""

from datetime import datetime

from pydantic import BaseModel, Field


class WeatherData(BaseModel):
    """Core weather data from the API."""

    city: str
    country: str
    temperature: float = Field(description="Temperature in Celsius")
    feels_like: float = Field(description="Feels like temperature in Celsius")
    humidity: int = Field(description="Humidity percentage")
    pressure: int = Field(description="Atmospheric pressure in hPa")
    wind_speed: float = Field(description="Wind speed in m/s")
    description: str = Field(description="Weather condition description")
    icon: str = Field(description="Weather icon code")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class WeatherResponse(BaseModel):
    """API response wrapper for weather data."""

    data: WeatherData
    cached: bool = Field(default=False, description="Whether data was served from cache")
    file_path: str | None = Field(default=None, description="Storage path for the data")

