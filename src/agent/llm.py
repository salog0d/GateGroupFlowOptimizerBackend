from langchain_google_genai import ChatGoogleGenerativeAI
from src.settings import Settings

settings = Settings()

class LLM:

    @staticmethod
    def instance_llm():
        """Crea una instancia configurada del modelo Gemini."""
        return ChatGoogleGenerativeAI(
            model=settings.llm_model,
            temperature=settings.llm_temperature or 0.2,
            max_output_tokens=settings.llm_max_tokens,
            timeout=settings.llm_timeout,
            max_retries=settings.llm_max_retries,
            google_api_key=settings.google_gemini_api_key,
        )