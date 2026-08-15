"""Adaptadores de scraping. Un adaptador por fuente (HTTP, Spotify, YouTube, Imágenes)."""

from scraper.adapters import http, imagenes, spotify, spotify_public, youtube

__all__ = ["http", "imagenes", "spotify", "spotify_public", "youtube"]
