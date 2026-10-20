"""Load explicitly supported provider settings without exporting unrelated secrets."""
import os
from pathlib import Path

KEYS = ("OPENALEX_API_KEY", "SERPER_API_KEY", "JINA_API_KEY", "OPENAI_API_KEY")


def load_provider_env():
    from dotenv import dotenv_values
    root = Path(__file__).resolve().parents[2]
    explicit = os.getenv("IDEATION_ENV_FILE")
    paths = ([Path(explicit)] if explicit else []) + [root / ".env", root / "ideation" / ".env", Path.home() / ".config/ideation/providers.env"]
    for path in paths:
        if path.is_file():
            values = dotenv_values(path, interpolate=False)
            for key in KEYS:
                if values.get(key) and not os.environ.get(key):
                    os.environ[key] = values[key]
