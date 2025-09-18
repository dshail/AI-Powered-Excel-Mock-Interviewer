"""
LLM Mock Manager for Excel Mock Interviewer
Provides intelligent mock responses to save API quota during development.
"""

import json
import logging
from typing import Dict, Any, Optional
from settings import settings

logger = logging.getLogger(__name__)

class MockLLMResponses:
    """
    Centralized mock responses for different Excel interview scenarios.
    Add more scenarios as your question bank grows.
    """
    
    # Welcome and introduction responses
    WELCOME_RESPONSES = {
        "default": """
Welcome to your Excel Skills Assessment! I'm your AI interviewer.

Today I'll evaluate your Microsoft Excel knowledge through a series of questions. 
The interview will adapt based on your performance, covering basic to advanced Excel skills.

Let's start with a fundamental question about Excel formulas.
        """.strip()
    }
    
    # Question-specific mock responses
    QUESTION_RESPONSES = {
        # Basic level responses
        "sum": "Excellent! You correctly identified the SUM function. This is the most commonly used Excel function for adding values in a range. Your approach =SUM(A1:A10) is perfect for calculating totals.",
        
        "max": "Great work! The MAX function is exactly right for finding the highest value. This function is very useful for data analysis tasks.",
        
        "average": "Perfect! AVERAGE is the correct function here. This gives you the mean of all values in the specified range.",
        
        "formatting": "Good understanding of Excel formatting! Using the toolbar or Ctrl+B for bold and adjusting font size shows you know the basics of cell formatting.",
        
        # Intermediate level responses  
        "vlookup": "Excellent choice! VLOOKUP is a powerful lookup function. Your syntax looks correct - remember that FALSE/0 ensures an exact match, which is usually what you want.",
        
        "pivottable": "Outstanding! You understand the PivotTable workflow perfectly. Insert > PivotTable, then dragging fields to Rows, Columns, and Values is exactly the right approach.",
        
        "conditional_formatting": "Great! Conditional formatting is a powerful feature for highlighting data patterns. Your understanding of the process is solid.",
        
        "charts": "Perfect! The Insert tab is indeed where you create charts. Understanding how to visualize data is crucial for Excel proficiency.",
        
        # Advanced level responses
        "index_match": "Impressive! INDEX-MATCH is often superior to VLOOKUP because it's more flexible and can look both left and right. This shows advanced Excel knowledge.",
        
        "macros": "Excellent advanced knowledge! Understanding VBA and macros demonstrates real Excel expertise. This can automate complex workflows.",
        
        "data_analysis": "Outstanding! Your knowledge of Excel's data analysis tools shows you understand how to work with large datasets efficiently.",
        
        # Generic fallbacks
        "generic_good": "Good work! Your answer shows understanding of Excel concepts. Consider adding more specific details about implementation.",
        
        "generic_partial": "You're on the right track! Your answer has some correct elements. Try to be more specific about the exact steps or functions.",
        
        "generic_needs_work": "I can see you're trying! Let me give you a hint - think about which Excel function or feature would be most appropriate for this task."
    }
    
    # Mock evaluation responses
    EVALUATION_TEMPLATES = {
        "excellent": {
            "accuracy_score": 0.95,
            "explanation_score": 0.90,
            "efficiency_score": 0.92,
            "overall_score": 9.2,
            "feedback": "Excellent work! Your answer demonstrates strong Excel knowledge with clear explanation and optimal approach.",
            "strengths": ["Accurate formula usage", "Clear explanation", "Efficient method"],
            "improvement_areas": ["Consider mentioning error handling"]
        },
        "good": {
            "accuracy_score": 0.80,
            "explanation_score": 0.75,
            "efficiency_score": 0.78,
            "overall_score": 7.7,
            "feedback": "Good answer! You identified the correct approach. Adding more detail to your explanation would improve your score.",
            "strengths": ["Correct function identified", "Understanding shown"],
            "improvement_areas": ["Provide more detailed steps", "Explain reasoning more clearly"]
        },
        "needs_improvement": {
            "accuracy_score": 0.50,
            "explanation_score": 0.45,
            "efficiency_score": 0.40,
            "overall_score": 4.5,
            "feedback": "You're making progress! Try to be more specific about Excel functions and provide step-by-step explanations.",
            "strengths": ["Shows effort", "Basic understanding present"],
            "improvement_areas": ["Be more specific about Excel features", "Provide detailed steps", "Practice common functions"]
        }
    }
    
    # Interview summary templates
    SUMMARY_TEMPLATES = {
        "high_performer": """
🎯 **Interview Complete - Excellent Performance!**

**Overall Assessment:** You demonstrated strong Excel proficiency across multiple areas.

**Key Strengths:**
• Expert-level formula knowledge
• Clear communication and explanation skills  
• Efficient problem-solving approach

**Proficiency Level:** **Advanced** 
**Recommendation:** You're ready for complex Excel challenges. Consider exploring Power Query and advanced data modeling.
        """.strip(),
        
        "mid_performer": """
🎯 **Interview Complete - Solid Performance!**

**Overall Assessment:** Good foundation with room for growth in advanced features.

**Key Strengths:**
• Solid understanding of basic functions
• Good grasp of data manipulation
• Clear communication style

**Areas for Growth:**
• Practice advanced lookup functions
• Explore PivotTable advanced features

**Proficiency Level:** **Intermediate**
**Recommendation:** Focus on VLOOKUP, INDEX-MATCH, and PivotTable mastery.
        """.strip(),
        
        "beginner": """
🎯 **Interview Complete - Keep Learning!**

**Overall Assessment:** You have a foundation to build upon with focused learning.

**Key Strengths:**
• Shows willingness to learn
• Basic understanding of Excel interface
• Good attitude toward feedback

**Areas for Growth:**
• Master basic functions (SUM, AVERAGE, MAX)
• Practice formula syntax
• Learn about cell references

**Proficiency Level:** **Basic**
**Recommendation:** Start with Excel fundamentals course and practice daily with basic formulas.
        """.strip()
    }

