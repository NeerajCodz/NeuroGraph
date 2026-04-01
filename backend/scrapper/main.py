"""Compatibility entrypoint for `uvicorn scrapper.main:app`."""

from src.main import app

__all__ = ["app"]

