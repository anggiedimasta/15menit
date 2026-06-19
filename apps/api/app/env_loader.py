"""Load root `.env` for local API development."""

from pathlib import Path

from dotenv import load_dotenv

_REPO_ROOT = Path(__file__).resolve().parents[3]


def load_root_env() -> None:
    load_dotenv(_REPO_ROOT / ".env", override=False)
