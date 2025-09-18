"""
Streamlit Frontend for Excel Mock Interviewer.
Communicates with FastAPI backend for all interview logic.
"""

import streamlit as st
import requests
import logging
from datetime import datetime
from typing import Optional, Dict, Any

from settings import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title=settings.APP_TITLE,
    page_icon=settings.APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inform about mock mode (now safe; runs after set_page_config)
if settings.USE_MOCK_LLM:
    st.info("🧪 **MOCK MODE ACTIVE** - No real API calls. Safe for development!")

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 1rem 0;
        border-bottom: 2px solid #f0f2f6;
        margin-bottom: 2rem;
    }
    
    .interview-stats {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #dee2e6;
    }
    
    .score-badge {
        display: inline-block;
        padding: 0.25rem 0.5rem;
        margin: 0.25rem;
        background-color: #28a745;
        color: white;
        border-radius: 0.25rem;
        font-weight: bold;
    }
    
    .status-indicator {
        display: inline-block;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        margin-right: 0.5rem;
    }
    
    .status-active { background-color: #28a745; }
    .status-waiting { background-color: #ffc107; }
    .status-complete { background-color: #6c757d; }
    
    .connection-error {
        background-color: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 0.25rem;
        border: 1px solid #f5c6cb;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state variables
def initialize_session_state():
    """Initialize Streamlit session state variables."""
    if "session_id" not in st.session_state:
        st.session_state.session_id = None
    
    if "interview_started" not in st.session_state:
        st.session_state.interview_started = False
    
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []
    
    if "candidate_name" not in st.session_state:
        st.session_state.candidate_name = ""
    
    if "interview_status" not in st.session_state:
        st.session_state.interview_status = None
    
    if "backend_connected" not in st.session_state:
        st.session_state.backend_connected = None

def check_backend_connection() -> bool:
    """Check if FastAPI backend is running."""
    try:
        response = requests.get(f"{settings.API_BASE_URL}/", timeout=5)
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Backend connection failed: {e}")
        return False

def display_connection_error():
    """Display backend connection error."""
    st.markdown("""
    <div class="connection-error">
        <h4>⚠️ Backend Connection Error</h4>
        <p>Cannot connect to the FastAPI backend server.</p>
        <p><strong>To fix this:</strong></p>
        <ol>
            <li>Make sure you have started the FastAPI backend:
                <br><code>python fastapi_backend.py</code>
            </li>
            <li>Verify the backend is running at: <a href="http://localhost:8000" target="_blank">http://localhost:8000</a></li>
            <li>Check your .env configuration</li>
        </ol>
        <p>Then refresh this page.</p>
    </div>
    """, unsafe_allow_html=True)

def display_header():
    """Display the main application header."""
    st.markdown(f"""
    <div class="main-header">
        <h1>{settings.APP_ICON} {settings.APP_TITLE}</h1>
        <p>AI-Powered Excel Skills Assessment</p>
    </div>
    """, unsafe_allow_html=True)

def display_sidebar():
    """Display sidebar with interview information and controls."""
    with st.sidebar:
        st.markdown(f"## {settings.SIDEBAR_LOGO} Interview Dashboard")
        
        # Backend status
        if st.session_state.backend_connected:
            st.success("🟢 Backend Connected")
        else:
            st.error("🔴 Backend Disconnected")
            if st.button("🔄 Retry Connection"):
                st.session_state.backend_connected = check_backend_connection()
                st.rerun()
        
        # Interview status
        if st.session_state.interview_started and st.session_state.interview_status:
            status = st.session_state.interview_status
            
            # Status indicator
            if status.get("interview_completed"):
                status_class = "status-complete"
                status_text = "Complete"
            elif status.get("questions_asked", 0) > 0:
                status_class = "status-active"
                status_text = "In Progress"
            else:
                status_class = "status-waiting"
                status_text = "Starting"
            
            st.markdown(f"""
            <div class="interview-stats">
                <h4>
                    <span class="status-indicator {status_class}"></span>
                    Status: {status_text}
                </h4>
            </div>
            """, unsafe_allow_html=True)
            
            # Interview progress
            questions_asked = status.get("questions_asked", 0)
            max_questions = settings.MAX_QUESTIONS_PER_INTERVIEW
            
            st.markdown("### 📊 Progress")
            progress = questions_asked / max_questions if max_questions > 0 else 0
            st.progress(progress)
            st.write(f"Questions: {questions_asked}/{max_questions}")
            
            if st.session_state.candidate_name:
                st.write(f"**Candidate:** {st.session_state.candidate_name}")
            
            current_difficulty = status.get("current_difficulty", "basic")
            st.write(f"**Difficulty:** {current_difficulty.title()}")
            
            # Performance summary
            if status.get("percentage_score") is not None:
                score = status["percentage_score"]
                st.markdown(f"""
                <div class="score-badge">
                    Current Score: {score:.1f}%
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("---")
        
        # Instructions
        st.markdown("### 💡 Tips")
        st.markdown("""
        - **Explain your reasoning** - not just the answer
        - **Be specific** about Excel features you'd use
        - **Ask for clarification** if needed
        - **Take your time** - quality over speed
        """)
        
        st.markdown("### 🎯 Assessment Areas")
        st.markdown("""
        - **Formulas & Functions**
        - **Data Analysis**
        - **Charts & Visualization**
        - **Data Management**
        - **Advanced Features**
        """)
        
        # Reset interview button
        if st.session_state.interview_started:
            st.markdown("---")
            if st.button("🔄 Start New Interview"):
                reset_interview()

def reset_interview():
    """Reset the interview session."""
    st.session_state.session_id = None
    st.session_state.interview_started = False
    st.session_state.chat_messages = []
    st.session_state.interview_status = None
    st.rerun()

def display_interview_setup():
    """Display the interview setup form."""
    st.markdown("## Welcome to Your Excel Skills Assessment! 🚀")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ### What to Expect
        - **5-7 targeted questions** covering various Excel skills
        - **Adaptive difficulty** based on your performance
        - **Immediate feedback** on each response
        - **Comprehensive summary** at the end
        
        ### How It Works
        1. Enter your name (optional) and click Start
        2. Answer questions about Excel features and functions
        3. Explain your reasoning and approach
        4. Receive feedback and your final assessment
        """)
        
        # Name input
        candidate_name = st.text_input(
            "Your Name (Optional)", 
            value=st.session_state.candidate_name,
            help="This helps personalize your experience"
        )
        st.session_state.candidate_name = candidate_name
        
        # Start interview button
        if st.button("🎯 Start Excel Assessment"):
            if st.session_state.backend_connected:
                start_interview()
            else:
                st.error("Cannot start interview: Backend server is not connected")
    
    with col2:
        st.markdown("### 📋 Assessment Levels")
        st.info("""
        **Basic Level**
        - Basic formulas (SUM, AVERAGE)
        - Cell formatting
        - Simple functions
        
        **Intermediate Level**
        - VLOOKUP, PivotTables
        - Conditional formatting
        - Charts and graphs
        
        **Advanced Level**
        - Complex formulas
        - Macros and VBA
        - Advanced data analysis
        """)

def start_interview():
    """Start a new interview session."""
    try:
        # Call FastAPI backend to start interview
        response = requests.post(
            f"{settings.API_BASE_URL}/start-interview",
            json={"candidate_name": st.session_state.candidate_name or None},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Update session state
            st.session_state.session_id = data["session_id"]
            st.session_state.interview_started = True
            st.session_state.chat_messages = [
                {"role": "assistant", "content": data["welcome_message"], "timestamp": datetime.now()}
            ]
            
            # Get initial interview status
            update_interview_status()
            
            # Rerun to show chat interface
            st.rerun()
        else:
            st.error(f"Failed to start interview: {response.text}")
            
    except Exception as e:
        st.error(f"Failed to start interview: {str(e)}")
        logger.error(f"Interview start failed: {e}")

def display_chat_interface():
    """Display the main chat interface."""
    # Chat container
    chat_container = st.container()
    
    with chat_container:
        # Display chat messages
        for message in st.session_state.chat_messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Type your response here..."):
        handle_user_input(prompt)

def handle_user_input(user_input: str):
    """Handle user input and get AI response."""
    if not st.session_state.session_id:
        st.error("No active interview session. Please start a new interview.")
        return
    
    # Add user message to chat immediately
    st.session_state.chat_messages.append({
        "role": "user",
        "content": user_input,
        "timestamp": datetime.now()
    })
    
    try:
        # Call FastAPI backend to process response
        response = requests.post(
            f"{settings.API_BASE_URL}/process-response",
            json={
                "session_id": st.session_state.session_id,
                "response": user_input
            },
            timeout=30  # Longer timeout for LLM processing
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Add AI response to chat
            st.session_state.chat_messages.append({
                "role": "assistant", 
                "content": data["ai_response"],
                "timestamp": datetime.now()
            })
            
            # Update interview status
            update_interview_status()
            
            # Rerun to show updated chat
            st.rerun()
        else:
            st.error(f"Failed to process response: {response.text}")
        
    except Exception as e:
        st.error(f"Failed to process response: {str(e)}")
        logger.error(f"Response processing failed: {e}")

def update_interview_status():
    """Update interview status from backend."""
    if not st.session_state.session_id:
        return
    
    try:
        response = requests.get(
            f"{settings.API_BASE_URL}/interview-status/{st.session_state.session_id}",
            timeout=5
        )
        
        if response.status_code == 200:
            st.session_state.interview_status = response.json()
        else:
            logger.error(f"Failed to get interview status: {response.text}")
            
    except Exception as e:
        logger.error(f"Status update failed: {e}")

def display_interview_summary():
    """Display interview summary if completed."""
    if st.session_state.interview_status and st.session_state.interview_status.get("interview_completed"):
        st.success("🎉 Interview Completed!")  
        status = st.session_state.interview_status
        download_transcript_button(st.session_state.session_id)

        
        if status.get("percentage_score") is not None:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Score", f"{status.get('total_score', 0):.1f}")
            
            with col2:
                st.metric("Percentage", f"{status.get('percentage_score', 0):.1f}%")
            
            with col3:
                st.metric("Questions", status.get("questions_asked", 0))
            
            # Detailed breakdown
            st.markdown("### 📊 Performance Breakdown")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Performance Level:**")
                percentage = status.get('percentage_score', 0)
                if percentage >= 80:
                    st.success("🏆 Advanced Level")
                elif percentage >= 65:
                    st.info("🥈 Intermediate Level") 
                else:
                    st.warning("🥉 Basic Level")
            
            with col2:
                st.markdown("**Interview Stats:**")
                st.write(f"• Questions Asked: {status.get('questions_asked', 0)}")
                st.write(f"• Final Difficulty: {status.get('current_difficulty', 'basic').title()}")
                st.write(f"• Status: Complete ✅")

import base64

def download_transcript_button(session_id):
    st.markdown("#### 📥 Export your transcript")
    # Call backend to get transcript (simple GET, returns JSON)
    url = f"{settings.API_BASE_URL}/transcript/{session_id}"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.text
            b64 = base64.b64encode(data.encode('utf-8')).decode()
            download_link = f'<a href="data:file/json;base64,{b64}" download="interview_transcript_{session_id}.json">⬇️ Download Interview Transcript (JSON)</a>'
            st.markdown(download_link, unsafe_allow_html=True)
        else:
            st.warning("Transcript not found or server error.")
    except Exception as e:
        st.warning(f"Could not download transcript: {e}")


def main():
    """Main application function."""
    # Initialize session state
    initialize_session_state()
    
    # Check backend connection
    if st.session_state.backend_connected is None:
        st.session_state.backend_connected = check_backend_connection()
    
    # Display header
    display_header()
    
    # Check if backend is connected
    if not st.session_state.backend_connected:
        display_connection_error()
        if st.button("🔄 Retry Connection"):
            st.session_state.backend_connected = check_backend_connection()
            st.rerun()
        return
    
    # Main content area
    if not st.session_state.interview_started:
        # Show setup page
        display_interview_setup()
    else:
        # Show chat interface with sidebar
        display_sidebar()
        
        # Main chat area
        st.markdown("## 💬 Interview Chat")
        display_chat_interface()
        
        # Show summary if completed
        display_interview_summary()
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #666;'>"
        "Excel Mock Interviewer • Powered by Gemini AI • Built with FastAPI + Streamlit"
        "</div>", 
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()