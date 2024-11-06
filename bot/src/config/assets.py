from pathlib import Path

STATIC_DIR = Path(__file__).parent.parent.parent / "static"


def get_static_path(filename: str) -> str:
    return str(STATIC_DIR / filename)
