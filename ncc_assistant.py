"""
NCC AI Assistant Pro - Enhanced Version
A comprehensive AI-powered study companion for NCC cadets
Author: Enhanced by Claude
Version: 3.0
"""

import streamlit as st
import google.generativeai as genai
import time
import os
import json
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv
from typing import Dict, List, Optional, Tuple
import logging
import sqlite3
import hashlib
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path

# Import custom modules
from utils.gemini_client import GeminiClient
from utils.database import DatabaseManager
from utils.auth import AuthManager
from interfaces.chat_interface import ChatInterface
from interfaces.quiz_interface import QuizInterface
from interfaces.study_materials import StudyMaterials
from interfaces.practice_tests import PracticeTests
from interfaces.progress_tracker import ProgressTracker
from interfaces.flashcards import FlashcardInterface
from config.settings import AppConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/ncc_assistant.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class NCCAssistantApp:
    """Main application class for NCC AI Assistant"""
    
    def __init__(self):
        self.config = AppConfig()
        self.setup_directories()
        self.load_environment()
        self.setup_page_config()
        self.initialize_components()
        
    def setup_directories(self):
        """Create necessary directories"""
        directories = ['logs', 'data', 'exports', 'uploads', 'cache']
        for directory in directories:
            Path(directory).mkdir(exist_ok=True)
    
    def load_environment(self):
        """Load environment variables"""
        load_dotenv()
        
    def setup_page_config(self):
        """Set up Streamlit page configuration"""
        st.set_page_config(
            page_title="NCC AI Assistant Pro",
            page_icon="🎖️",
            layout="wide",
            initial_sidebar_state="expanded",
            menu_items={
                'Get Help': 'https://github.com/ncc-assistant/help',
                'Report a bug': 'https://github.com/ncc-assistant/issues',
                'About': '# NCC AI Assistant Pro\n\nYour comprehensive NCC study companion with AI-powered features.'
            }
        )
        
    def initialize_components(self):
        """Initialize application components"""
        try:
            # Initialize core components
            self.db_manager = DatabaseManager()
            self.auth_manager = AuthManager(self.db_manager)
            self.gemini_client = GeminiClient()
            
            # Initialize interfaces
            self.chat_interface = ChatInterface(self.gemini_client, self.db_manager)
            self.quiz_interface = QuizInterface(self.gemini_client, self.db_manager)
            self.study_materials = StudyMaterials(self.db_manager)
            self.practice_tests = PracticeTests(self.gemini_client, self.db_manager)
            self.progress_tracker = ProgressTracker(self.db_manager)
            self.flashcard_interface = FlashcardInterface(self.gemini_client, self.db_manager)
            
            # Initialize session state
            self.initialize_session_state()
            
        except Exception as e:
            logger.error(f"Error initializing components: {e}")
            st.error(f"Initialization Error: {e}")
    
    def initialize_session_state(self):
        """Initialize session state variables"""
        defaults = {
            # User session
            'user_id': None,
            'username': None,
            'is_authenticated': False,
            
            # Navigation
            'current_page': '🏠 Dashboard',
            'previous_page': None,
            
            # Chat state
            'chat_messages': [],
            'chat_session_id': None,
            
            # Quiz state
            'current_quiz': None,
            'quiz_in_progress': False,
            'quiz_results': [],
            
            # Study state
            'current_study_session': None,
            'study_time_start': None,
            'total_study_time': 0,
            
            # Flashcards state
            'current_deck': None,
            'flashcard_session': None,
            
            # Practice test state
            'practice_test_active': False,
            'practice_test_data': None,
            
            # Settings
            'theme': 'light',
            'difficulty_level': 'intermediate',
            'notifications_enabled': True,
            'sound_enabled': True,
            
            # Performance tracking
            'daily_goals': {'questions': 10, 'study_time': 30},
            'achievements': [],
            'streak_count': 0,
            
            # API management
            'api_calls_today': 0,
            'last_api_reset': datetime.now().date(),
        }
        
        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value
    
    def load_custom_css(self):
        """Load custom CSS for enhanced UI"""
        css = """
        <style>
        /* Import Google Fonts */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        /* Global Styles */
        .main {
            font-family: 'Inter', sans-serif;
        }
        
        /* Header Styles */
        .main-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 2rem;
            border-radius: 15px;
            color: white;
            text-align: center;
            margin-bottom: 2rem;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        
        .main-header h1 {
            margin: 0;
            font-size: 2.5rem;
            font-weight: 700;
        }
        
        .main-header p {
            margin: 0.5rem 0 0 0;
            font-size: 1.1rem;
            opacity: 0.9;
        }
        
        /* Card Styles */
        .feature-card {
            background: white;
            padding: 1.5rem;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            border: 1px solid #e1e5e9;
            margin-bottom: 1rem;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        
        .feature-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 30px rgba(0,0,0,0.15);
        }
        
        /* Stats Cards */
        .stats-container {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin: 2rem 0;
        }
        
        .stat-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1.5rem;
            border-radius: 12px;
            text-align: center;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        }
        
        .stat-card h3 {
            margin: 0;
            font-size: 2rem;
            font-weight: 700;
        }
        
        .stat-card p {
            margin: 0.5rem 0 0 0;
            opacity: 0.9;
        }
        
        /* Progress Bars */
        .progress-container {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 1rem;
            margin: 1rem 0;
        }
        
        .progress-bar {
            background: #e9ecef;
            border-radius: 10px;
            height: 8px;
            overflow: hidden;
        }
        
        .progress-fill {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            height: 100%;
            transition: width 0.3s ease;
        }
        
        /* Achievement Badges */
        .achievement-badge {
            display: inline-block;
            background: linear-gradient(135deg, #ffd700 0%, #ffed4a 100%);
            color: #333;
            padding: 0.5rem 1rem;
            border-radius: 20px;
            margin: 0.25rem;
            font-size: 0.85rem;
            font-weight: 600;
            box-shadow: 0 2px 10px rgba(255, 215, 0, 0.3);
        }
        
        /* Sidebar Styles */
        .sidebar .sidebar-content {
            background: #f8f9fa;
        }
        
        /* Button Styles */
        .stButton > button {
            border-radius: 8px;
            border: none;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            font-weight: 500;
            transition: all 0.2s ease;
        }
        
        .stButton > button:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        }
        
        /* Alert Styles */
        .success-alert {
            background: #d4edda;
            border: 1px solid #c3e6cb;
            color: #155724;
            padding: 1rem;
            border-radius: 8px;
            margin: 1rem 0;
        }
        
        .warning-alert {
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            color: #856404;
            padding: 1rem;
            border-radius: 8px;
            margin: 1rem 0;
        }
        
        .error-alert {
            background: #f8d7da;
            border: 1px solid #f5c6cb;
            color: #721c24;
            padding: 1rem;
            border-radius: 8px;
            margin: 1rem 0;
        }
        
        /* Dark Mode Support */
        @media (prefers-color-scheme: dark) {
            .feature-card {
                background: #2d3748;
                border-color: #4a5568;
                color: white;
            }
        }
        
        /* Responsive Design */
        @media (max-width: 768px) {
            .main-header {
                padding: 1rem;
            }
            
            .main-header h1 {
                font-size: 2rem;
            }
            
            .stats-container {
                grid-template-columns: 1fr;
            }
        }
        
        /* Animation for loading states */
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
        
        .loading {
            animation: pulse 2s infinite;
        }
        </style>
        """
        st.markdown(css, unsafe_allow_html=True)
    
    def render_header(self):
        """Render application header"""
        st.markdown("""
        <div class="main-header">
            <h1>🎖️ NCC AI Assistant Pro</h1>
            <p>Your Complete AI-Powered NCC Study Companion</p>
        </div>
        """, unsafe_allow_html=True)
    
    def render_sidebar(self):
        """Render enhanced sidebar"""
        with st.sidebar:
            # User authentication section
            if not st.session_state.is_authenticated:
                self.render_auth_section()
            else:
                self.render_user_section()
            
            st.markdown("---")
            
            # Navigation
            self.render_navigation()
            
            st.markdown("---")
            
            # Quick stats
            self.render_quick_stats()
            
            st.markdown("---")
            
            # System status
            self.render_system_status()
            
            st.markdown("---")
            
            # Daily tip
            self.render_daily_tip()
    
    def render_auth_section(self):
        """Render authentication section"""
        st.subheader("🔐 Login")
        
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            
            col1, col2 = st.columns(2)
            
            with col1:
                login_clicked = st.form_submit_button("Login", use_container_width=True)
            
            with col2:
                register_clicked = st.form_submit_button("Register", use_container_width=True)
        
        if login_clicked and username and password:
            if self.auth_manager.authenticate_user(username, password):
                st.session_state.is_authenticated = True
                st.session_state.username = username
                st.session_state.user_id = self.auth_manager.get_user_id(username)
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Invalid credentials")
        
        if register_clicked and username and password:
            if self.auth_manager.register_user(username, password):
                st.success("Registration successful! Please login.")
            else:
                st.error("Registration failed. Username may already exist.")
    
    def render_user_section(self):
        """Render user section for authenticated users"""
        st.subheader(f"👋 Welcome, {st.session_state.username}!")
        
        # User stats
        user_stats = self.progress_tracker.get_user_stats(st.session_state.user_id)
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Level", user_stats.get('level', 1))
        with col2:
            st.metric("XP", user_stats.get('xp', 0))
        
        # Progress bar for current level
        current_xp = user_stats.get('xp', 0)
        next_level_xp = (user_stats.get('level', 1) * 100)
        progress = min(current_xp / next_level_xp, 1.0)
        
        st.progress(progress)
        st.caption(f"{current_xp}/{next_level_xp} XP to next level")
        
        if st.button("🚪 Logout", use_container_width=True):
            for key in ['is_authenticated', 'username', 'user_id']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
    
    def render_navigation(self):
        """Render navigation menu"""
        st.subheader("🧭 Navigation")
        
        pages = [
            ("🏠", "Dashboard"),
            ("💬", "Chat Assistant"),
            ("🎯", "Knowledge Quiz"),
            ("📚", "Study Materials"),
            ("📝", "Practice Tests"),
            ("🎴", "Flashcards"),
            ("📊", "Progress Tracker"),
            ("⚙️", "Settings")
        ]
        
        for icon, page_name in pages:
            full_page_name = f"{icon} {page_name}"
            if st.button(full_page_name, use_container_width=True, 
                        key=f"nav_{page_name.lower().replace(' ', '_')}"):
                st.session_state.previous_page = st.session_state.current_page
                st.session_state.current_page = full_page_name
                st.rerun()
    
    def render_quick_stats(self):
        """Render quick statistics"""
        st.subheader("📊 Today's Progress")
        
        if st.session_state.is_authenticated:
            today_stats = self.progress_tracker.get_daily_stats(st.session_state.user_id)
            
            # Questions answered today
            questions_today = today_stats.get('questions_answered', 0)
            questions_goal = st.session_state.daily_goals['questions']
            st.metric("Questions", f"{questions_today}/{questions_goal}")
            
            # Study time today
            study_time = today_stats.get('study_time', 0)
            study_goal = st.session_state.daily_goals['study_time']
            st.metric("Study Time", f"{study_time}m/{study_goal}m")
            
            # Streak
            streak = today_stats.get('streak', 0)
            st.metric("Streak", f"{streak} days", delta=1 if streak > 0 else 0)
        else:
            st.info("Login to track your progress!")
    
    def render_system_status(self):
        """Render system status"""
        st.subheader("🔧 System Status")
        
        # API Status
        if self.gemini_client.is_available():
            st.success("✅ AI Assistant Online")
        else:
            st.error("❌ AI Assistant Offline")
        
        # Database Status
        if self.db_manager.is_connected():
            st.success("✅ Database Connected")
        else:
            st.error("❌ Database Error")
        
        # API Usage
        api_usage = st.session_state.api_calls_today
        st.metric("API Calls Today", api_usage)
    
    def render_daily_tip(self):
        """Render daily tip"""
        st.subheader("💡 Daily Tip")
        
        tips = [
            "Practice drill commands daily for muscle memory",
            "Review map reading skills regularly",
            "Master first aid basics - they're essential",
            "Understand leadership principles deeply",
            "Learn military terminology and abbreviations",
            "Practice weapon handling safety procedures",
            "Study NCC history and traditions",
            "Develop physical fitness consistently",
            "Learn communication skills and protocols",
            "Understand disaster management procedures"
        ]
        
        tip_index = datetime.now().day % len(tips)
        st.info(tips[tip_index])
    
    def render_dashboard(self):
        """Render main dashboard"""
        # Welcome message
        if st.session_state.is_authenticated:
            st.markdown(f"## Welcome back, {st.session_state.username}! 👋")
        else:
            st.markdown("## Welcome to NCC AI Assistant Pro! 🎖️")
            st.info("👆 Please login from the sidebar to access all features and track your progress.")
        
        # Quick stats cards
        if st.session_state.is_authenticated:
            self.render_dashboard_stats()
        
        # Recent activity
        self.render_recent_activity()
        
        # Quick actions
        self.render_quick_actions()
        
        # Featured content
        self.render_featured_content()
    
    def render_dashboard_stats(self):
        """Render dashboard statistics"""
        st.markdown("### 📊 Your Progress Overview")
        
        user_stats = self.progress_tracker.get_comprehensive_stats(st.session_state.user_id)
        
        # Create stats grid
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("""
            <div class="stat-card">
                <h3>{}</h3>
                <p>Questions Answered</p>
            </div>
            """.format(user_stats.get('total_questions', 0)), unsafe_allow_html=True)
        
        with col2:
            accuracy = user_stats.get('accuracy', 0)
            st.markdown("""
            <div class="stat-card">
                <h3>{:.1f}%</h3>
                <p>Accuracy Rate</p>
            </div>
            """.format(accuracy), unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div class="stat-card">
                <h3>{}</h3>
                <p>Quizzes Completed</p>
            </div>
            """.format(user_stats.get('quizzes_completed', 0)), unsafe_allow_html=True)
        
        with col4:
            study_hours = user_stats.get('study_time', 0) // 60
            st.markdown("""
            <div class="stat-card">
                <h3>{}h</h3>
                <p>Total Study Time</p>
            </div>
            """.format(study_hours), unsafe_allow_html=True)
        
        # Progress chart
        if user_stats.get('daily_progress'):
            st.markdown("### 📈 7-Day Progress")
            self.render_progress_chart(user_stats['daily_progress'])
    
    def render_progress_chart(self, daily_data):
        """Render progress chart"""
        df = pd.DataFrame(daily_data)
        
        fig = px.line(df, x='date', y='questions_answered', 
                     title='Daily Questions Answered',
                     markers=True)
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
        )
        st.plotly_chart(fig, use_container_width=True)
    
    def render_recent_activity(self):
        """Render recent activity section"""
        st.markdown("### 📝 Recent Activity")
        
        if st.session_state.is_authenticated:
            activities = self.progress_tracker.get_recent_activities(st.session_state.user_id, limit=5)
            
            if activities:
                for activity in activities:
                    with st.expander(f"{activity['type']} - {activity['timestamp']}"):
                        st.write(activity['description'])
                        if activity.get('score'):
                            st.metric("Score", f"{activity['score']:.1f}%")
            else:
                st.info("No recent activity. Start studying to see your progress here!")
        else:
            st.info("Login to see your recent activity.")
    
    def render_quick_actions(self):
        """Render quick action buttons"""
        st.markdown("### 🚀 Quick Actions")
        
        col1, col2, col3, col4 = st.columns(4)
        
        actions = [
            ("📚 Study Now", "📚 Study Materials", "Start a focused study session"),
            ("🎯 Take Quiz", "🎯 Knowledge Quiz", "Test your knowledge"),
            ("📝 Practice Test", "📝 Practice Tests", "Full-length practice exam"),
            ("🎴 Flashcards", "🎴 Flashcards", "Quick review with flashcards")
        ]
        
        for i, (button_text, page, description) in enumerate(actions):
            with [col1, col2, col3, col4][i]:
                st.markdown(f"""
                <div class="feature-card">
                    <h4>{button_text}</h4>
                    <p>{description}</p>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button(f"Start {button_text.split()[-1]}", 
                           key=f"quick_action_{i}", 
                           use_container_width=True):
                    st.session_state.current_page = page
                    st.rerun()
    
    def render_featured_content(self):
        """Render featured content section"""
        st.markdown("### ⭐ Featured Content")
        
        # NCC Updates
        with st.expander("📢 Latest NCC Updates", expanded=True):
            st.markdown("""
            - **New Training Modules**: Advanced leadership and communication skills
            - **Camp Updates**: Summer camp registrations now open
            - **Certificate Requirements**: Updated guidelines for A, B, C certificates
            - **Equipment Updates**: New drill procedures and weapon handling protocols
            """)
        
        # Study tips
        with st.expander("📖 Study Tips & Resources"):
            st.markdown("""
            **Effective Study Strategies for NCC:**
            1. **Daily Practice**: Spend 15-20 minutes daily on drill commands
            2. **Visual Learning**: Use maps and diagrams for field craft
            3. **Group Study**: Practice leadership scenarios with peers
            4. **Regular Testing**: Take quizzes weekly to assess progress
            5. **Practical Application**: Join camps and outdoor activities
            """)
    
    def route_pages(self):
        """Handle page routing"""
        current_page = st.session_state.current_page
        
        if current_page == "🏠 Dashboard":
            self.render_dashboard()
        elif current_page == "💬 Chat Assistant":
            self.chat_interface.render()
        elif current_page == "🎯 Knowledge Quiz":
            self.quiz_interface.render()
        elif current_page == "📚 Study Materials":
            self.study_materials.render()
        elif current_page == "📝 Practice Tests":
            self.practice_tests.render()
        elif current_page == "🎴 Flashcards":
            self.flashcard_interface.render()
        elif current_page == "📊 Progress Tracker":
            self.progress_tracker.render()
        elif current_page == "⚙️ Settings":
            self.render_settings()
        else:
            self.render_dashboard()
    
    def render_settings(self):
        """Render settings page"""
        st.header("⚙️ Settings & Preferences")
        
        if not st.session_state.is_authenticated:
            st.warning("Please login to access settings.")
            return
        
        tabs = st.tabs(["👤 Profile", "🎯 Study Preferences", "📊 Progress", "🔧 System", "💾 Data"])
        
        with tabs[0]:
            self.render_profile_settings()
        
        with tabs[1]:
            self.render_study_preferences()
        
        with tabs[2]:
            self.render_progress_settings()
        
        with tabs[3]:
            self.render_system_settings()
        
        with tabs[4]:
            self.render_data_management()
    
    def render_profile_settings(self):
        """Render profile settings"""
        st.subheader("👤 Profile Settings")
        
        # User info form
        with st.form("profile_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                display_name = st.text_input("Display Name", value=st.session_state.username)
                email = st.text_input("Email", placeholder="your.email@example.com")
                phone = st.text_input("Phone", placeholder="+91 XXXXX XXXXX")
            
            with col2:
                ncc_unit = st.text_input("NCC Unit", placeholder="e.g., 1 Maharashtra Battalion")
                certificate_level = st.selectbox("Certificate Level", 
                                               ["A Certificate", "B Certificate", "C Certificate"])
                year_of_joining = st.number_input("Year of Joining NCC", 
                                               min_value=2010, max_value=datetime.now().year)
            
            if st.form_submit_button("Update Profile"):
                profile_data = {
                    'display_name': display_name,
                    'email': email,
                    'phone': phone,
                    'ncc_unit': ncc_unit,
                    'certificate_level': certificate_level,
                    'year_of_joining': year_of_joining
                }
                
                if self.db_manager.update_user_profile(st.session_state.user_id, profile_data):
                    st.success("Profile updated successfully!")
                else:
                    st.error("Failed to update profile.")
    
    def render_study_preferences(self):
        """Render study preferences"""
        st.subheader("🎯 Study Preferences")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Difficulty Settings**")
            difficulty = st.select_slider(
                "Default Difficulty Level",
                options=["Beginner", "Intermediate", "Advanced"],
                value=st.session_state.difficulty_level.title()
            )
            st.session_state.difficulty_level = difficulty.lower()
            
            st.markdown("**Study Goals**")
            daily_questions = st.number_input("Daily Questions Goal", 
                                            min_value=1, max_value=50, 
                                            value=st.session_state.daily_goals['questions'])
            daily_study_time = st.number_input("Daily Study Time (minutes)", 
                                             min_value=5, max_value=180, 
                                             value=st.session_state.daily_goals['study_time'])
        
        with col2:
            st.markdown("**Notification Settings**")
            notifications = st.checkbox("Enable Notifications", 
                                      value=st.session_state.notifications_enabled)
            sound_effects = st.checkbox("Enable Sound Effects", 
                                      value=st.session_state.sound_enabled)
            
            st.markdown("**Focus Areas**")
            focus_areas = st.multiselect(
                "Select your focus areas:",
                ["Drill Commands", "Map Reading", "First Aid", "Weapon Training",
                 "Leadership", "Military History", "Adventure Activities", 
                 "Disaster Management", "Social Service", "Environment"],
                default=["Drill Commands", "First Aid", "Leadership"]
            )
        
        if st.button("Save Preferences"):
            preferences = {
                'difficulty_level': difficulty.lower(),
                'daily_questions_goal': daily_questions,
                'daily_study_time_goal': daily_study_time,
                'notifications_enabled': notifications,
                'sound_enabled': sound_effects,
                'focus_areas': focus_areas
            }
            
            # Update session state
            st.session_state.daily_goals = {
                'questions': daily_questions,
                'study_time': daily_study_time
            }
            st.session_state.notifications_enabled = notifications
            st.session_state.sound_enabled = sound_effects
            
            # Save to database
            if self.db_manager.update_user_preferences(st.session_state.user_id, preferences):
                st.success("Preferences saved successfully!")
            else:
                st.error("Failed to save preferences.")
    
    def render_progress_settings(self):
        """Render progress settings"""
        st.subheader("📊 Progress Settings
