"""
FastAPI Backend for Excel Mock Interviewer.
Handles all interview logic, LLM interactions, and state management.
"""

import uuid
import logging
from typing import Dict, List, Optional
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import os
import json

from settings import settings
from data_models import (
    Question, Answer, Evaluation, InterviewState, 
    QuestionDifficulty, ChatMessage
)
from gemini_llm_manager import GeminiLLMManager
from evaluator import ExcelAnswerEvaluator
from question_bank import QuestionBank

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Excel Mock Interviewer API", version="1.0.0")

# Add CORS middleware for Streamlit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
llm_manager = GeminiLLMManager()
evaluator = ExcelAnswerEvaluator(llm_manager)
question_bank = QuestionBank()

# In-memory storage for active sessions
active_sessions: Dict[str, InterviewState] = {}
chat_history: Dict[str, List[ChatMessage]] = {}

# API Request/Response Models
class StartInterviewRequest(BaseModel):
    candidate_name: Optional[str] = None

class StartInterviewResponse(BaseModel):
    session_id: str
    welcome_message: str

class ProcessResponseRequest(BaseModel):
    session_id: str
    response: str

class ProcessResponseResponse(BaseModel):
    ai_response: str
    interview_completed: bool
    current_score: Optional[float] = None

class InterviewStatusResponse(BaseModel):
    session_id: str
    questions_asked: int
    current_difficulty: str
    interview_completed: bool
    total_score: Optional[float] = None
    percentage_score: Optional[float] = None

@app.get("/")
async def root():
    """Health check endpoint."""
    return {"message": "Excel Mock Interviewer API is running!"}

@app.post("/start-interview", response_model=StartInterviewResponse)
async def start_interview(request: StartInterviewRequest):
    """Start a new interview session."""
    try:
        session_id = str(uuid.uuid4())
        
        # Create new interview state
        interview_state = InterviewState(
            session_id=session_id,
            candidate_name=request.candidate_name,
            current_difficulty=QuestionDifficulty.BASIC
        )
        
        active_sessions[session_id] = interview_state
        chat_history[session_id] = []
        
        # Generate welcome message
        welcome_message = await _generate_welcome_message(request.candidate_name)
        
        # Add to chat history
        _add_chat_message(session_id, "assistant", welcome_message)
        
        logger.info(f"Started interview session {session_id} for {request.candidate_name or 'Anonymous'}")
        
        return StartInterviewResponse(
            session_id=session_id,
            welcome_message=welcome_message
        )
        
    except Exception as e:
        logger.error(f"Failed to start interview: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start interview: {str(e)}")

