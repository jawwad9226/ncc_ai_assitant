"""
NCC Assistant Pro - Application Configuration Settings

This module contains all configuration settings for the NCC Assistant Pro application.
It handles environment variables, API settings, feature flags, and application constants.

Author: NCC Assistant Pro Team
Version: 2.0
"""

import os
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

class Environment(Enum):
    """Application environment types"""
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    TESTING = "testing"

class LogLevel(Enum):
    """Logging levels"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

@dataclass
class APIConfig:
    """API-related configuration"""
    gemini_api_key: str
    max_requests_per_minute: int = 60
    request_timeout: int = 30
    retry_attempts: int = 3
    retry_delay: float = 1.0

@dataclass
class SessionConfig:
    """Session management configuration"""
    timeout_minutes: int = 30
    max_concurrent_sessions: int = 100
    enable_persistence: bool = True
    cleanup_interval_minutes: int = 5

@dataclass
class QuizConfig:
    """Quiz system configuration"""
    default_question_count: int = 10
    max_question_count: int = 50
    time_limit_minutes: int = 30
    passing_score_percentage: int = 70
    difficulty_levels: List[str] = field(default_factory=lambda: ["Easy", "Medium", "Hard"])
    question_categories: List[str] = field(default_factory=lambda: [
        "NCC Organization", "National Integration", "Foot Drill", "Weapon Training",
        "Leadership", "Disaster Management", "Social Service", "Health & Hygiene",
        "Adventure Activities", "Environment", "Self Defence"
    ])

@dataclass
class UIConfig:
    """User interface configuration"""
    theme: str = "light"
    sidebar_width: int = 300
    max_chat_history: int = 100
    auto_save_interval: int = 30
    animation_speed: str = "medium"
    show_tips: bool = True

@dataclass
class SecurityConfig:
    """Security-related configuration"""
    enable_rate_limiting: bool = True
    max_login_attempts: int = 3
    session_encryption: bool = True
    sanitize_inputs: bool = True
    allowed_file_types: List[str] = field(default_factory=lambda: [".txt", ".pdf", ".json"])

class AppConfig:
    """
    Main application configuration class.
    
    This class loads and manages all configuration settings from environment variables,
    provides default values, and validates configuration integrity.
    """
    
    def __init__(self):
        """Initialize configuration from environment variables and defaults"""
        self.environment = self._get_environment()
        self.debug = self._get_debug_mode()
        self.log_level = self._get_log_level()
        
        # Load component configurations
        self.api = self._load_api_config()
        self.session = self._load_session_config()
        self.quiz = self._load_quiz_config()
        self.ui = self._load_ui_config()
        self.security = self._load_security_config()
        
        # Application metadata
        self.app_name = "NCC Assistant Pro"
        self.app_version = "2.0"
        self.app_description = "Comprehensive NCC study companion with AI assistance"
        
        # Feature flags
        self.features = self._load_feature_flags()
        
        # Validate configuration
        self._validate_config()
    
    def _get_environment(self) -> Environment:
        """Get application environment from environment variable"""
        env_str = os.getenv("ENVIRONMENT", "development").lower()
        try:
            return Environment(env_str)
        except ValueError:
            return Environment.DEVELOPMENT
    
    def _get_debug_mode(self) -> bool:
        """Get debug mode setting"""
        return os.getenv("DEBUG", "false").lower() in ("true", "1", "yes", "on")
    
    def _get_log_level(self) -> LogLevel:
        """Get logging level"""
        level_str = os.getenv("LOG_LEVEL", "INFO").upper()
        try:
            return LogLevel(level_str)
        except ValueError:
            return LogLevel.INFO
    
    def _load_api_config(self) -> APIConfig:
        """Load API configuration"""
        # Try to get API key from multiple sources
        api_key = (
            os.getenv("GEMINI_API_KEY") or
            self._get_streamlit_secret("GEMINI_API_KEY") or
            ""
        )
        
        return APIConfig(
            gemini_api_key=api_key,
            max_requests_per_minute=int(os.getenv("API_MAX_REQUESTS", "60")),
            request_timeout=int(os.getenv("API_TIMEOUT", "30")),
            retry_attempts=int(os.getenv("API_RETRY_ATTEMPTS", "3")),
            retry_delay=float(os.getenv("API_RETRY_DELAY", "1.0"))
        )
    
    def _load_session_config(self) -> SessionConfig:
        """Load session management configuration"""
        return SessionConfig(
            timeout_minutes=int(os.getenv("SESSION_TIMEOUT", "30")),
            max_concurrent_sessions=int(os.getenv("MAX_SESSIONS", "100")),
            enable_persistence=os.getenv("SESSION_PERSISTENCE", "true").lower() == "true",
            cleanup_interval_minutes=int(os.getenv("SESSION_CLEANUP_INTERVAL", "5"))
        )
    
    def _load_quiz_config(self) -> QuizConfig:
        """Load quiz system configuration"""
        return QuizConfig(
            default_question_count=int(os.getenv("QUIZ_DEFAULT_QUESTIONS", "10")),
            max_question_count=int(os.getenv("QUIZ_MAX_QUESTIONS", "50")),
            time_limit_minutes=int(os.getenv("QUIZ_TIME_LIMIT", "30")),
            passing_score_percentage=int(os.getenv("QUIZ_PASSING_SCORE", "70"))
        )
    
    def _load_ui_config(self) -> UIConfig:
        """Load UI configuration"""
        return UIConfig(
            theme=os.getenv("UI_THEME", "light"),
            sidebar_width=int(os.getenv("UI_SIDEBAR_WIDTH", "300")),
            max_chat_history=int(os.getenv("UI_MAX_CHAT_HISTORY", "100")),
            auto_save_interval=int(os.getenv("UI_AUTO_SAVE_INTERVAL", "30")),
            animation_speed=os.getenv("UI_ANIMATION_SPEED", "medium"),
            show_tips=os.getenv("UI_SHOW_TIPS", "true").lower() == "true"
        )
    
    def _load_security_config(self) -> SecurityConfig:
        """Load security configuration"""
        return SecurityConfig(
            enable_rate_limiting=os.getenv("SECURITY_RATE_LIMITING", "true").lower() == "true",
            max_login_attempts=int(os.getenv("SECURITY_MAX_LOGIN_ATTEMPTS", "3")),
            session_encryption=os.getenv("SECURITY_SESSION_ENCRYPTION", "true").lower() == "true",
            sanitize_inputs=os.getenv("SECURITY_SANITIZE_INPUTS", "true").lower() == "true"
        )
    
    def _load_feature_flags(self) -> Dict[str, bool]:
        """Load feature flags configuration"""
        return {
            "enable_chat": os.getenv("FEATURE_CHAT", "true").lower() == "true",
            "enable_quiz": os.getenv("FEATURE_QUIZ", "true").lower() == "true",
            "enable_study_planner": os.getenv("FEATURE_STUDY_PLANNER", "true").lower() == "true",
            "enable_drill_trainer": os.getenv("FEATURE_DRILL_TRAINER", "true").lower() == "true",
            "enable_career_guide": os.getenv("FEATURE_CAREER_GUIDE", "true").lower() == "true",
            "enable_progress_tracking": os.getenv("FEATURE_PROGRESS_TRACKING", "true").lower() == "true",
            "enable_offline_mode": os.getenv("FEATURE_OFFLINE_MODE", "false").lower() == "true",
            "enable_analytics": os.getenv("FEATURE_ANALYTICS", "true").lower() == "true"
        }
    
    def _get_streamlit_secret(self, key: str) -> Optional[str]:
        """Try to get value from Streamlit secrets"""
        try:
            import streamlit as st
            return st.secrets.get(key)
        except:
            return None
    
    def _validate_config(self) -> None:
        """Validate configuration integrity"""
        errors = []
        
        # Validate API key
        if not self.api.gemini_api_key:
            errors.append("GEMINI_API_KEY is required but not set")
        
        # Validate numeric ranges
        if self.session.timeout_minutes <= 0:
            errors.append("Session timeout must be positive")
        
        if self.quiz.default_question_count <= 0:
            errors.append("Quiz question count must be positive")
        
        if self.quiz.passing_score_percentage < 0 or self.quiz.passing_score_percentage > 100:
            errors.append("Quiz passing score must be between 0 and 100")
        
        # Log validation errors
        if errors:
            import logging
            logger = logging.getLogger(__name__)
            for error in errors:
                logger.error(f"Configuration validation error: {error}")
    
    def is_feature_enabled(self, feature_name: str) -> bool:
        """Check if a specific feature is enabled"""
        return self.features.get(feature_name, False)
    
    def get_database_url(self) -> str:
        """Get database URL (for future database integration)"""
        return os.getenv("DATABASE_URL", "sqlite:///ncc_assistant.db")
    
    def get_cache_settings(self) -> Dict[str, any]:
        """Get caching configuration"""
        return {
            "enable_cache": os.getenv("ENABLE_CACHE", "true").lower() == "true",
            "cache_ttl": int(os.getenv("CACHE_TTL", "3600")),  # 1 hour default
            "max_cache_size": int(os.getenv("MAX_CACHE_SIZE", "100")),
            "cache_type": os.getenv("CACHE_TYPE", "memory")  # memory, redis, file
        }
    
    def get_logging_config(self) -> Dict[str, any]:
        """Get logging configuration"""
        return {
            "level": self.log_level.value,
            "format": os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"),
            "file_path": os.getenv("LOG_FILE_PATH", "logs/ncc_assistant.log"),
            "max_file_size": int(os.getenv("LOG_MAX_FILE_SIZE", "10485760")),  # 10MB
            "backup_count": int(os.getenv("LOG_BACKUP_COUNT", "5")),
            "enable_console": os.getenv("LOG_ENABLE_CONSOLE", "true").lower() == "true"
        }
    
    def to_dict(self) -> Dict[str, any]:
        """Convert configuration to dictionary (useful for debugging)"""
        return {
            "app_name": self.app_name,
            "app_version": self.app_version,
            "environment": self.environment.value,
            "debug": self.debug,
            "log_level": self.log_level.value,
            "features": self.features,
            "api_configured": bool(self.api.gemini_api_key),
            "session_timeout": self.session.timeout_minutes,
            "quiz_default_questions": self.quiz.default_question_count,
            "ui_theme": self.ui.theme
        }
    
    def __str__(self) -> str:
        """String representation of configuration"""
        return f"AppConfig(env={self.environment.value}, debug={self.debug}, features={len(self.features)})"

# Global configuration instance
# This can be imported and used throughout the application
config = AppConfig()

# Convenience functions for common configuration access
def get_api_key() -> str:
    """Get API key"""
    return config.api.gemini_api_key

def is_debug_mode() -> bool:
    """Check if debug mode is enabled"""
    return config.debug

def get_quiz_config() -> QuizConfig:
    """Get quiz configuration"""
    return config.quiz

def get_session_config() -> SessionConfig:
    """Get session configuration"""
    return config.session

# Export commonly used configurations
__all__ = [
    'AppConfig', 'config', 'get_api_key', 'is_debug_mode', 
    'get_quiz_config', 'get_session_config', 'Environment', 
    'LogLevel', 'APIConfig', 'SessionConfig', 'QuizConfig', 
    'UIConfig', 'SecurityConfig'
]
