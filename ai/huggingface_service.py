import time

from huggingface_hub import InferenceClient

from config.settings import settings
from utils.logger import get_logger


class HuggingFaceService:
    def __init__(self):
        self.logger = get_logger(__name__)
        self.model = settings.AI_MODEL

    def generate(self, prompt):
        if not settings.HF_TOKEN:
            raise RuntimeError(
                "HF_TOKEN is not configured. Set it in the backend environment."
            )

        client = InferenceClient(
            api_key=settings.HF_TOKEN,
            provider="auto",
        )
        last_error = None

        for attempt in range(settings.MAX_RETRIES + 1):
            start_time = time.perf_counter()
            try:
                self.logger.info(
                    "Hugging Face request attempt %d",
                    attempt + 1,
                )
                response = client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=settings.MAX_TOKENS,
                    temperature=settings.TEMPERATURE,
                )
                answer = response.choices[0].message.content
                if not isinstance(answer, str) or not answer.strip():
                    raise RuntimeError(
                        "The Hugging Face API returned an empty response."
                    )

                self.logger.info(
                    "Hugging Face request succeeded in %.3f seconds",
                    time.perf_counter() - start_time,
                )
                return answer
            except Exception as error:
                last_error = error
                self.logger.exception("Hugging Face request failed.")
                if attempt < settings.MAX_RETRIES:
                    time.sleep(settings.RETRY_DELAY)

        raise RuntimeError(
            f"Hugging Face generation failed after "
            f"{settings.MAX_RETRIES + 1} attempts: {last_error}"
        ) from last_error
