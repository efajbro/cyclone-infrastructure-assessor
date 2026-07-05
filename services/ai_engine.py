import json
from google import genai
from google.genai import types
from google.genai import errors as genai_errors
from pydantic import BaseModel, Field
from typing import Literal, Dict, Any
import tenacity
from config import Config
from PIL import Image

# Expanded Knowledge Prompt
LGED_VISION_PROMPT = """
You are a Rapid Triage Copilot for the Local Government Engineering Department (LGED), Bangladesh.
Your SOLE purpose is visual perception of post-cyclone infrastructure damage.

Analyze the provided image and strictly output the requested JSON schema.
DO NOT calculate material quantities. DO NOT estimate costs.

Few-Shot Examples:
1. Image showing cracked road surface but passable.
   -> {"damage_type": "Pavement Undercutting", "severity": "Low", "structural_notes": "Minor longitudinal cracking on wearing course.", "confidence": 0.85}
2. Image showing bridge collapsed into river.
   -> {"damage_type": "Shear Failure", "severity": "Total Collapse", "structural_notes": "Deck decoupled from piers. Complete loss of structural integrity.", "confidence": 0.98}
"""


class DamagePerception(BaseModel):
    damage_type: str
    severity: Literal["Low", "Medium", "Critical", "Total Collapse"]
    structural_notes: str
    confidence: float = Field(ge=0.0, le=1.0)


class AIEngine:
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)

    @tenacity.retry(
        stop=tenacity.stop_after_attempt(3),
        wait=tenacity.wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    def _call_gemini(self, model_name: str, image: Image.Image) -> Dict[str, Any]:
        response = self.client.models.generate_content(
            model=model_name,
            contents=[image],
            config=types.GenerateContentConfig(
                system_instruction=LGED_VISION_PROMPT,
                response_mime_type="application/json",
                response_schema=DamagePerception,
            ),
        )
        return json.loads(response.text)

    def analyze_image(self, image: Image.Image) -> Dict[str, Any]:
        try:
            # Primary Call
            result = self._call_gemini(Config.PRIMARY_MODEL, image)
            return self._validate_and_format_result(result)
        # Catch specific exceptions from google.genai
        except (genai_errors.APIError, genai_errors.ServerError) as e:
            # Fallback Route for server congestion or rate limiting
            # APIError often wraps HTTP errors, check if it's 429 or 503
            status_code = getattr(e, "code", None)
            if (
                status_code in (429, 503)
                or isinstance(e, genai_errors.ServerError)
                or "429" in str(e)
                or "503" in str(e)
            ):
                try:
                    result = self._call_gemini(Config.FALLBACK_MODEL, image)
                    return self._validate_and_format_result(result)
                except Exception as fallback_e:
                    # The fallback itself failed, which is a critical error
                    raise RuntimeError(
                        f"Primary model failed ({type(e).__name__}). Fallback model also failed: {fallback_e}"
                    )
            else:
                raise RuntimeError(f"AI Engine failed with an API error: {e}")
        except Exception as e:
            # Catch any other unexpected exceptions
            raise RuntimeError(f"AI Engine failed with an unexpected error: {e}")

    def _validate_and_format_result(self, ai_data: Dict[str, Any]) -> Dict[str, Any]:
        # Fallback if severity is not in enum
        valid_severities = ["Low", "Medium", "Critical", "Total Collapse"]
        if ai_data.get("severity") not in valid_severities:
            ai_data["severity"] = "Medium"
            ai_data[
                "structural_notes"
            ] += " [System Warning: AI provided invalid severity. Defaulted to Medium.]"
        return ai_data
