"""
Gemini LLM Manager with Mock Routing for Excel Mock Interviewer.
Provides real or mock LLM prompts/responses based on settings.USE_MOCK_LLM.
"""

import json
import logging
from typing import Dict, Any, Optional
import google.generativeai as genai

from settings import settings
from prompts import (
    SYSTEM_PROMPT, INTERVIEWER_PROMPT, EVALUATOR_PROMPT,
    FEEDBACK_PROMPT, SUMMARY_PROMPT
)
from llm_mock_manager import mock_manager

logger = logging.getLogger(__name__)

class GeminiLLMManager:
    """Routes to Gemini API or mock LLM manager based on settings."""

    def __init__(self):
        if not settings.USE_MOCK_LLM:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self.model_name = settings.LLM_MODEL
            self.temperature = settings.LLM_TEMPERATURE
            self.max_tokens = settings.MAX_TOKENS

            generation_config = genai.types.GenerationConfig(
                temperature=self.temperature,
                max_output_tokens=self.max_tokens,
            )
            self.model = genai.GenerativeModel(
                model_name=self.model_name,
                generation_config=generation_config,
                system_instruction=SYSTEM_PROMPT
            )

    async def _call_gemini(self, prompt: str, temperature: Optional[float] = None) -> str:
        try:
            if temperature is not None:
                generation_config = genai.types.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=self.max_tokens,
                )
                model = genai.GenerativeModel(
                    model_name=self.model_name,
                    generation_config=generation_config,
                    system_instruction=SYSTEM_PROMPT
                )
            else:
                model = self.model

            response = model.generate_content(prompt)
            return response.text.strip()

        except Exception as e:
            logger.error(f"Gemini API call failed: {e}")
            raise Exception(f"Failed to get Gemini response: {str(e)}")

    async def get_interviewer_response(self, context: Dict[str, Any]) -> str:
        if settings.USE_MOCK_LLM:
            return await mock_manager.mock_interviewer_response(context)
        prompt = INTERVIEWER_PROMPT.format(**context)
        return await self._call_gemini(prompt)

    async def evaluate_answer(self, evaluation_data: Dict[str, Any]) -> Dict[str, Any]:
        if settings.USE_MOCK_LLM:
            return await mock_manager.mock_evaluate_answer(evaluation_data)
        prompt = EVALUATOR_PROMPT.format(**evaluation_data)
        json_instruction = "\n\nIMPORTANT: Respond with ONLY valid JSON in the format specified."
        prompt += json_instruction
        response = await self._call_gemini(prompt, temperature=0.1)
        try:
            response_clean = response.strip()
            if response_clean.startswith('```'):
                response_clean = response_clean[7:]
            if response_clean.endswith('```'):
                response_clean = response_clean[:-3]
            response_clean = response_clean.strip()
            evaluation = json.loads(response_clean)
            required_fields = ['accuracy_score', 'explanation_score', 'efficiency_score',
                               'overall_score', 'feedback', 'strengths', 'improvement_areas']
            for field in required_fields:
                if field not in evaluation:
                    raise ValueError(f"Missing required field: {field}")
            return evaluation
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse evaluation response: {e}")
            logger.error(f"Raw response: {response}")
            return {
                "accuracy_score": 0.5,
                "explanation_score": 0.5,
                "efficiency_score": 0.5,
                "overall_score": 5.0,
                "feedback": "I had trouble evaluating this response. Please try again with more specific Excel details.",
                "strengths": ["Attempted the question"],
                "improvement_areas": ["Could provide more detail", "Be more specific about Excel features"]
            }

    async def generate_feedback(self, feedback_data: Dict[str, Any]) -> str:
        if settings.USE_MOCK_LLM:
            return await mock_manager.mock_generate_feedback(feedback_data)
        prompt = FEEDBACK_PROMPT.format(**feedback_data)
        return await self._call_gemini(prompt)

    async def generate_summary(self, summary_data: Dict[str, Any]) -> str:
        if settings.USE_MOCK_LLM:
            return await mock_manager.mock_generate_summary(summary_data)
        prompt = SUMMARY_PROMPT.format(**summary_data)
        return await self._call_gemini(prompt)

    async def chat_response(self, message: str, context: str = "") -> str:
        if settings.USE_MOCK_LLM:
            return await mock_manager.mock_chat_response(message, context)
        full_prompt = f"Context: {context}\n\nUser message: {message}\n\nProvide a helpful, professional response as an Excel interviewer."
        return await self._call_gemini(full_prompt)