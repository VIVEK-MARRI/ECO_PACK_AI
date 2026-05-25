import os
import logging
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

class GeminiProvider:
    def __init__(self, api_key=None, model_name="gemini-1.5-pro"):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = model_name
        self.client = genai.Client(api_key=self.api_key) if self.api_key else None
        if not self.client:
            logger.warning("GEMINI_API_KEY is not set; using fallback LLM responses.")

    def generate_structured(self, prompt: str, response_schema) -> dict:
        """Generates a structured response matching the Pydantic schema."""
        if not self.api_key:
            raise ValueError("Gemini API key not found.")
            
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=response_schema,
                temperature=0.2,
            ),
        )
        return response.parsed
