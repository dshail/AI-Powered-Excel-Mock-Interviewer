"""
Data models for the Excel Mock Interviewer system.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum

class QuestionDifficulty(str, Enum):
    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

class QuestionType(str, Enum):
    FORMULA = "formula"
    FUNCTION = "function"
    DATA_ANALYSIS = "data_analysis"
    CHART = "chart"
    PIVOT_TABLE = "pivot_table"
    MACRO = "macro"
    CONDITIONAL_FORMATTING = "conditional_formatting"

class Question(BaseModel):
    id: str
    text: str
    type: QuestionType
    difficulty: QuestionDifficulty
    expected_answers: List[str]
    keywords: List[str] = []
    max_score: int = 10
    time_limit: Optional[int] = 300
    hints: List[str] = []

class Answer(BaseModel):
    question_id: str
    response: str
    timestamp: datetime = datetime.now()
    processing_time: Optional[float] = None

class Evaluation(BaseModel):
    question_id: str
    answer: str
    score: float
    max_score: int
    accuracy_score: float
    explanation_score: float
    efficiency_score: float
    feedback: str
    strengths: List[str] = []
    improvement_areas: List[str] = []

class InterviewState(BaseModel):
    session_id: str
    candidate_name: Optional[str] = None
    current_question_index: int = 0
    questions_asked: List[str] = []
    answers: List[Answer] = []
    evaluations: List[Evaluation] = []
    start_time: datetime = datetime.now()
    end_time: Optional[datetime] = None
    current_difficulty: QuestionDifficulty = QuestionDifficulty.BASIC
    interview_completed: bool = False

class ChatMessage(BaseModel):
    role: str
    content: str
    timestamp: datetime = datetime.now()
    metadata: Dict[str, Any] = {}
