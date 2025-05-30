import streamlit as st
import google.generativeai as genai
import time
import re
from datetime import datetime, timedelta
import os
import random
from dotenv import load_dotenv
from typing import Dict, List, Optional, Tuple
from chat_interface import display_chat_interface
from quiz_interface import display_quiz_interface
from utils import get_ncc_response, generate_quiz_questions, parse_quiz_response

# Set page config must be the first Streamlit command
st.set_page_config(
    page_title="NCC AI Assistant",
    page_icon="🎖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load environment variables
load_dotenv()

# Configure Gemini
@st.cache_resource
def setup_gemini():
    """Initialize Gemini API with API key from environment variables"""
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key or api_key == "your_api_key_here":
            st.error("❌ Please set up your GEMINI_API_KEY in the .env file")
            st.stop()
        genai.configure(api_key=api_key)
        return genai.GenerativeModel('gemini-1.5-flash'), None
    except Exception as e:
        st.error(f"❌ Error initializing Gemini API: {str(e)}")
        return None, str(e)

# Initialize model and error as global variables
model = None
model_error = None

def initialize_session_state():
    """Initialize all session state variables"""
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'quiz_questions' not in st.session_state:
        st.session_state.quiz_questions = []
    if 'current_question' not in st.session_state:
        st.session_state.current_question = 0
    if 'user_answers' not in st.session_state:
        st.session_state.user_answers = {}
    if 'quiz_submitted' not in st.session_state:
        st.session_state.quiz_submitted = False
    if 'quiz_score' not in st.session_state:
        st.session_state.quiz_score = 0
    if 'quiz_completed' not in st.session_state:
        st.session_state.quiz_completed = False
    if 'quiz_topic' not in st.session_state:
        st.session_state.quiz_topic = ""
    if 'last_api_call' not in st.session_state:
        st.session_state.last_api_call = 0

def can_make_api_call() -> tuple[bool, str]:
    """Check if we can make an API call based on rate limiting"""
    if not st.session_state.last_api_call:
        return True, ""

    time_since_last = datetime.now() - st.session_state.last_api_call
    cooldown_minutes = 2  # Reduced cooldown for better UX

    if time_since_last < timedelta(minutes=cooldown_minutes):
        remaining = cooldown_minutes - (time_since_last.seconds // 60)
        return False, f"Please wait {remaining} more minute(s) before generating another quiz."

    return True, ""

def display_chat_interface(model, model_error, get_response_func, st_session_state):
    """Display the chat interface"""
    st.header("💬 NCC AI Assistant")
    
    # Initialize chat history if not exists
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Hello! I'm your NCC AI Assistant. How can I help you with NCC today?"}
        ]
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask me anything about NCC..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Display assistant response
        with st.chat_message("assistant"):
            response = get_response_func(model, model_error, prompt)
            st.markdown(response)
        
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})

def display_quiz_interface(model, model_error, generate_quiz_func, parse_quiz_func, st_session_state):
    """Display the quiz interface"""
    st.header("🎯 NCC Knowledge Quiz")
    st.write("Test your knowledge with AI-generated NCC quizzes!")

    # Quiz creation section
    if not st.session_state.get('quiz_questions') or st.session_state.get('quiz_completed', False):
        display_quiz_creation(model, model_error, generate_quiz_func, parse_quiz_func, st_session_state)
    else:
        display_active_quiz(model, model_error, generate_quiz_func, parse_quiz_func, st_session_state)

