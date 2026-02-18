"""Centralized configuration and environment variable loading.

Loads .env from the project root (two levels above backend/).
"""

import os
from pathlib import Path
from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_DIR.parent


def load_env():
    """Load environment variables from the project root .env file."""
    env_path = PROJECT_ROOT / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
        return True

    backend_env = BACKEND_DIR / ".env"
    if backend_env.exists():
        load_dotenv(dotenv_path=backend_env)
        return True

    return False
