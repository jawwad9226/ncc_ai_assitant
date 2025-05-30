"""
NCC Assistant Pro - Main Application Entry Point

This is the main Streamlit application file that serves as the entry point for the
NCC Assistant Pro system. It handles:
- Application initialization and configuration
- User interface routing and navigation
- Session management and state persistence
- Error handling and logging
- Integration with all core modules and features

Author: NCC Assistant Pro Team
Last Updated: 2025
Version: 2.0

TODO for next developer:
1. Test all interface integrations thoroughly
2. Add more comprehensive error logging
3. Implement user authentication if needed
4. Add performance monitoring dashboard
5. Create admin panel for content management
"""

import streamlit as st
import logging
import traceback
from datetime import datetime
import os
from pathlib import Path

# Configure page settings - MUST be first Streamlit command
st.set_page_config(
    page_title="NCC Assistant Pro",
    page_icon="🎖️",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/ncc-assistant/ncc-assistant-pro',
        'Report a bug': 'https://github.com/ncc-assistant/ncc-assistant-pro/issues',
        'About': '''
        # NCC Assistant Pro v2.0
        
        Your comprehensive NCC study companion with AI-powered features:
        - Interactive study planning
        - Progressive skill assessments  
        - Real-time performance tracking
        - Certificate-specific guidance
        
        Built with ❤️ for NCC Cadets
        '''
    }
)

# Import core modules
try:
    from core.session_manager import SessionManager
    from core.gemini_client import GeminiClient
    from config.settings import AppConfig
    
    # Import interface modules
    from interfaces.dashboard import Dashboard
    from interfaces.chat_interface import ChatInterface
    from interfaces.quiz_interface import QuizInterface
    from interfaces.study_planner import StudyPlanner
    from interfaces.progress_tracker import ProgressTracker
    from interfaces.certificate_guide import CertificateGuide
    
    # Import feature modules
    from features.drill_trainer import DrillTrainer
    from features.map_reader import MapReader
    from features.first_aid_simulator import FirstAidSimulator
    from features.rank_insignia import RankInsignia
    from features.career_counselor import CareerCounselor
    
    # Import utilities
    from utils.analytics import Analytics
    from utils.data_handler import DataHandler
    
except ImportError as e:
    st.error(f"""
    **Module Import Error**: {str(e)}
    
    This usually means you need to create the required module files.
    Please refer to the project structure guide and create the missing modules.
    
    **Quick Fix**: Make sure all required files exist in the correct directories.
    """)
    st.stop()

# Configure logging
def setup_logging():
    """Configure application logging with proper formatting and levels"""
    log_level = logging.DEBUG if AppConfig.DEBUG else logging.INFO
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('ncc_assistant.log'),
            logging.StreamHandler()
        ]
    )
    
    # Create logger for this module
    logger = logging.getLogger(__name__)
    logger.info("NCC Assistant Pro application starting...")
    return logger

# Initialize logger
logger = setup_logging()

