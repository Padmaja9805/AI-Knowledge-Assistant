import os

from dotenv import load_dotenv


load_dotenv()


class Settings:

    HF_TOKEN = os.getenv(
        "HF_TOKEN"
    )

    AI_MODEL = os.getenv(
        "AI_MODEL",
        "openai/gpt-oss-120b"
    )

    MAX_TOKENS = int(
        os.getenv(
            "MAX_TOKENS",
            "512"
        )
    )

    TEMPERATURE = float(
        os.getenv(
            "TEMPERATURE",
            "0.2"
        )
    )

    RAG_TOP_K = int(
        os.getenv(
            "RAG_TOP_K",
            "8"
        )
    )

    RAG_MIN_SCORE = float(
        os.getenv(
            "RAG_MIN_SCORE",
            "0.45"
        )
    )

    MAX_RETRIES = int(
    os.getenv(
        "MAX_RETRIES",
        "2"
    )
    )

    RETRY_DELAY = float(
        os.getenv(
            "RETRY_DELAY",
            "1"
        )
    )


settings = Settings()
