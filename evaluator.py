"""
Updated Answer Evaluator for Excel Mock Interviewer.
Handles intelligent evaluation of candidate responses using Gemini API.
"""

import re
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from data_models import Question, Answer, Evaluation, QuestionDifficulty
from gemini_llm_manager import GeminiLLMManager
from settings import settings

logger = logging.getLogger(__name__)

class ExcelAnswerEvaluator:
    """Evaluates candidate answers using multiple assessment criteria."""
    
    def __init__(self, llm_manager: GeminiLLMManager):
        """Initialize evaluator with Gemini LLM manager."""
        self.llm_manager = llm_manager
        self.accuracy_weight = settings.ACCURACY_WEIGHT
        self.explanation_weight = settings.EXPLANATION_WEIGHT
        self.efficiency_weight = settings.EFFICIENCY_WEIGHT
    
    async def evaluate_answer(self, question: Question, answer: Answer) -> Evaluation:
        """Main evaluation method that combines multiple assessment approaches."""
        try:
            # 1. Keyword-based evaluation
            keyword_score = self._evaluate_keywords(question, answer.response)
            
            # 2. Formula validation (if applicable)
            formula_score = self._evaluate_formula(question, answer.response)
            
            # 3. Gemini LLM-based comprehensive evaluation
            llm_evaluation = await self._llm_evaluate(question, answer)
            
            # 4. Combine scores intelligently
            final_evaluation = self._combine_evaluations(
                question, answer, keyword_score, formula_score, llm_evaluation
            )
            
            logger.info(f"Evaluated question {question.id}: {final_evaluation.score}/10")
            return final_evaluation
            
        except Exception as e:
            logger.error(f"Evaluation failed for question {question.id}: {e}")
            return self._create_fallback_evaluation(question, answer)
    
    def _evaluate_keywords(self, question: Question, response: str) -> float:
        """Evaluate based on presence of key terms and concepts."""
        if not question.keywords:
            return 0.5  # Neutral score if no keywords defined
            
        response_lower = response.lower()
        matches = 0
        
        for keyword in question.keywords:
            # Check for exact matches and variations
            keyword_lower = keyword.lower()
            
            # Direct match
            if keyword_lower in response_lower:
                matches += 1
            # Check for formula variations (=SUM vs SUM)  
            elif keyword_lower.startswith('=') and keyword_lower[1:] in response_lower:
                matches += 1
            elif not keyword_lower.startswith('=') and f"={keyword_lower}" in response_lower:
                matches += 1
        
        # Score based on percentage of keywords found
        keyword_score = min(matches / len(question.keywords), 1.0)
        
        # Bonus for comprehensive answers
        if keyword_score > 0.8 and len(response.split()) > 10:
            keyword_score = min(keyword_score * 1.1, 1.0)
        
        return keyword_score
    
    def _evaluate_formula(self, question: Question, response: str) -> Optional[float]:
        """Evaluate Excel formulas for correctness."""
        if question.type.value not in ['formula', 'function']:
            return None
            
        # Extract potential formulas from response
        formulas = re.findall(r'=[A-Z][A-Z0-9]*\([^)]+\)|=[A-Z]+\([^)]+\)', response)
        
        if not formulas:
            # Look for function names without = sign
            functions = re.findall(r'\b(SUM|MAX|MIN|AVERAGE|VLOOKUP|INDEX|MATCH|COUNT|IF|CONCATENATE)\b', response.upper())
            if functions:
                return 0.7  # Partial credit for mentioning function
            return 0.0
        
        # Check against expected answers
        for formula in formulas:
            for expected in question.expected_answers:
                if self._formulas_equivalent(formula, expected):
                    return 1.0
        
        # Partial credit for syntactically correct formulas
        return 0.6
    
    def _formulas_equivalent(self, formula1: str, formula2: str) -> bool:
        """Check if two Excel formulas are functionally equivalent."""
        try:
            # Normalize formulas (remove spaces, standardize case)
            f1 = re.sub(r'\s+', '', formula1.upper())
            f2 = re.sub(r'\s+', '', formula2.upper())
            
            # Direct string match
            if f1 == f2:
                return True
            
            # Check for range equivalents (A1:A10 vs A1..A10)
            f1_normalized = f1.replace('..', ':')
            f2_normalized = f2.replace('..', ':')
            
            return f1_normalized == f2_normalized
            
        except Exception:
            return False
    
    async def _llm_evaluate(self, question: Question, answer: Answer) -> Dict[str, Any]:
        """Use Gemini LLM for comprehensive answer evaluation."""
        evaluation_data = {
            "question": question.text,
            "question_type": question.type.value,
            "difficulty": question.difficulty.value,
            "answer": answer.response,
            "expected_answers": question.expected_answers,
            "keywords": question.keywords
        }
        
        return await self.llm_manager.evaluate_answer(evaluation_data)
    
    def _combine_evaluations(
        self, 
        question: Question, 
        answer: Answer,
        keyword_score: float,
        formula_score: Optional[float],
        llm_evaluation: Dict[str, Any]
    ) -> Evaluation:
        """Intelligently combine different evaluation approaches."""
        
        # Extract LLM scores
        llm_accuracy = llm_evaluation.get('accuracy_score', 0.5)
        llm_explanation = llm_evaluation.get('explanation_score', 0.5) 
        llm_efficiency = llm_evaluation.get('efficiency_score', 0.5)
        
        # Combine keyword and LLM accuracy scores
        if formula_score is not None:
            # For formula questions, weight formula validation higher
            accuracy_score = (formula_score * 0.6 + llm_accuracy * 0.3 + keyword_score * 0.1)
        else:
            # For non-formula questions, balance LLM and keyword scores
            accuracy_score = (llm_accuracy * 0.7 + keyword_score * 0.3)
        
        # Use LLM scores for explanation and efficiency
        explanation_score = llm_explanation
        efficiency_score = llm_efficiency
        
        # Calculate weighted overall score
        overall_score = (
            accuracy_score * self.accuracy_weight +
            explanation_score * self.explanation_weight +
            efficiency_score * self.efficiency_weight
        ) * question.max_score
        
        # Apply difficulty-based adjustments
        overall_score = self._apply_difficulty_adjustment(overall_score, question.difficulty)
        
        return Evaluation(
            question_id=question.id,
            answer=answer.response,
            score=round(overall_score, 2),
            max_score=question.max_score,
            accuracy_score=round(accuracy_score, 3),
            explanation_score=round(explanation_score, 3),
            efficiency_score=round(efficiency_score, 3),
            feedback=llm_evaluation.get('feedback', 'Good attempt!'),
            strengths=llm_evaluation.get('strengths', []),
            improvement_areas=llm_evaluation.get('improvement_areas', [])
        )
    
    def _apply_difficulty_adjustment(self, score: float, difficulty: QuestionDifficulty) -> float:
        """Apply slight adjustments based on question difficulty."""
        if difficulty == QuestionDifficulty.BASIC:
            # Slightly more generous for basic questions
            return min(score * 1.05, 10.0)
        elif difficulty == QuestionDifficulty.ADVANCED:
            # Slightly more credit for attempting advanced questions
            return max(score, 2.0) if score > 0 else score
        
        return score  # No adjustment for intermediate
    
    def _create_fallback_evaluation(self, question: Question, answer: Answer) -> Evaluation:
        """Create fallback evaluation when main evaluation fails."""
        return Evaluation(
            question_id=question.id,
            answer=answer.response,
            score=5.0,  # Neutral score
            max_score=question.max_score,
            accuracy_score=0.5,
            explanation_score=0.5,
            efficiency_score=0.5,
            feedback="I had some difficulty evaluating this response. The answer shows effort, but please try to be more specific about your Excel approach.",
            strengths=["Attempted the question", "Provided a response"],
            improvement_areas=["Could be more specific", "Include more technical details"]
        )
    
    def calculate_performance_metrics(self, evaluations: List[Evaluation]) -> Dict[str, Any]:
        """Calculate overall performance metrics from evaluations."""
        if not evaluations:
            return {
                "total_score": 0,
                "max_possible_score": 0,
                "percentage_score": 0,
                "average_accuracy": 0,
                "average_explanation": 0,
                "average_efficiency": 0
            }
        
        total_score = sum(eval.score for eval in evaluations)
        max_possible = sum(eval.max_score for eval in evaluations)
        percentage = (total_score / max_possible * 100) if max_possible > 0 else 0
        
        avg_accuracy = sum(eval.accuracy_score for eval in evaluations) / len(evaluations)
        avg_explanation = sum(eval.explanation_score for eval in evaluations) / len(evaluations)
        avg_efficiency = sum(eval.efficiency_score for eval in evaluations) / len(evaluations)
        
        return {
            "total_score": round(total_score, 2),
            "max_possible_score": max_possible,
            "percentage_score": round(percentage, 1),
            "average_accuracy": round(avg_accuracy, 3),
            "average_explanation": round(avg_explanation, 3),
            "average_efficiency": round(avg_efficiency, 3)
        }