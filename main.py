"""
NCC Assistant Pro - Main Application Entry Point (Streamlined Version)

This is the main Streamlit application file that serves as the entry point for the
NCC Assistant Pro system. This streamlined version focuses on core functionality
with external files handling styling and complex logic.

Author: NCC Assistant Pro Team
Version: 2.0

Architecture Notes:
- All styling moved to external CSS files
- Complex UI components extracted to separate modules
- Configuration externalized to config files
- Error handling streamlined but comprehensive
- Session management simplified but effective

Next Steps for Development:
1. Create config/settings.py for app configuration
2. Create core modules (session_manager, gemini_client)
3. Build interface modules starting with quiz system
4. Add styling via external CSS files
5. Implement utilities and data handlers

TODO: The following modules need to be created in order:
- config/settings.py (basic app settings)
- config/ncc_syllabus.py (syllabus structure)
- core/session_manager.py (session handling)
- core/gemini_client.py (AI integration)
- interfaces/quiz_interface.py (first feature)
"""

import streamlit as st
import logging
import os
from datetime import datetime
from pathlib import Path

# Configure page settings - MUST be first Streamlit command
st.set_page_config(
    page_title="NCC Assistant Pro",
    page_icon="🎖️",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://ncc-assistant-pro.com/help',
        'Report a bug': 'https://ncc-assistant-pro.com/issues',
        'About': 'NCC Assistant Pro v2.0 - Your comprehensive NCC study companion'
    }
)

# Setup basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