class LLMMockManager:
    """
    Manages mock LLM responses for development and testing.
    Integrates seamlessly with existing LLM manager.
    """
    
    def __init__(self):
        self.responses = MockLLMResponses()
        self.call_count = 0
        
    def _detect_response_type(self, prompt: str, context: str = "") -> str:
        """
        Intelligently categorize the prompt to return appropriate mock response.
        """
        prompt_lower = prompt.lower()
        context_lower = context.lower()
        
        # Check for specific Excel functions/features
        if any(word in prompt_lower for word in ["sum", "total", "add up"]):
            return "sum"
        elif any(word in prompt_lower for word in ["max", "maximum", "highest", "largest"]):
            return "max"
        elif any(word in prompt_lower for word in ["average", "mean"]):
            return "average"
        elif any(word in prompt_lower for word in ["vlookup", "lookup", "search"]):
            return "vlookup"
        elif any(word in prompt_lower for word in ["pivot", "pivottable"]):
            return "pivottable"
        elif any(word in prompt_lower for word in ["index", "match"]):
            return "index_match"
        elif any(word in prompt_lower for word in ["chart", "graph"]):
            return "charts"
        elif any(word in prompt_lower for word in ["format", "bold", "font"]):
            return "formatting"
        elif any(word in prompt_lower for word in ["macro", "vba"]):
            return "macros"
        else:
            return "generic_good"
    
    def _detect_evaluation_level(self, answer: str) -> str:
        """
        Determine evaluation level based on answer characteristics.
        """
        answer_lower = answer.lower()
        
        # High quality indicators
        if (len(answer) > 50 and 
            any(word in answer_lower for word in ["because", "step", "first", "then", "formula"]) and
            "=" in answer):
            return "excellent"
        
        # Medium quality indicators
        elif (len(answer) > 20 and 
              any(word in answer_lower for word in ["use", "function", "excel"])):
            return "good"
        
        # Needs improvement
        else:
            return "needs_improvement"
    
    async def mock_interviewer_response(self, context: Dict[str, Any]) -> str:
        """
        Mock response for interviewer agent.
        """
        self.call_count += 1
        
        stage = context.get("stage", "asking_question")
        question = context.get("current_question", "")
        
        if stage == "welcome":
            return self.responses.WELCOME_RESPONSES["default"]
        
        # Determine response type based on question content
        response_type = self._detect_response_type(question)
        base_response = self.responses.QUESTION_RESPONSES.get(response_type, 
                                                            self.responses.QUESTION_RESPONSES["generic_good"])
        
        # Add question number context
        question_num = context.get("question_number", 1)
        
        return f"""
📋 **Question {question_num}:** {question}

{base_response}

Please provide your answer, and I'll evaluate your response and give you detailed feedback!
        """.strip()
    
    async def mock_evaluate_answer(self, evaluation_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Mock response for answer evaluation.
        """
        answer = evaluation_data.get("answer", "")
        question_type = evaluation_data.get("question_type", "function")
        
        # Determine evaluation level
        eval_level = self._detect_evaluation_level(answer)
        
        # Get base template
        evaluation = self.responses.EVALUATION_TEMPLATES[eval_level].copy()
        
        # Customize feedback based on question type
        if question_type == "formula" and "=" in answer:
            evaluation["accuracy_score"] = min(evaluation["accuracy_score"] + 0.1, 1.0)
            evaluation["feedback"] += " Great use of formula syntax!"
        
        return evaluation
    
    async def mock_generate_feedback(self, feedback_data: Dict[str, Any]) -> str:
        """
        Mock response for feedback generation.
        """
        score = feedback_data.get("overall_score", 5.0)
        
        if score >= 8.0:
            return "Excellent work! You demonstrated strong Excel knowledge and clear communication."
        elif score >= 6.0:
            return "Good job! You're on the right track. Practice explaining your reasoning more thoroughly."
        else:
            return "Keep practicing! Focus on the fundamentals and don't hesitate to ask for help."
    
    async def mock_generate_summary(self, summary_data: Dict[str, Any]) -> str:
        """
        Mock response for interview summary.
        """
        overall_score = summary_data.get("overall_score", 50)
        
        if overall_score >= 80:
            return self.responses.SUMMARY_TEMPLATES["high_performer"]
        elif overall_score >= 60:
            return self.responses.SUMMARY_TEMPLATES["mid_performer"]
        else:
            return self.responses.SUMMARY_TEMPLATES["beginner"]
    
    async def mock_chat_response(self, message: str, context: str = "") -> str:
        """
        Mock response for general chat.
        """
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["hello", "hi", "start"]):
            return "Hello! I'm ready to begin your Excel skills assessment. Let's start with our first question!"
        
        elif any(word in message_lower for word in ["help", "clarify", "explain"]):
            return "Of course! I'm here to help. Feel free to ask for clarification on any question, and I'll provide guidance."
        
        elif any(word in message_lower for word in ["ready", "continue", "next"]):
            return "Great! Let's continue with the next question."
        
        else:
            return "I understand. Let me know if you need any clarification, and we can proceed with the assessment."
    
    def get_mock_stats(self) -> Dict[str, Any]:
        """
        Get statistics about mock usage.
        """
        return {
            "total_mock_calls": self.call_count,
            "mock_mode_active": settings.USE_MOCK_LLM,
            "available_response_types": len(self.responses.QUESTION_RESPONSES),
            "available_evaluation_levels": len(self.responses.EVALUATION_TEMPLATES)
        }

# Global instance for easy import
mock_manager = LLMMockManager()

# Convenience functions for direct use
async def get_mock_interviewer_response(context: Dict[str, Any]) -> str:
    """Convenience function for mock interviewer response."""
    return await mock_manager.mock_interviewer_response(context)

async def get_mock_evaluation(evaluation_data: Dict[str, Any]) -> Dict[str, Any]:
    """Convenience function for mock evaluation."""
    return await mock_manager.mock_evaluate_answer(evaluation_data)

async def get_mock_feedback(feedback_data: Dict[str, Any]) -> str:
    """Convenience function for mock feedback."""
    return await mock_manager.mock_generate_feedback(feedback_data)

async def get_mock_summary(summary_data: Dict[str, Any]) -> str:
    """Convenience function for mock summary."""
    return await mock_manager.mock_generate_summary(summary_data)

async def get_mock_chat_response(message: str, context: str = "") -> str:
    """Convenience function for mock chat response."""
    return await mock_manager.mock_chat_response(message, context)