@app.post("/process-response", response_model=ProcessResponseResponse)
async def process_candidate_response(request: ProcessResponseRequest):
    """Process candidate response and return next action."""
    try:
        if request.session_id not in active_sessions:
            raise HTTPException(status_code=404, detail="Interview session not found")
        
        interview_state = active_sessions[request.session_id]
        
        # Add candidate response to chat history
        _add_chat_message(request.session_id, "user", request.response)
        
        # Handle different interview stages
        if not interview_state.questions_asked:
            # First interaction - ask first question
            ai_response = await _ask_next_question(request.session_id)
        elif len(interview_state.questions_asked) > len(interview_state.answers):
            # Waiting for answer to current question
            ai_response = await _handle_answer_and_continue(request.session_id, request.response)
        else:
            # General conversation or clarification
            ai_response = await _handle_general_conversation(request.session_id, request.response)
        
        # Calculate current score if evaluations exist
        current_score = None
        if interview_state.evaluations:
            metrics = evaluator.calculate_performance_metrics(interview_state.evaluations)
            current_score = metrics["percentage_score"]
        
        return ProcessResponseResponse(
            ai_response=ai_response,
            interview_completed=interview_state.interview_completed,
            current_score=current_score
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process response: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process response: {str(e)}")

@app.get("/interview-status/{session_id}", response_model=InterviewStatusResponse)
async def get_interview_status(session_id: str):
    """Get current interview status."""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Interview session not found")
    
    interview_state = active_sessions[session_id]
    
    # Calculate scores if available
    total_score = None
    percentage_score = None
    if interview_state.evaluations:
        metrics = evaluator.calculate_performance_metrics(interview_state.evaluations)
        total_score = metrics["total_score"]
        percentage_score = metrics["percentage_score"]
    
    return InterviewStatusResponse(
        session_id=session_id,
        questions_asked=len(interview_state.questions_asked),
        current_difficulty=interview_state.current_difficulty.value,
        interview_completed=interview_state.interview_completed,
        total_score=total_score,
        percentage_score=percentage_score
    )

async def _generate_welcome_message(candidate_name: Optional[str]) -> str:
    """Generate personalized welcome message."""
    name_greeting = f"Hi {candidate_name}!" if candidate_name else "Hello there!"
    
    welcome_msg = f"""
{name_greeting} Welcome to your Excel Skills Assessment! 🎯

I'm your AI interviewer, and I'm here to evaluate your Microsoft Excel proficiency. Here's what to expect:

📋 **Interview Structure:**
- 5-7 targeted questions covering various Excel skills
- Questions will adapt based on your performance
- Each question builds understanding of your capabilities

⏱️ **Format:**
- Take your time to think through each question
- Explain your reasoning - I value understanding over just correct answers
- Feel free to ask for clarification if needed

🎯 **What I'm Looking For:**
- Technical accuracy of your Excel knowledge
- Quality of your explanations and reasoning
- Practical understanding of when to use different features

Ready to begin? I'll start with a fundamental Excel question to get us going. Good luck! 🚀
    """.strip()
    
    return welcome_msg

async def _ask_next_question(session_id: str) -> str:
    """Select and ask the next appropriate question."""
    interview_state = active_sessions[session_id]
    
    # Determine if we should continue or end interview
    if _should_end_interview(interview_state):
        return await _end_interview(session_id)
    
    # Select next question based on current performance
    next_question = _select_adaptive_question(interview_state)
    
    if not next_question:
        return await _end_interview(session_id)
    
    # Update interview state
    interview_state.questions_asked.append(next_question.id)
    interview_state.current_question_index += 1
    
    # Generate contextual question presentation
    question_context = {
        "stage": "asking_question",
        "question_number": interview_state.current_question_index,
        "total_questions": settings.MAX_QUESTIONS_PER_INTERVIEW,
        "difficulty_level": interview_state.current_difficulty.value,
        "performance_summary": _get_performance_summary(interview_state),
        "task_description": "Present the next question in a professional, encouraging manner",
        "current_question": next_question.text
    }
    
    presentation = await llm_manager.get_interviewer_response(question_context)
    
    _add_chat_message(session_id, "assistant", presentation)
    
    logger.info(f"Asked question {next_question.id} in session {session_id}")
    return presentation

async def _handle_answer_and_continue(session_id: str, response: str) -> str:
    """Evaluate the answer and provide feedback, then continue."""
    interview_state = active_sessions[session_id]
    
    # Get the current question being answered
    current_question_id = interview_state.questions_asked[-1]
    current_question = question_bank.get_question(current_question_id)
    
    if not current_question:
        return "I'm sorry, there was an issue with the current question. Let's continue."
    
    # Create answer object
    answer = Answer(
        question_id=current_question_id,
        response=response,
        timestamp=datetime.now()
    )
    
    # Add answer to interview state
    interview_state.answers.append(answer)
    
    # Evaluate the answer
    evaluation = await evaluator.evaluate_answer(current_question, answer)
    interview_state.evaluations.append(evaluation)
    
    # Update difficulty based on performance
    _update_difficulty_level(interview_state, evaluation)
    
    # Generate feedback and next steps
    feedback_msg = await _generate_contextual_feedback(
        session_id, current_question, evaluation
    )
    
    _add_chat_message(session_id, "assistant", feedback_msg)
    
    # Decide next action - continue or end
    if _should_end_interview(interview_state):
        summary_msg = await _end_interview(session_id)
        return feedback_msg + "\n\n" + summary_msg
    else:
        next_question_msg = await _ask_next_question(session_id)
        return feedback_msg + "\n\n" + next_question_msg

async def _handle_general_conversation(session_id: str, response: str) -> str:
    """Handle general conversation or clarification requests."""
    interview_state = active_sessions[session_id]
    
    # Get current interview context
    context = f"Interview in progress. Question {interview_state.current_question_index} of {settings.MAX_QUESTIONS_PER_INTERVIEW}."
    
    # Generate appropriate response
    reply = await llm_manager.chat_response(response, context)
    
    _add_chat_message(session_id, "assistant", reply)
    return reply

def _select_adaptive_question(interview_state: InterviewState) -> Optional[Question]:
    """Select next question based on adaptive difficulty logic."""
    # Get available questions at current difficulty level
    available_questions = question_bank.get_questions_by_difficulty(
        interview_state.current_difficulty
    )
    
    # Filter out already asked questions
    unasked_questions = [
        q for q in available_questions 
        if q.id not in interview_state.questions_asked
    ]
    
    if not unasked_questions:
        # Try different difficulty levels if current level is exhausted
        for difficulty in [QuestionDifficulty.INTERMEDIATE, QuestionDifficulty.BASIC, QuestionDifficulty.ADVANCED]:
            if difficulty != interview_state.current_difficulty:
                backup_questions = question_bank.get_questions_by_difficulty(difficulty)
                unasked_questions = [
                    q for q in backup_questions 
                    if q.id not in interview_state.questions_asked
                ]
                if unasked_questions:
                    break
    
    if not unasked_questions:
        return None
    
    # Select question with some variety
    import random
    return random.choice(unasked_questions)

def _update_difficulty_level(interview_state: InterviewState, evaluation: Evaluation):
    """Update difficulty level based on recent performance."""
    if not settings.ADAPTIVE_DIFFICULTY:
        return
    
    recent_evaluations = interview_state.evaluations[-3:]  # Last 3 questions
    if len(recent_evaluations) < 2:
        return  # Need at least 2 evaluations to adapt
    
    avg_recent_score = sum(e.score for e in recent_evaluations) / len(recent_evaluations)
    progression_rules = settings.DIFFICULTY_PROGRESSION
    
    current_difficulty = interview_state.current_difficulty
    
    # Progression logic
    if current_difficulty == QuestionDifficulty.BASIC:
        if avg_recent_score >= progression_rules["basic_to_intermediate_threshold"]:
            interview_state.current_difficulty = QuestionDifficulty.INTERMEDIATE
            logger.info(f"Advanced to INTERMEDIATE difficulty in session {interview_state.session_id}")
    
    elif current_difficulty == QuestionDifficulty.INTERMEDIATE:
        if avg_recent_score >= progression_rules["intermediate_to_advanced_threshold"]:
            interview_state.current_difficulty = QuestionDifficulty.ADVANCED
            logger.info(f"Advanced to ADVANCED difficulty in session {interview_state.session_id}")
        elif avg_recent_score < progression_rules["regression_threshold"]:
            interview_state.current_difficulty = QuestionDifficulty.BASIC
            logger.info(f"Regressed to BASIC difficulty in session {interview_state.session_id}")

def _should_end_interview(interview_state: InterviewState) -> bool:
    """Determine if interview should end."""
    num_questions = len(interview_state.questions_asked)
    
    # Minimum questions reached
    if num_questions < settings.MIN_QUESTIONS_PER_INTERVIEW:
        return False
    
    # Maximum questions reached
    if num_questions >= settings.MAX_QUESTIONS_PER_INTERVIEW:
        return True
    
    # End if we have good assessment and candidate is struggling
    if num_questions >= 5:
        recent_scores = [e.score for e in interview_state.evaluations[-3:]]
        if recent_scores and sum(recent_scores) / len(recent_scores) < 3.0:
            return True  # End if struggling significantly
    
    return False

async def _end_interview(session_id: str) -> str:
    """End the interview and generate summary."""
    interview_state = active_sessions[session_id]
    interview_state.end_time = datetime.now()
    interview_state.interview_completed = True
    
    # Generate comprehensive summary
    summary = await _generate_interview_summary(session_id)
    
    # Create summary message
    summary_msg = f"""
🎯 **Interview Complete!** 

Thank you for participating in the Excel Skills Assessment. Here's your performance summary:

{summary}

---

Thank you for your time and effort! This assessment will help identify your Excel proficiency level and areas for continued growth. Best of luck with your career journey! 🚀
    """.strip()
    
    _add_chat_message(session_id, "assistant", summary_msg)
    
    logger.info(f"Completed interview session {session_id}")
    
    # Optionally export transcript for dataset growth
    if getattr(interview_state, "consent_for_export", False):
        export_transcript(interview_state)

    return summary_msg

async def _generate_interview_summary(session_id: str) -> str:
    """Generate comprehensive interview summary."""
    interview_state = active_sessions[session_id]
    
    # Calculate performance metrics
    metrics = evaluator.calculate_performance_metrics(interview_state.evaluations)
    
    # Calculate duration
    duration = (interview_state.end_time - interview_state.start_time).total_seconds() / 60
    
    # Prepare summary data
    summary_data = {
        "total_questions": len(interview_state.questions_asked),
        "overall_score": metrics["percentage_score"],
        "duration": round(duration, 1),
        "skill_breakdown": _calculate_skill_breakdown(interview_state),
        "difficulty_performance": _calculate_difficulty_performance(interview_state)
    }
    
    return await llm_manager.generate_summary(summary_data)

def _calculate_skill_breakdown(interview_state: InterviewState) -> Dict[str, float]:
    """Calculate performance by skill type."""
    skill_scores = {}
    
    for i, question_id in enumerate(interview_state.questions_asked):
        if i < len(interview_state.evaluations):
            question = question_bank.get_question(question_id)
            evaluation = interview_state.evaluations[i]
            
            if question:
                skill_type = question.type.value
                if skill_type not in skill_scores:
                    skill_scores[skill_type] = []
                skill_scores[skill_type].append(evaluation.score)
    
    # Average scores by skill
    return {
        skill: round(sum(scores) / len(scores), 1)
        for skill, scores in skill_scores.items()
    }

def _calculate_difficulty_performance(interview_state: InterviewState) -> Dict[str, float]:
    """Calculate performance by difficulty level."""
    difficulty_scores = {
        QuestionDifficulty.BASIC.value: [],
        QuestionDifficulty.INTERMEDIATE.value: [],
        QuestionDifficulty.ADVANCED.value: []
    }
    
    for i, question_id in enumerate(interview_state.questions_asked):
        if i < len(interview_state.evaluations):
            question = question_bank.get_question(question_id)
            evaluation = interview_state.evaluations[i]
            
            if question:
                difficulty_scores[question.difficulty.value].append(evaluation.score)
    
    # Average scores by difficulty, only include if questions were asked
    return {
        diff: round(sum(scores) / len(scores), 1)
        for diff, scores in difficulty_scores.items()
        if scores
    }

async def _generate_contextual_feedback(
    session_id: str, 
    question: Question, 
    evaluation: Evaluation
) -> str:
    """Generate contextual feedback for the answer."""
    interview_state = active_sessions[session_id]
    
    # Add contextual elements
    question_num = len(interview_state.questions_asked)
    
    contextual_msg = f"""
📊 **Question {question_num} Feedback:**

{evaluation.feedback}

**Score: {evaluation.score:.1f}/10** ⭐
    """.strip()
    
    return contextual_msg

def _get_performance_summary(interview_state: InterviewState) -> str:
    """Get brief performance summary for context."""
    if not interview_state.evaluations:
        return "Just getting started"
    
    avg_score = sum(e.score for e in interview_state.evaluations) / len(interview_state.evaluations)
    
    if avg_score >= 8:
        return "Excellent performance so far"
    elif avg_score >= 6:
        return "Good performance with solid understanding"
    elif avg_score >= 4:
        return "Mixed performance, some areas strong"
    else:
        return "Challenging session, providing support"

def _add_chat_message(session_id: str, role: str, content: str):
    """Add message to chat history."""
    if session_id not in chat_history:
        chat_history[session_id] = []
    
    message = ChatMessage(role=role, content=content)
    chat_history[session_id].append(message)

def export_transcript(interview_state, folder=None):
    if folder is None:
        folder = settings.TRANSCRIPTS_DIR
    os.makedirs(folder, exist_ok=True)
    file_path = os.path.join(folder, f"{interview_state.session_id}.json")
    with open(file_path, "w", encoding="utf-8") as f:
        try:
            json.dump(interview_state.model_dump(), f, indent=2, ensure_ascii=False)
        except AttributeError:
            json.dump(interview_state.dict(), f, indent=2, ensure_ascii=False)
    logging.info(f"Transcript exported: {file_path}")
    return file_path

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.API_HOST, port=settings.API_PORT, reload=settings.API_RELOAD)
