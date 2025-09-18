"""
Question Bank for Excel Mock Interviewer.
Manages question storage, retrieval, and expansion over time.
"""

import json
import logging
import os
import random
from typing import Dict, List, Optional
from data_models import Question, QuestionDifficulty, QuestionType
from settings import settings

logger = logging.getLogger(__name__)

class QuestionBank:
    """Manages the collection of interview questions."""
    
    def __init__(self):
        """Initialize question bank and load questions."""
        self.questions: Dict[str, Question] = {}
        self.questions_by_difficulty: Dict[QuestionDifficulty, List[Question]] = {
            QuestionDifficulty.BASIC: [],
            QuestionDifficulty.INTERMEDIATE: [],
            QuestionDifficulty.ADVANCED: []
        }
        self.questions_by_type: Dict[QuestionType, List[Question]] = {}
        self._load_questions()
    
    def _load_questions(self):
        """Load questions from JSON files or create sample questions."""
        try:
            # Create directories if they don't exist
            os.makedirs(settings.QUESTIONS_DIR, exist_ok=True)
            
            # Try to load questions from files, create samples if missing
            for difficulty, category in [
                (QuestionDifficulty.BASIC, "basic"),
                (QuestionDifficulty.INTERMEDIATE, "intermediate"),
                (QuestionDifficulty.ADVANCED, "advanced"),
            ]:
                file_path = os.path.join(settings.QUESTIONS_DIR, f"{category}_questions.json")

                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        questions_data = json.load(f)
                    for question_id, question_data in questions_data.items():
                        question = Question(**question_data)
                        self._add_question_to_bank(question)
                else:
                    logger.warning(f"Question file not found: {file_path}, creating samples")
                    self._create_sample_questions(difficulty)
            
            logger.info(f"Loaded {len(self.questions)} questions into question bank")
        
        except Exception as e:
            logger.error(f"Failed to load questions: {e}")
            self._create_minimal_sample_questions()
    
    def _create_sample_questions(self, difficulty: QuestionDifficulty):
        """Create sample questions for cold start scenario."""
        sample_questions = {}

        if difficulty == QuestionDifficulty.BASIC:
            sample_questions = {
                "basic_001": {
                    "id": "basic_001",
                    "text": "Calculate the total sales for the month with data in cells A1 through A10. What Excel formula would you use and why?",
                    "type": "formula",
                    "difficulty": "basic",
                    "expected_answers": [
                        "=SUM(A1:A10)", "SUM(A1:A10)",
                        "Use the SUM function with range A1:A10"
                    ],
                    "keywords": ["SUM", "formula", "range", "A1:A10", "total", "addition"],
                    "max_score": 10,
                    "time_limit": 180,
                    "hints": [
                        "Which function adds up numbers in Excel?",
                        "The function starts with S and adds all numbers in a range"
                    ]
                },
                "basic_002": {
                    "id": "basic_002",
                    "text": "How would you make text in a cell appear bold and increase the font size to 14? Walk me through the steps.",
                    "type": "conditional_formatting",
                    "difficulty": "basic",
                    "expected_answers": [
                        "Select cell, click Bold button, change font size to 14",
                        "Ctrl+B for bold, then change font size dropdown to 14",
                        "Right-click, Format Cells, Font tab, Bold and size 14"
                    ],
                    "keywords": ["bold", "font", "size", "formatting", "toolbar", "Ctrl+B"],
                    "max_score": 10,
                    "time_limit": 180
                },
                "basic_003": {
                    "id": "basic_003",
                    "text": "I want to find the highest value in a column of numbers from B1 to B15. What function should I use?",
                    "type": "function",
                    "difficulty": "basic",
                    "expected_answers": [
                        "=MAX(B1:B15)",
                        "MAX(B1:B15)",
                        "Use MAX function",
                        "The MAX function will find the highest value"
                    ],
                    "keywords": ["MAX", "maximum", "highest", "largest", "function", "B1:B15"],
                    "max_score": 10,
                    "time_limit": 180
                }
            }
        
        elif difficulty == QuestionDifficulty.INTERMEDIATE:
            sample_questions = {
                "inter_001": {
                    "id": "inter_001",
                    "text": "I have a table with employee names in column A and their salaries in column B. I want to look up 'John Smith' and return his salary. How would you do this using a lookup function?",
                    "type": "function",
                    "difficulty": "intermediate",
                    "expected_answers": [
                        "=VLOOKUP(\"John Smith\",A:B,2,FALSE)",
                        "=VLOOKUP(\"John Smith\",A1:B100,2,0)",
                        "Use VLOOKUP function to search for John Smith"
                    ],
                    "keywords": ["VLOOKUP", "lookup", "search", "exact match", "FALSE", "column 2"],
                    "max_score": 10,
                    "time_limit": 240
                },
                "inter_002": {
                    "id": "inter_002",
                    "text": "Explain how you would create a PivotTable to summarize sales data by region and product category. What are the key steps?",
                    "type": "pivot_table",
                    "difficulty": "intermediate",
                    "expected_answers": [
                        "Select data, Insert > PivotTable, drag Region to Rows, Category to Columns, Sales to Values",
                        "Insert PivotTable, set up rows and columns, add values field"
                    ],
                    "keywords": ["PivotTable", "Insert", "Rows", "Columns", "Values", "drag", "field list"],
                    "max_score": 10,
                    "time_limit": 300
                }
            }
        
        elif difficulty == QuestionDifficulty.ADVANCED:
            sample_questions = {
                "adv_001": {
                    "id": "adv_001",
                    "text": "Create a dynamic formula that combines INDEX and MATCH to lookup a value. Explain why this is sometimes better than VLOOKUP and provide an example.",
                    "type": "formula",
                    "difficulty": "advanced",
                    "expected_answers": [
                        "=INDEX(return_range, MATCH(lookup_value, lookup_range, 0))",
                        "INDEX-MATCH is more flexible than VLOOKUP, can look left or right"
                    ],
                    "keywords": ["INDEX", "MATCH", "lookup", "flexible", "dynamic", "VLOOKUP alternative"],
                    "max_score": 10,
                    "time_limit": 360
                }
            }

        for question_id, question_data in sample_questions.items():
            question = Question(**question_data)
            self._add_question_to_bank(question)
    
    def _create_minimal_sample_questions(self):
        """Create absolute minimal questions for emergency cold start."""
        minimal_questions = [
            {
                "id": "emergency_001",
                "text": "What Excel function would you use to add up a column of numbers?",
                "type": "function",
                "difficulty": "basic",
                "expected_answers": ["SUM", "=SUM()", "SUM function"],
                "keywords": ["SUM", "add", "total"],
                "max_score": 10,
                "time_limit": 180
            },
            {
                "id": "emergency_002", 
                "text": "How would you create a simple chart from your data in Excel?",
                "type": "chart",
                "difficulty": "intermediate",
                "expected_answers": ["Select data, Insert tab, Chart", "Insert > Chart"],
                "keywords": ["chart", "Insert", "data", "graph"],
                "max_score": 10,
                "time_limit": 240
            }
        ]
        
        for question_data in minimal_questions:
            question = Question(**question_data)
            self._add_question_to_bank(question)
        
        logger.warning("Created emergency minimal question set")
    
    def _add_question_to_bank(self, question: Question):
        """Add a question to all relevant collections."""
        self.questions[question.id] = question
        self.questions_by_difficulty[question.difficulty].append(question)
        
        if question.type not in self.questions_by_type:
            self.questions_by_type[question.type] = []
        self.questions_by_type[question.type].append(question)
    
    def get_question(self, question_id: str) -> Optional[Question]:
        """Get a specific question by ID."""
        return self.questions.get(question_id)
    
    def get_questions_by_difficulty(self, difficulty: QuestionDifficulty) -> List[Question]:
        """Get all questions of a specific difficulty level."""
        return self.questions_by_difficulty.get(difficulty, [])
    
    def get_random_question(
        self, 
        difficulty: Optional[QuestionDifficulty] = None,
        question_type: Optional[QuestionType] = None,
        exclude_ids: Optional[List[str]] = None
    ) -> Optional[Question]:
        """Get a random question based on criteria."""
        exclude_ids = exclude_ids or []
        
        # Filter questions based on criteria
        candidates = list(self.questions.values())
        
        if difficulty:
            candidates = [q for q in candidates if q.difficulty == difficulty]
        
        if question_type:
            candidates = [q for q in candidates if q.type == question_type]
        
        # Exclude already used questions
        candidates = [q for q in candidates if q.id not in exclude_ids]
        
        if not candidates:
            return None
        
        return random.choice(candidates)
    
    def get_statistics(self) -> Dict[str, any]:
        """Get statistics about the question bank."""
        stats = {
            "total_questions": len(self.questions),
            "by_difficulty": {
                difficulty.value: len(questions) 
                for difficulty, questions in self.questions_by_difficulty.items()
            },
            "by_type": {
                qtype.value: len(questions)
                for qtype, questions in self.questions_by_type.items()
            }
        }
        return stats
