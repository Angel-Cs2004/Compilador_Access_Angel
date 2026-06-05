import os
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
LOCAL_ENV_PATH = ROOT_DIR / ".env"


def load_local_env(path: Path = LOCAL_ENV_PATH) -> None:
    if not path.is_file():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def get_groq_api_key() -> str:
    load_local_env()
    return os.getenv("GROQ_API_KEY", "").strip()
