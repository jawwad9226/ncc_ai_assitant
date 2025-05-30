import streamlit as st
import google.generativeai as genai
import time
import os
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
from typing import Dict, List, Optional, Tuple
import logging

# Import custom modules
from utils import (
    setup_gemini, get_ncc_response, generate_quiz_questions, 
    parse_quiz_response, export_chat_history, import_chat_history
)
from chat_interface import display_chat_interface
from quiz_interface import display_quiz_interface
from study_materials import display_study_materials
from practice_tests import display_practice_tests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set page config must be the first Streamlit command
st.set_page_config(
    page_title="NCC AI Assistant Pro",
    page_icon="🎖️",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/your-username/ncc-assistant',
        'Report a bug': 'https://github.com/your-username/ncc-assistant/issues',
        'About': 'NCC AI Assistant - Your comprehensive study companion'
    }
)

# Load environment variables
load_dotenv()

# Custom CSS for better UI
def load_custom_css():
    st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .feature-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #2a5298;
        margin-bottom: 1rem;
    }
    
    .stats-container {
        display: flex;
        justify-content: space-around;
        margin: 1rem 0;
    }
    
    .stat-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
        min-width: 120px;
    }
    
    .sidebar-info {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #dee2e6;
    }
    
    .success-message {
        background: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 0.75rem;
        border-radius: 0.25rem;
        margin: 1rem 0;
    }
    
    .warning-message {
        background: #fff3cd;
        border: 1px solid #ffeaa7;
        color: #856404;
        padding: 0.75rem;
        border-radius: 0.25rem;
        margin: 1rem 0;
    }
    </style>
    """, unsafe_allow_html=True)

@st.cache_resource
def setup_gemini_cached():
    """Initialize Gemini API with caching"""
    return setup_gemini()

def initialize_session_state():
    """Initialize all session state variables with better structure"""
    defaults = {
        # Chat state
        'messages': [{"role": "assistant", "content": "🎖️ Welcome to NCC AI Assistant Pro! I'm here to help you with all aspects of NCC training. How can I assist you today?"}],
        'chat_sessions': {},
        'current_session_id': 'default',
        
        # Quiz state
        'quiz_questions': [],
        'current_question': 0,
        'user_answers': {},
        'quiz_submitted': False,
        'quiz_score': 0,
        'quiz_completed': False,
        'quiz_topic': "",
        'quiz_history': [],
        
        # Practice test state
        'practice_test_active': False,
        'practice_test_questions': [],
        'practice_test_answers': {},
        'practice_test_time_limit': 30,
        'practice_test_start_time': None,
        
        # Study materials state
        'bookmarks': [],
        'study_progress': {},
        'notes': {},
        
        # API management
        'last_api_call': None,
        'api_call_count': 0,
        'daily_quota_used': 0,
        'daily_quota_reset': datetime.now().date(),
        
        # User preferences
        'theme': 'light',
        'difficulty_level': 'intermediate',
        'preferred_topics': [],
        
        # Statistics
        'total_questions_answered': 0,
        'correct_answers': 0,
        'study_time': 0,
        'certificates_studied': [],
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def check_api_quota():
    """Enhanced API quota management"""
    today = datetime.now().date()
    
    # Reset daily quota if it's a new day
    if st.session_state.daily_quota_reset != today:
        st.session_state.daily_quota_used = 0
        st.session_state.api_call_count = 0
        st.session_state.daily_quota_reset = today
    
    # Check if quota exceeded (example: 50 calls per day for free tier)
    daily_limit = 50
    if st.session_state.daily_quota_used >= daily_limit:
        return False, f"Daily API limit reached ({daily_limit} calls). Resets at midnight."
    
    return True, ""

def display_dashboard():
    """Display a comprehensive dashboard"""
    st.markdown('<div class="main-header"><h1>🎖️ NCC AI Assistant Pro</h1><p>Your Complete NCC Study Companion</p></div>', unsafe_allow_html=True)
    
    # Statistics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="stat-box">
            <h3>{st.session_state.total_questions_answered}</h3>
            <p>Questions Answered</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        accuracy = (st.session_state.correct_answers / max(st.session_state.total_questions_answered, 1)) * 100
        st.markdown(f"""
        <div class="stat-box">
            <h3>{accuracy:.1f}%</h3>
            <p>Accuracy Rate</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="stat-box">
            <h3>{len(st.session_state.quiz_history)}</h3>
            <p>Quizzes Taken</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        study_hours = st.session_state.study_time // 3600
        st.markdown(f"""
        <div class="stat-box">
            <h3>{study_hours}h</h3>
            <p>Study Time</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Recent activity
    st.subheader("📊 Recent Activity")
    if st.session_state.quiz_history:
        recent_quiz = st.session_state.quiz_history[-1]
        st.info(f"Last quiz: {recent_quiz['topic']} - Score: {recent_quiz['score']:.1f}% on {recent_quiz['date']}")
    else:
        st.info("No recent quiz activity. Start a quiz to track your progress!")
    
    # Quick actions
    st.subheader("🚀 Quick Actions")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📚 Start Study Session", use_container_width=True):
            st.session_state.page = "📚 Study Materials"
            st.rerun()
    
    with col2:
        if st.button("🎯 Take Quiz", use_container_width=True):
            st.session_state.page = "🎯 Knowledge Quiz"
            st.rerun()
    
    with col3:
        if st.button("📝 Practice Test", use_container_width=True):
            st.session_state.page = "📝 Practice Tests"
            st.rerun()
    
    with col4:
        if st.button("💬 Ask Assistant", use_container_width=True):
            st.session_state.page = "💬 Chat Assistant"
            st.rerun()

def display_settings():
    """Display user settings and preferences"""
    st.header("⚙️ Settings & Preferences")
    
    # User preferences
    st.subheader("👤 User Preferences")
    
    col1, col2 = st.columns(2)
    
    with col1:
        difficulty = st.selectbox(
            "Difficulty Level",
            ["beginner", "intermediate", "advanced"],
            index=["beginner", "intermediate", "advanced"].index(st.session_state.difficulty_level)
        )
        st.session_state.difficulty_level = difficulty
        
        certificate_focus = st.multiselect(
            "Certificate Focus",
            ["A Certificate", "B Certificate", "C Certificate"],
            default=st.session_state.certificates_studied
        )
        st.session_state.certificates_studied = certificate_focus
    
    with col2:
        preferred_topics = st.multiselect(
            "Preferred Study Topics",
            [
                "Drill Commands", "Map Reading", "First Aid", "Weapon Training",
                "Leadership", "Military History", "Adventure Activities",
                "Disaster Management", "Social Service", "Environment"
            ],
            default=st.session_state.preferred_topics
        )
        st.session_state.preferred_topics = preferred_topics
    
    # API Management
    st.subheader("🔧 API Management")
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Daily API Calls Used", st.session_state.daily_quota_used, delta=f"out of 50")
    
    with col2:
        if st.button("Reset API Counter", type="secondary"):
            st.session_state.daily_quota_used = 0
            st.session_state.api_call_count = 0
            st.success("API counter reset!")
    
    # Data Management
    st.subheader("💾 Data Management")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📥 Export Chat History"):
            chat_data = export_chat_history(st.session_state.messages)
            st.download_button(
                "Download Chat History",
                chat_data,
                "ncc_chat_history.json",
                "application/json"
            )
    
    with col2:
        uploaded_file = st.file_uploader("📤 Import Chat History", type="json")
        if uploaded_file:
            imported_messages = import_chat_history(uploaded_file)
            if imported_messages:
                st.session_state.messages = imported_messages
                st.success("Chat history imported successfully!")
    
    with col3:
        if st.button("🗑️ Clear All Data", type="secondary"):
            if st.checkbox("I understand this will delete all my progress"):
                initialize_session_state()
                st.success("All data cleared!")

def main():
    """Enhanced main application function"""
    # Load custom CSS
    load_custom_css()
    
    # Initialize session state
    initialize_session_state()
    
    # Setup Gemini model
    model, model_error = setup_gemini_cached()
    
    # Check API quota
    quota_ok, quota_message = check_api_quota()
    
    # Sidebar navigation
    with st.sidebar:
        st.title("🧭 Navigation")
        
        # Navigation options
        page_options = [
            "🏠 Dashboard",
            "💬 Chat Assistant", 
            "🎯 Knowledge Quiz",
            "📝 Practice Tests",
            "📚 Study Materials",
            "⚙️ Settings"
        ]
        
        # Get current page from session state or default
        if 'page' not in st.session_state:
            st.session_state.page = "🏠 Dashboard"
        
        current_index = page_options.index(st.session_state.page) if st.session_state.page in page_options else 0
        
        page = st.radio(
            "Choose a section:",
            page_options,
            index=current_index,
            key="nav_radio"
        )
        
        # Update session state
        st.session_state.page = page
        
        # API Status
        st.markdown("---")
        st.subheader("📡 API Status")
        if model:
            st.success("✅ Connected")
        else:
            st.error("❌ Connection Error")
            
        if not quota_ok:
            st.warning(quota_message)
        
        # Quick stats
        st.markdown("---")
        st.subheader("📊 Quick Stats")
        st.metric("Questions Today", st.session_state.api_call_count)
        st.metric("Total Study Sessions", len(st.session_state.quiz_history))
        
        # Tips
        st.markdown("---")
        st.subheader("💡 Study Tips")
        tips = [
            "Review drill commands daily",
            "Practice map reading regularly", 
            "Study first aid procedures",
            "Understand leadership principles",
            "Learn military terminology"
        ]
        tip_of_day = tips[datetime.now().day % len(tips)]
        st.info(f"💡 {tip_of_day}")
    
    # Error handling for model initialization
    if not model:
        st.error(f"⚠️ **Setup Required:** {model_error}")
        st.markdown("""
        **To get started:**
        1. Get a free API key from [Google AI Studio](https://ai.google.dev/)
        2. Create a `.env` file in your project directory
        3. Add: `GEMINI_API_KEY=your_api_key_here`
        4. Restart the application
        
        **Alternative Setup:**
        - Set the environment variable directly: `export GEMINI_API_KEY=your_key`
        - Use Streamlit secrets: Add to `.streamlit/secrets.toml`
        """)
        return
    
    # Page routing
    if page == "🏠 Dashboard":
        display_dashboard()
    elif page == "💬 Chat Assistant":
        display_chat_interface(model, model_error, get_ncc_response, st.session_state)
    elif page == "🎯 Knowledge Quiz":
        display_quiz_interface(model, model_error, generate_quiz_questions, parse_quiz_response, st.session_state)
    elif page == "📝 Practice Tests":
        display_practice_tests(model, model_error, st.session_state)
    elif page == "📚 Study Materials":
        display_study_materials(st.session_state)
    elif page == "⚙️ Settings":
        display_settings()
    
    # Footer
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div style='text-align: center; color: #666; padding: 1rem;'>
            <p>🎖️ <strong>NCC AI Assistant Pro</strong> - Made with ❤️ for NCC Cadets</p>
            <p><small>Version 2.0 | Enhanced with AI-powered features</small></p>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"Application Error: {str(e)}")
        logger.error(f"Application error: {e}", exc_info=True)
        
        # Show debug info in development
        if os.getenv("DEBUG", "false").lower() == "true":
            st.exception(e)
