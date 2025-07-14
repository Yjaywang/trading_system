from google import genai
import os
import httpx
import json
from pydantic import BaseModel
from ..middleware.error_decorators import core_logger
from typing import Optional


class TraderInsights(BaseModel):
    foreign: str
    domestic: str
    top_ten: Optional[str] = None


class TradingAnalysis(BaseModel):
    future: TraderInsights
    option: TraderInsights
    overall: str


client = genai.Client(api_key=os.getenv("GEMINI_API_KEY", ""))


def analyze_trading_report(doc_url: str, system_prompt) -> TradingAnalysis | None:
    try:
        response = httpx.get(doc_url, timeout=30)
        response.raise_for_status()  # 4xx or 5xx error handling
        doc_data = response.content

    except httpx.RequestError as e:
        core_logger.error(f"can not download PDF file: {e}")
        return None

    try:
        prompt = ""
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                genai.types.Part.from_bytes(
                    data=doc_data,
                    mime_type="application/pdf",
                ),
                prompt,
            ],
            config=genai.types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=TradingAnalysis,
                thinking_config=genai.types.ThinkingConfig(
                    thinking_budget=-1
                ),  # turn on dynamic thinking
                system_instruction=system_prompt,
            ),
        )
        analysis_data = TradingAnalysis.model_validate_json(response.text)
        return analysis_data.model_dump()

    except Exception as e:
        core_logger.error(f"API call or data parsing error: {e}")
        return None