class NCCAssistantApp:
    """
    Main application class that orchestrates all components of the NCC Assistant Pro.
    
    This class manages:
    - Application initialization and configuration
    - User interface state and navigation
    - Component integration and communication
    - Error handling and recovery
    - Performance monitoring and analytics
    
    TODO for next developer:
    1. Add user authentication and role management
    2. Implement advanced caching strategies
    3. Add real-time collaboration features
    4. Create API endpoints for mobile app integration
    """
    
    def __init__(self):
        """Initialize the main application with all necessary components"""
        try:
            # Initialize core components
            self.session_manager = SessionManager()
            self.gemini_client = GeminiClient()
            self.analytics = Analytics()
            self.data_handler = DataHandler()
            
            # Initialize interface components
            self.dashboard = Dashboard()
            self.chat_interface = ChatInterface(self.gemini_client)
            self.quiz_interface = QuizInterface(self.gemini_client)
            self.study_planner = StudyPlanner(self.gemini_client)
            self.progress_tracker = ProgressTracker()
            self.certificate_guide = CertificateGuide()
            
            # Initialize feature components
            self.drill_trainer = DrillTrainer()
            self.map_reader = MapReader()
            self.first_aid_simulator = FirstAidSimulator()
            self.rank_insignia = RankInsignia()
            self.career_counselor = CareerCounselor(self.gemini_client)
            
            logger.info("All application components initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize application components: {e}")
            st.error(f"Application initialization failed: {str(e)}")
            raise
    
    def load_custom_css(self):
        """Load custom CSS styles for enhanced UI appearance"""
        try:
            css_file = Path("assets/css/custom_styles.css")
            if css_file.exists():
                with open(css_file, 'r') as f:
                    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
            else:
                # Fallback inline CSS if file doesn't exist
                st.markdown("""
                <style>
                .main-header {
                    background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
                    padding: 2rem;
                    border-radius: 15px;
                    color: white;
                    text-align: center;
                    margin-bottom: 2rem;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                }
                
                .feature-card {
                    background: white;
                    padding: 1.5rem;
                    border-radius: 12px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                    border-left: 4px solid #2a5298;
                    margin-bottom: 1.5rem;
                    transition: transform 0.2s ease;
                }
                
                .feature-card:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                }
                
                .stats-container {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 1rem;
                    margin: 2rem 0;
                }
                
                .stat-box {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 1.5rem;
                    border-radius: 12px;
                    text-align: center;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                }
                
                .sidebar-section {
                    background: #f8f9fa;
                    padding: 1rem;
                    border-radius: 8px;
                    border: 1px solid #dee2e6;
                    margin-bottom: 1rem;
                }
                
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
                
                .navigation-button {
                    width: 100%;
                    margin-bottom: 0.5rem;
                    padding: 0.75rem;
                    background: linear-gradient(135deg, #2a5298 0%, #1e3c72 100%);
                    color: white;
                    border: none;
                    border-radius: 8px;
                    cursor: pointer;
                    transition: all 0.2s ease;
                }
                
                .navigation-button:hover {
                    transform: translateY(-1px);
                    box-shadow: 0 2px 4px rgba(0,0,0,0.2);
                }
                </style>
                """, unsafe_allow_html=True)
                
        except Exception as e:
            logger.warning(f"Failed to load custom CSS: {e}")
    
    def setup_sidebar_navigation(self):
        """Setup the sidebar navigation with enhanced features and status indicators"""
        with st.sidebar:
            # Application header
            st.markdown("""
            <div style='text-align: center; padding: 1rem; background: linear-gradient(135deg, #2a5298, #1e3c72); border-radius: 10px; margin-bottom: 1rem;'>
                <h2 style='color: white; margin: 0;'>🎖️ NCC Assistant Pro</h2>
                <p style='color: #e8f4fd; margin: 0; font-size: 0.9em;'>v2.0 Enhanced Edition</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Navigation menu
            st.subheader("🧭 Navigation")
            
            # Define all available pages with icons and descriptions
            pages = {
                "🏠 Dashboard": {
                    "description": "Overview and quick stats",
                    "component": self.dashboard
                },
                "💬 AI Chat Assistant": {
                    "description": "Ask questions about NCC",
                    "component": self.chat_interface
                },
                "🎯 Knowledge Quiz": {
                    "description": "Test your NCC knowledge",
                    "component": self.quiz_interface
                },
                "📚 Study Planner": {
                    "description": "Personalized study schedules",
                    "component": self.study_planner
                },
                "📊 Progress Tracker": {
                    "description": "Track your learning progress",
                    "component": self.progress_tracker
                },
                "🎖️ Certificate Guide": {
                    "description": "A, B, C certificate guidance",
                    "component": self.certificate_guide
                },
                "🚶 Drill Trainer": {
                    "description": "Interactive drill practice",
                    "component": self.drill_trainer
                },
                "🗺️ Map Reading": {
                    "description": "Navigation skills training",
                    "component": self.map_reader
                },
                "🏥 First Aid Simulator": {
                    "description": "Medical emergency training",
                    "component": self.first_aid_simulator
                },
                "👤 Ranks & Insignia": {
                    "description": "Visual identification guide",
                    "component": self.rank_insignia
                },
                "💼 Career Counselor": {
                    "description": "Service career guidance",
                    "component": self.career_counselor
                }
            }
            
            # Get current page from session state
            if 'current_page' not in st.session_state:
                st.session_state.current_page = "🏠 Dashboard"
            
            # Create navigation buttons
            for page_name, page_info in pages.items():
                if st.button(
                    page_name,
                    key=f"nav_{page_name}",
                    help=page_info["description"],
                    use_container_width=True
                ):
                    st.session_state.current_page = page_name
                    st.rerun()
            
            # System status section
            st.markdown("---")
            st.subheader("📡 System Status")
            
            # API connection status
            api_status = self.gemini_client.check_connection()
            if api_status["connected"]:
                st.success("✅ AI System Online")
            else:
                st.error("❌ AI System Offline")
                st.caption(api_status.get("error", "Unknown error"))
            
            # Session statistics
            st.markdown("---")
            st.subheader("📊 Session Stats")
            
            session_stats = self.session_manager.get_session_stats()
            st.metric("Questions Asked", session_stats.get("questions_asked", 0))
            st.metric("Quizzes Completed", session_stats.get("quizzes_completed", 0))
            st.metric("Study Time", f"{session_stats.get('study_time_minutes', 0)} min")
            
            # Quick tips section
            st.markdown("---")
            st.subheader("💡 Daily Tip")
            
            tips = [
                "Practice drill commands daily for muscle memory",
                "Review map symbols before field exercises",
                "Master first aid basics - they save lives",
                "Leadership starts with self-discipline",
                "Physical fitness is foundation of military training",
                "Punctuality and precision define a good cadet",
                "Teamwork makes difficult tasks achievable",
                "Respect and courtesy build strong relationships"
            ]
            
            import random
            daily_tip = tips[datetime.now().day % len(tips)]
            st.info(f"💡 {daily_tip}")
            
            # Emergency help section
            st.markdown("---")
            st.subheader("🆘 Need Help?")
            
            if st.button("📞 Emergency Contacts", use_container_width=True):
                st.info("""
                **Emergency Contacts:**
                - Medical Emergency: 108
                - Fire Emergency: 101
                - Police Emergency: 100
                - NCC Unit: Contact your ANO
                """)
            
            if st.button("📖 Quick Reference", use_container_width=True):
                st.info("""
                **Quick Commands:**
                - Attention: Squad - Attention!
                - Stand at Ease: Squad - Stand at Ease!
                - Right Turn: Right - Turn!
                - Left Turn: Left - Turn!
                - Quick March: Quick - March!
                """)
    
    def render_current_page(self):
        """Render the currently selected page with proper error handling"""
        try:
            current_page = st.session_state.current_page
            
            # Map page names to components
            page_mapping = {
                "🏠 Dashboard": self.dashboard,
                "💬 AI Chat Assistant": self.chat_interface,
                "🎯 Knowledge Quiz": self.quiz_interface,
                "📚 Study Planner": self.study_planner,
                "📊 Progress Tracker": self.progress_tracker,
                "🎖️ Certificate Guide": self.certificate_guide,
                "🚶 Drill Trainer": self.drill_trainer,
                "🗺️ Map Reading": self.map_reader,
                "🏥 First Aid Simulator": self.first_aid_simulator,
                "👤 Ranks & Insignia": self.rank_insignia,
                "💼 Career Counselor": self.career_counselor
            }
            
            # Get the component for the current page
            component = page_mapping.get(current_page)
            
            if component:
                # Track page view for analytics
                self.analytics.track_page_view(current_page)
                
                # Render the component
                component.render()
            else:
                st.error(f"Page '{current_page}' not found!")
                logger.error(f"Unknown page requested: {current_page}")
                
        except Exception as e:
            st.error(f"Error rendering page: {str(e)}")
            logger.error(f"Page rendering error: {e}")
            logger.error(traceback.format_exc())
            
            # Show fallback content
            st.markdown("""
            ### 🔧 Something went wrong!
            
            We encountered an error while loading this page. Here's what you can do:
            
            1. **Try refreshing** the page
            2. **Go back to Dashboard** and try again
            3. **Check your internet connection**
            4. **Contact support** if the problem persists
            
            The error has been logged for our team to investigate.
            """)
    
    def display_footer(self):
        """Display application footer with version info and links"""
        st.markdown("---")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown("""
            <div style='text-align: center; color: #666; padding: 2rem 0;'>
                <h4>🎖️ NCC Assistant Pro v2.0</h4>
                <p>Empowering NCC Cadets with AI-powered learning tools</p>
                <p>
                    <small>
                        Made with ❤️ for the National Cadet Corps<br>
                        Jai Hind! 🇮🇳
                    </small>
                </p>
            </div>
            """, unsafe_allow_html=True)
    
    def run(self):
        """Main application entry point - orchestrates the entire application flow"""
        try:
            # Initialize session state
            self.session_manager.initialize_session()
            
            # Load custom styling
            self.load_custom_css()
            
            # Setup sidebar navigation
            self.setup_sidebar_navigation()
            
            # Render main content area
            self.render_current_page()
            
            # Display footer
            self.display_footer()
            
            # Track session activity
            self.analytics.track_session_activity()
            
        except Exception as e:
            st.error(f"Critical application error: {str(e)}")
            logger.critical(f"Critical application error: {e}")
            logger.critical(traceback.format_exc())
            
            # Show error recovery options
            st.markdown("""
            ### 🚨 Critical Error Detected
            
            The application encountered a critical error. Please try:
            
            1. **Refresh the page** (Ctrl+R or Cmd+R)
            2. **Clear browser cache** and reload
            3. **Check browser console** for additional error details
            4. **Contact support** with error details
            
            We apologize for the inconvenience!
            """)
            
            if st.button("🔄 Reset Application", type="primary"):
                # Clear session state and restart
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()

# Application entry point
def main():
    """
    Main function that initializes and runs the NCC Assistant Pro application.
    
    This function serves as the entry point when the script is run directly.
    It handles:
    - Application initialization
    - Error handling for startup issues
    - Environment validation
    - Application execution
    
    TODO for next developer:
    1. Add environment validation checks
    2. Implement health checks for external dependencies
    3. Add startup performance monitoring
    4. Create graceful shutdown handling
    """
    try:
        # Validate environment
        if not os.getenv("GEMINI_API_KEY"):
            st.error("""
            **🔑 API Key Required**
            
            Please set up your Gemini API key to use this application:
            
            1. Get your free API key from [Google AI Studio](https://ai.google.dev/)
            2. Create a `.env` file in the project root
            3. Add: `GEMINI_API_KEY=your_api_key_here`
            4. Restart the application
            
            **Alternative**: Set the environment variable directly:
            ```bash
            export GEMINI_API_KEY=your_api_key_here
            ```
            """)
            st.stop()
        
        # Initialize and run the application
        app = NCCAssistantApp()
        app.run()
        
        logger.info("Application session completed successfully")
        
    except KeyboardInterrupt:
        logger.info("Application terminated by user")
        st.stop()
        
    except Exception as e:
        logger.critical(f"Failed to start application: {e}")
        st.error(f"Failed to start NCC Assistant Pro: {str(e)}")
        
        # Show startup troubleshooting guide
        st.markdown("""
        ## 🔧 Startup Troubleshooting
        
        If you're seeing this error, try these steps:
        
        ### 1. Check Dependencies
        ```bash
        pip install -r requirements.txt
        ```
        
        ### 2. Verify File Structure
        Make sure all required files and directories exist as per the project structure.
        
        ### 3. Environment Variables
        Ensure your `.env` file is properly configured.
        
        ### 4. Python Version
        This application requires Python 3.8 or higher.
        
        ### 5. Contact Support
        If issues persist, please report them with the full error message.
        """)

if __name__ == "__main__":
    main()