def display_quiz_creation(model, model_error, generate_quiz_func, parse_quiz_func, st_session_state):
    """Display quiz creation form"""
    st.subheader("📝 Create New Quiz")
    
    # Predefined topics
    col1, col2 = st.columns([2, 1])
    
    with col1:
        topic_options = [
            "Custom Topic",
            "Drill Commands and Procedures",
            "Map Reading and Navigation",
            "First Aid and Medical Training", 
            "Weapon Training and Safety",
            "NCC History and Organization",
            "Leadership and Discipline",
            "Adventure Activities",
            "Military Knowledge",
            "Field Craft and Camping"
        ]
        
        selected_topic = st.selectbox("Choose a topic:", topic_options)
        
        if selected_topic == "Custom Topic":
            quiz_topic = st.text_input("Enter your custom topic:", 
                                     placeholder="e.g., Signal Communications, Parade Commands")
        else:
            quiz_topic = selected_topic
    
    with col2:
        num_questions = st.number_input("Number of Questions", 
                                      min_value=3, max_value=10, value=5)
    
    # Generate button
    if st.button("🚀 Generate Quiz", type="primary", disabled=not quiz_topic):
        if quiz_topic.strip():
            questions = generate_quiz_func(quiz_topic.strip(), num_questions)
            if questions:
                st_session_state.quiz_questions = questions
                st_session_state.quiz_topic = quiz_topic.strip()
                st_session_state.current_question = 0
                st_session_state.user_answers = {}
                st_session_state.quiz_submitted = False
                st_session_state.quiz_completed = False
                st_session_state.quiz_score = 0
                st.rerun()
        else:
            st.warning("Please enter a quiz topic.")
    
    # Show rate limiting info
    if 'last_api_call' in st_session_state and st_session_state.last_api_call:
        time_since_last = datetime.now() - st_session_state.last_api_call
        if time_since_last < timedelta(minutes=2):
            remaining = 2 - (time_since_last.seconds // 60)
            st.info(f"ℹ️ Quiz generation available in {remaining} minute(s)")

def display_active_quiz(model, model_error, generate_quiz_func, parse_quiz_func, st_session_state):
    """Display the active quiz"""
    # Check if quiz is submitted and show results if true
    if st_session_state.get('quiz_submitted', False):
        show_current_answer_result(None, None, st_session_state)
        return
        
    if not st_session_state.get('quiz_questions'):
        st.warning("No quiz questions available. Please generate a quiz first.")
        return
        
    questions = st_session_state.quiz_questions
    current_idx = st_session_state.get('current_question', 0)
    
    # Ensure current index is within bounds
    if current_idx >= len(questions):
        current_idx = 0
        st_session_state.current_question = 0
    
    # Initialize answer in session state if not exists
    answer_key = f"answer_{current_idx}"
    if answer_key not in st.session_state:
        st.session_state[answer_key] = st.session_state.user_answers.get(str(current_idx), "")
    
    # Ensure the current question has the required structure
    current_question = questions[current_idx]
    if not isinstance(current_question, dict) or 'options' not in current_question:
        st.error("Invalid question format. Please generate a new quiz.")
        if st.button("Generate New Quiz"):
            reset_quiz(st_session_state)
            st.rerun()
        return

    # Quiz header
    st.subheader(f"📚 Quiz: {st_session_state.get('quiz_topic', 'General Knowledge')}")
    
    # Progress bar
    progress = (current_idx + 1) / len(questions)
    st.progress(progress)
    st.write(f"Question {current_idx + 1} of {len(questions)}")
    
    # Question display
    st.markdown(f"### {current_question.get('question', 'Question not available')}")
    
    # Get current answer if it exists
    current_answer = st.session_state[answer_key].upper()
    
    # Ensure options exist and are in the correct format
    options = current_question.get('options', {})
    option_keys = [k for k in ['A', 'B', 'C', 'D'] if k in options]
    
    if not option_keys:
        st.error("No valid options found for this question.")
        return
    
    # Use a form for the current question
    with st.form(key=f'question_form_{current_idx}'):
        # Answer options
        selected_answer = st.radio(
            "Choose your answer:",
            options=option_keys,
            format_func=lambda x: f"{x}) {options.get(x, '')}",
            key=answer_key,
            index=option_keys.index(current_answer) if current_answer in option_keys else 0
        )
        
        # Navigation buttons
        col1, col2 = st.columns([1, 2])
        
        with col1:
            if st.form_submit_button("⏮️ Previous", disabled=current_idx == 0):
                st_session_state.user_answers[str(current_idx)] = selected_answer
                st_session_state.current_question = max(0, current_idx - 1)
                st.rerun()
        
        with col2:
            if current_idx < len(questions) - 1:
                if st.form_submit_button("Next ⏭️"):
                    st_session_state.user_answers[str(current_idx)] = selected_answer
                    st_session_state.current_question = current_idx + 1
                    st.rerun()
            else:
                if st.form_submit_button("✅ Submit Quiz"):
                    st_session_state.user_answers[str(current_idx)] = selected_answer
                    st_session_state.quiz_submitted = True
                    st.rerun()
    
    # Add a new quiz button at the bottom
    if st.button("🔄 New Quiz", key="new_quiz_btn"):
        reset_quiz(st_session_state)
        st.rerun()

def calculate_and_show_results(st_session_state):
    """Calculate quiz results and display them"""
    questions = st_session_state.quiz_questions
    user_answers = st_session_state.user_answers
    
    correct_count = 0
    total_questions = len(questions)
    
    st.session_state.quiz_submitted = True
    st.session_state.quiz_completed = True
    
    # Calculate score
    for i, question in enumerate(questions):
        if user_answers.get(str(i)) == question['answer']:
            correct_count += 1
    
    score_percentage = (correct_count / total_questions) * 100
    st.session_state.quiz_score = score_percentage
    
    # Store results in session state for display
    st.session_state.quiz_results = {
        'correct_count': correct_count,
        'total_questions': total_questions,
        'score_percentage': score_percentage,
        'questions': questions,
        'user_answers': user_answers
    }

def show_current_answer_result(question: Dict, user_answer: str, st_session_state):
    """Show result for current question or quiz results"""
    if not hasattr(st_session_state, 'quiz_results'):
        # Show single question result
        if not user_answer:
            return
        
        st.markdown("---")
        
        # Create columns for better layout
        col1, col2 = st.columns([1, 20])
        
        correct_answer = question['answer']
        is_correct = user_answer.lower() == correct_answer.lower()
        
        with col1:
            if is_correct:
                st.success("✅")
            else:
                st.error("❌")
        
        with col2:
            if is_correct:
                st.success("**Correct!**")
            else:
                st.error(f"**Incorrect.** The correct answer is {correct_answer}) {question['options'][correct_answer]}")
        
        if question.get('explanation'):
            with st.expander("💡 Explanation", expanded=True):
                st.info(question['explanation'])
    else:
        # Show full quiz results
        results = st_session_state.quiz_results
        
        # Display overall results
        st.markdown("---")
        st.header("🎉 Quiz Results")
        
        # Score display with color coding
        if results['score_percentage'] >= 80:
            st.success(f"🏆 Excellent! You scored {results['correct_count']}/{results['total_questions']} ({results['score_percentage']:.1f}%)")
        elif results['score_percentage'] >= 60:
            st.warning(f"👍 Good job! You scored {results['correct_count']}/{results['total_questions']} ({results['score_percentage']:.1f}%)")
        else:
            st.error(f"📚 Keep studying! You scored {results['correct_count']}/{results['total_questions']} ({results['score_percentage']:.1f}%)")
        
        # Detailed results
        with st.expander("📊 View Detailed Results", expanded=True):
            for i, question in enumerate(results['questions']):
                user_answer = results['user_answers'].get(str(i), "No answer")
                correct_answer = question['answer']
                is_correct = user_answer.lower() == correct_answer.lower()
                
                st.markdown(f"**Question {i+1}:** {question['question']}")
                
                if is_correct:
                    st.success(f"✅ Your answer: {user_answer}) {question['options'][user_answer]}")
                else:
                    st.error(f"❌ Your answer: {user_answer}) {question['options'].get(user_answer, 'No answer')}")
                    st.info(f"✅ Correct answer: {correct_answer}) {question['options'][correct_answer]}")
                
                if question.get('explanation'):
                    st.info(f"💡 **Explanation:** {question['explanation']}")
                
                st.markdown("---")

def reset_quiz(st_session_state):
    """Reset quiz state"""
    st_session_state.quiz_questions = []
    st_session_state.current_question = 0
    st.session_state.user_answers = {}
    st.session_state.quiz_submitted = False
    st.session_state.quiz_score = 0
    st.session_state.quiz_completed = False
    st.session_state.quiz_topic = ""

def main():
    """Main application function"""
    global model, model_error
    
    # Initialize the Gemini model
    model, model_error = setup_gemini()
    
    # Initialize session state
    initialize_session_state()
    
    # Error handling for model initialization
    if not model:
        st.error(f"⚠️ **Setup Required:** {model_error}")
        st.markdown("""
        **To get started:**
        1. Get a free API key from [Google AI Studio](https://ai.google.dev/)
        2. Create a `.env` file in your project directory
        3. Add: `GEMINI_API_KEY=your_api_key_here`
        4. Restart the application
        """)
        return
    
    # Header
    st.title("🎖️ NCC AI Assistant")
    st.markdown("*Your comprehensive AI-powered NCC study companion*")
    
    # Navigation
    st.sidebar.title("🧭 Navigation")
    st.sidebar.markdown("---")
    
    # Add a unique key to the radio widget
    page = st.sidebar.radio(
        "Choose a section:",
        ["💬 Chat Assistant", "🎯 Knowledge Quiz"],
        key="nav_radio",
        label_visibility="collapsed"
    )
    
    # Page routing with required arguments
    if page == "💬 Chat Assistant":
        from utils import get_ncc_response
        display_chat_interface(
            model=model,
            model_error=model_error,
            get_response_func=get_ncc_response,
            st_session_state=st.session_state
        )
    else:
        from utils import generate_quiz_questions, parse_quiz_response
        display_quiz_interface(
            model=model,
            model_error=model_error,
            generate_quiz_func=lambda topic, num: generate_quiz_questions(model, model_error, st.session_state, topic, num),
            parse_quiz_func=parse_quiz_response,
            st_session_state=st.session_state
        )
    
    # Sidebar info
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📖 About NCC Assistant")
    st.sidebar.markdown("""
    This AI assistant helps NCC cadets with:
    - **Study Materials**: Get detailed explanations
    - **Practice Quizzes**: Test your knowledge  
    - **Quick Answers**: Ask any NCC-related questions
    - **Exam Preparation**: Comprehensive coverage
    """)
    
    # Footer
    st.sidebar.markdown("---")
    st.sidebar.markdown("*Made with ❤️ by : Jawwad*")
    st.sidebar.markdown("*Developed for NCC Cadets 🎖️*")

if __name__ == "__main__":
    main()