class NCCAssistantApp:
    """
    Main application class for NCC Assistant Pro.
    
    This streamlined version handles:
    - Basic initialization and component loading
    - Navigation and routing
    - Error handling with graceful fallbacks
    - Session management integration
    
    Design Philosophy:
    - Keep main file lightweight and focused
    - Delegate complex logic to specialized modules
    - Maintain clean separation of concerns
    - Provide clear error messages and recovery options
    """
    
    def __init__(self):
        """Initialize application with error handling for missing modules"""
        self.components = {}
        self.load_components()
    
    def load_components(self):
        """
        Dynamically load application components with graceful failure handling.
        
        This approach allows the app to work even if some modules are missing,
        showing helpful messages about what needs to be created next.
        """
        # Define component loading order and requirements
        component_specs = {
            'config': {
                'settings': 'config.settings.AppConfig',
                'syllabus': 'config.ncc_syllabus.NCCSyllabus'
            },
            'core': {
                'session_manager': 'core.session_manager.SessionManager',
                'gemini_client': 'core.gemini_client.GeminiClient'
            },
            'interfaces': {
                'dashboard': 'interfaces.dashboard.Dashboard',
                'chat_interface': 'interfaces.chat_interface.ChatInterface',
                'quiz_interface': 'interfaces.quiz_interface.QuizInterface',
                'study_planner': 'interfaces.study_planner.StudyPlanner'
            },
            'features': {
                'drill_trainer': 'features.drill_trainer.DrillTrainer',
                'career_counselor': 'features.career_counselor.CareerCounselor'
            }
        }
        
        # Load each component with individual error handling
        for category, modules in component_specs.items():
            self.components[category] = {}
            for name, import_path in modules.items():
                try:
                    module_path, class_name = import_path.rsplit('.', 1)
                    module = __import__(module_path, fromlist=[class_name])
                    component_class = getattr(module, class_name)
                    self.components[category][name] = component_class()
                    logger.info(f"Loaded {category}.{name} successfully")
                except ImportError as e:
                    logger.warning(f"Module {import_path} not found: {e}")
                    self.components[category][name] = None
                except Exception as e:
                    logger.error(f"Failed to load {import_path}: {e}")
                    self.components[category][name] = None
    
    def check_critical_components(self):
        """
        Check if critical components are available and show setup guidance.
        
        Returns True if app can run, False if critical setup is needed.
        """
        # Check for API key
        api_key = os.getenv("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY")
        if not api_key:
            st.error("""
            🔑 **API Key Required**
            
            Please set up your Gemini API key:
            1. Get free API key from [Google AI Studio](https://ai.google.dev/)
            2. Add to `.env` file: `GEMINI_API_KEY=your_key_here`
            3. Or set in Streamlit secrets for cloud deployment
            """)
            return False
        
        # Check for critical missing components
        missing_critical = []
        if not self.components['core'].get('session_manager'):
            missing_critical.append('core/session_manager.py')
        if not self.components['config'].get('settings'):
            missing_critical.append('config/settings.py')
        
        if missing_critical:
            st.warning(f"""
            🔧 **Setup Required**
            
            Missing critical components:
            {chr(10).join(f'• {comp}' for comp in missing_critical)}
            
            The app will run in demo mode. Create these files to unlock full functionality.
            """)
        
        return True
    
    def setup_navigation(self):
        """Setup sidebar navigation with dynamic component detection"""
        with st.sidebar:
            # App header
            st.markdown("""
            <div style='text-align: center; padding: 1rem; background: linear-gradient(135deg, #2a5298, #1e3c72); 
                        border-radius: 10px; margin-bottom: 1rem; color: white;'>
                <h2 style='margin: 0;'>🎖️ NCC Assistant Pro</h2>
                <p style='margin: 0; opacity: 0.8;'>v2.0 Enhanced</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Navigation menu
            st.subheader("🧭 Navigation")
            
            # Define available pages based on loaded components
            available_pages = {
                "🏠 Dashboard": {
                    "component": self.components['interfaces'].get('dashboard'),
                    "description": "Overview and quick stats"
                },
                "💬 AI Chat": {
                    "component": self.components['interfaces'].get('chat_interface'),
                    "description": "Ask NCC questions"
                },
                "🎯 Knowledge Quiz": {
                    "component": self.components['interfaces'].get('quiz_interface'),
                    "description": "Test your knowledge"
                },
                "📚 Study Planner": {
                    "component": self.components['interfaces'].get('study_planner'),
                    "description": "Personalized study plans"
                },
                "🚶 Drill Trainer": {
                    "component": self.components['features'].get('drill_trainer'),
                    "description": "Practice drill commands"
                },
                "💼 Career Guide": {
                    "component": self.components['features'].get('career_counselor'),
                    "description": "Service career guidance"
                }
            }
            
            # Initialize current page
            if 'current_page' not in st.session_state:
                st.session_state.current_page = "🏠 Dashboard"
            
            # Create navigation buttons
            for page_name, page_info in available_pages.items():
                # Show different button styles based on component availability
                if page_info["component"]:
                    if st.button(page_name, key=f"nav_{page_name}", use_container_width=True):
                        st.session_state.current_page = page_name
                        st.rerun()
                else:
                    # Disabled button with tooltip for missing components
                    st.button(
                        f"{page_name} (Coming Soon)", 
                        key=f"nav_{page_name}", 
                        disabled=True,
                        use_container_width=True,
                        help=f"{page_info['description']} - Component not yet implemented"
                    )
            
            # Quick status section
            st.markdown("---")
            st.subheader("📊 Quick Stats")
            
            # Session stats (with fallback if session manager not available)
            if self.components['core'].get('session_manager'):
                try:
                    stats = self.components['core']['session_manager'].get_session_stats()
                    st.metric("Questions Asked", stats.get("questions_asked", 0))
                    st.metric("Study Time", f"{stats.get('study_minutes', 0)} min")
                except:
                    st.info("Session tracking initializing...")
            else:
                st.info("Install session manager for detailed stats")
            
            # Daily tip
            st.markdown("---")
            st.subheader("💡 Today's Tip")
            tips = [
                "Practice drill commands daily for muscle memory",
                "Review NCC aims and objectives regularly",
                "Leadership starts with self-discipline",
                "Teamwork makes difficult tasks achievable"
            ]
            daily_tip = tips[datetime.now().day % len(tips)]
            st.info(daily_tip)
    
    def render_current_page(self):
        """Render the currently selected page with error handling"""
        try:
            current_page = st.session_state.current_page
            
            # Map pages to components
            page_components = {
                "🏠 Dashboard": self.components['interfaces'].get('dashboard'),
                "💬 AI Chat": self.components['interfaces'].get('chat_interface'),
                "🎯 Knowledge Quiz": self.components['interfaces'].get('quiz_interface'),
                "📚 Study Planner": self.components['interfaces'].get('study_planner'),
                "🚶 Drill Trainer": self.components['features'].get('drill_trainer'),
                "💼 Career Guide": self.components['features'].get('career_counselor')
            }
            
            component = page_components.get(current_page)
            
            if component:
                component.render()
            else:
                # Show fallback content for missing components
                self.show_component_placeholder(current_page)
                
        except Exception as e:
            st.error(f"Error loading page: {str(e)}")
            logger.error(f"Page rendering error: {e}")
            self.show_error_recovery()
    
    def show_component_placeholder(self, page_name):
        """Show helpful placeholder when component is not available"""
        st.markdown(f"""
        ## {page_name}
        
        ### 🚧 This feature is being built!
        
        This component will provide:
        """)
        
        feature_descriptions = {
            "🏠 Dashboard": [
                "📊 Study progress overview",
                "🎯 Performance analytics", 
                "📅 Upcoming activities",
                "🏆 Achievement badges"
            ],
            "💬 AI Chat": [
                "🤖 NCC syllabus-aware AI assistant",
                "📚 Context-aware answers",
                "🎓 Study guidance",
                "❓ Interactive Q&A"
            ],
            "🎯 Knowledge Quiz": [
                "📝 Syllabus-based questions",
                "🎚️ Difficulty adaptation",
                "📈 Progress tracking",
                "🔍 Detailed explanations"
            ],
            "📚 Study Planner": [
                "📅 Personalized schedules",
                "🎯 Goal setting and tracking",
                "⏰ Study reminders",
                "📊 Progress analytics"
            ],
            "🚶 Drill Trainer": [
                "👮 Interactive drill commands",
                "🎥 Step-by-step guidance",
                "🏃 Practice sessions",
                "📋 Performance evaluation"
            ],
            "💼 Career Guide": [
                "🎯 Service selection guidance",
                "📋 Entry requirements",
                "🎓 Preparation roadmaps",
                "💡 Career insights"
            ]
        }
        
        features = feature_descriptions.get(page_name, ["Feature details coming soon..."])
        for feature in features:
            st.write(f"• {feature}")
        
        st.info("""
        **For Developers**: Create the corresponding interface/feature module to activate this page.
        Check the project README for implementation guidance.
        """)
    
    def show_error_recovery(self):
        """Show error recovery options"""
        st.markdown("""
        ### 🔧 Something went wrong!
        
        Try these recovery options:
        
        1. **Refresh the page** (F5 or Ctrl+R)
        2. **Go back to Dashboard**
        3. **Check browser console** for details
        
        If problems persist, check the application logs.
        """)
        
        if st.button("🔄 Reset Application", type="primary"):
            # Clear session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    
    def run(self):
        """Main application execution flow"""
        try:
            # Check critical components and API setup
            if not self.check_critical_components():
                st.stop()
            
            # Initialize session if manager is available
            if self.components['core'].get('session_manager'):
                self.components['core']['session_manager'].initialize_session()
            
            # Setup navigation and render current page
            self.setup_navigation()
            self.render_current_page()
            
            # Footer
            st.markdown("---")
            st.markdown("""
            <div style='text-align: center; color: #666; padding: 1rem;'>
                <small>🎖️ NCC Assistant Pro v2.0 | Made with ❤️ for NCC Cadets | Jai Hind! 🇮🇳</small>
            </div>
            """, unsafe_allow_html=True)
            
        except Exception as e:
            st.error(f"Critical application error: {str(e)}")
            logger.critical(f"Application error: {e}")
            self.show_error_recovery()

def main():
    """
    Application entry point.
    
    This function:
    1. Validates environment setup
    2. Initializes the main application
    3. Handles critical startup errors
    4. Provides setup guidance for developers
    """
    try:
        # Basic environment check
        if not Path("config").exists():
            st.warning("""
            📁 **Project Setup Needed**
            
            Creating basic directory structure...
            """)
            # Create basic directories
            for directory in ['config', 'core', 'interfaces', 'features', 'utils', 'data', 'assets']:
                Path(directory).mkdir(exist_ok=True)
                Path(f"{directory}/__init__.py").touch()
            
            st.success("✅ Basic directories created! You can now add component files.")
        
        # Initialize and run application
        app = NCCAssistantApp()
        app.run()
        
    except KeyboardInterrupt:
        logger.info("Application terminated by user")
        st.stop()
    except Exception as e:
        st.error(f"Failed to start NCC Assistant Pro: {str(e)}")
        logger.critical(f"Startup failure: {e}")
        
        st.markdown("""
        ## 🚨 Startup Error
        
        **Quick Troubleshooting:**
        1. Ensure Python 3.8+ is installed
        2. Install dependencies: `pip install -r requirements.txt`
        3. Check file permissions and directory structure
        4. Verify environment variables are set
        
        **For Developers:**
        - Check the logs above for specific error details
        - Ensure all required modules are created
        - Verify the project structure matches README.md
        """)

if __name__ == "__main__":
    main()
