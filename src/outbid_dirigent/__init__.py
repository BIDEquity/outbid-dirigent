"""Outbid Dirigent – Headless autonomous coding agent controller."""

try:
    from importlib.metadata import version
    __version__ = version("outbid-dirigent")
except Exception:
    # Fallback for development/testing when package isn't installed
    __version__ = "dev"
