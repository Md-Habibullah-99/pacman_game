import os
import sys


def get_base_path() -> str:
    """Return the base path for bundled or source execution.

    - When frozen by PyInstaller, assets are unpacked into sys._MEIPASS.
    - When running from source, base is the project root (one level up from src).
    """
    if hasattr(sys, "_MEIPASS"):
        return sys._MEIPASS  # type: ignore[attr-defined]
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def resource_path(*parts: str) -> str:
    """Build an absolute path to bundled resources."""
    return os.path.join(get_base_path(), *parts)
