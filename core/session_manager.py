"""
NCC Assistant Pro - Session Manager

This module handles session state management, user progress tracking,
and persistent data storage across the application.

Key Features:
- Session initialization and cleanup
- Progress tracking and analytics
- User preference management
- Activity logging and statistics
- Cross-session data persistence

Author: NCC Assistant Pro Team
Version: 2.0
"""

import streamlit as st
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from pathlib import Path
import uuid

logger = logging.getLogger(__name__)

class SessionManager:
    """
    Comprehensive session management for NCC Assistant Pro.
    
    Handles:
    - User session initialization and cleanup
    - Activity tracking and progress monitoring  
    - Settings and preferences management
    - Study statistics and performance analytics
    - Data persistence across sessions
    """
    
    def __init__(self):
        """Initialize session manager with default configurations"""
        self.session_timeout = timedelta(hours=2)
        self.data_dir = Path("data/sessions")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Default session structure
        self.default_session = {
            'user_id': None,
            'session_start': None,
            'last_activity': None,
            'total_study_time': 0,
            'questions_asked': 0,
            'quizzes_taken': 0,
            'quiz_scores': [],
            'topics_studied': [],
            'current_certificate_level': 'JD/JW',  # JD/JW or SD/SW
            'preferred_wing': 'common',  # common, army, navy, air
            'study_goals': {},
            'achievements': [],
            'preferences': {
                'difficulty_level': 'medium',
                'quiz_length': 10,
                'show_explanations': True,
                'daily_goal_minutes': 30
            },
            'progress': {
                'topics_completed': {},
                'overall_progress': 0,
                'current_streak': 0,
                'longest_streak': 0
            }
        }
    
    def initialize_session(self) -> None:
        """
        Initialize or restore user session with comprehensive setup.
        
        This method:
        1. Checks for existing session data
        2. Creates new session if needed
        3. Updates activity timestamps
        4. Loads user preferences and progress
        """
        try:
            # Generate or restore user ID
            if 'user_id' not in st.session_state:
                st.session_state.user_id = str(uuid.uuid4())
                logger.info(f"New user session created: {st.session_state.user_id}")
            
            # Initialize session data structure
            if 'session_data' not in st.session_state:
                st.session_state.session_data = self.default_session.copy()
                st.session_state.session_data['user_id'] = st.session_state.user_id
                st.session_state.session_data['session_start'] = datetime.now().isoformat()
            
            # Update activity timestamp
            st.session_state.session_data['last_activity'] = datetime.now().isoformat()
            
            # Load persistent data if available
            self._load_persistent_data()
            
            # Initialize page-specific session states
            self._initialize_page_states()
            
            logger.info("Session initialized successfully")
            
        except Exception as e:
            logger.error(f"Session initialization failed: {e}")
            # Fallback to basic session
            st.session_state.session_data = self.default_session.copy()
    
    def _load_persistent_data(self) -> None:
        """Load user's persistent data from storage"""
        try:
            user_file = self.data_dir / f"{st.session_state.user_id}.json"
            if user_file.exists():
                with open(user_file, 'r') as f:
                    persistent_data = json.load(f)
                
                # Merge persistent data with current session
                for key in ['quiz_scores', 'topics_studied', 'achievements', 
                           'preferences', 'progress', 'study_goals']:
                    if key in persistent_data:
                        st.session_state.session_data[key] = persistent_data[key]
                
                logger.info("Persistent data loaded successfully")
        except Exception as e:
            logger.warning(f"Could not load persistent data: {e}")
    
    def _initialize_page_states(self) -> None:
        """Initialize page-specific session states"""
        page_states = {
            'quiz_state': {
                'current_quiz': None,
                'current_question': 0,
                'answers': [],
                'start_time': None,
                'quiz_type': 'mixed'
            },
            'chat_state': {
                'conversation_history': [],
                'context': '',
                'last_query': ''
            },
            'study_state': {
                'current_topic': None,
                'study_start_time': None,
                'daily_progress': 0
            }
        }
        
        for state_name, default_state in page_states.items():
            if state_name not in st.session_state:
                st.session_state[state_name] = default_state.copy()
    
    def update_activity(self, activity_type: str, details: Dict[str, Any] = None) -> None:
        """
        Track user activity and update relevant statistics.
        
        Args:
            activity_type: Type of activity ('quiz', 'chat', 'study', etc.)
            details: Additional activity details
        """
        try:
            current_time = datetime.now()
            st.session_state.session_data['last_activity'] = current_time.isoformat()
            
            # Update activity-specific counters
            if activity_type == 'question_asked':
                st.session_state.session_data['questions_asked'] += 1
            
            elif activity_type == 'quiz_completed':
                st.session_state.session_data['quizzes_taken'] += 1
                if details and 'score' in details:
                    st.session_state.session_data['quiz_scores'].append({
                        'score': details['score'],
                        'timestamp': current_time.isoformat(),
                        'topic': details.get('topic', 'mixed'),
                        'difficulty': details.get('difficulty', 'medium')
                    })
            
            elif activity_type == 'topic_studied':
                topic = details.get('topic', 'unknown')
                if topic not in st.session_state.session_data['topics_studied']:
                    st.session_state.session_data['topics_studied'].append(topic)
            
            elif activity_type == 'study_session':
                duration = details.get('duration_minutes', 0)
                st.session_state.session_data['total_study_time'] += duration
                self._update_daily_progress(duration)
            
            # Check for achievements
            self._check_achievements()
            
            # Save progress periodically
            if st.session_state.session_data['questions_asked'] % 5 == 0:
                self.save_progress()
            
        except Exception as e:
            logger.error(f"Activity update failed: {e}")
    
    def _update_daily_progress(self, minutes: int) -> None:
        """Update daily study progress and streaks"""
        try:
            today = datetime.now().date().isoformat()
            
            # Initialize daily progress tracking
            if 'daily_progress' not in st.session_state.session_data:
                st.session_state.session_data['daily_progress'] = {}
            
            # Update today's progress
            if today not in st.session_state.session_data['daily_progress']:
                st.session_state.session_data['daily_progress'][today] = 0
            
            st.session_state.session_data['daily_progress'][today] += minutes
            
            # Update study streaks
            self._update_study_streak()
            
        except Exception as e:
            logger.error(f"Daily progress update failed: {e}")
    
    def _update_study_streak(self) -> None:
        """Calculate and update study streaks"""
        try:
            daily_goal = st.session_state.session_data['preferences']['daily_goal_minutes']
            daily_progress = st.session_state.session_data.get('daily_progress', {})
            
            # Get sorted dates
            dates = sorted(daily_progress.keys(), reverse=True)
            current_streak = 0
            
            # Calculate current streak
            for date in dates:
                if daily_progress[date] >= daily_goal:
                    current_streak += 1
                else:
                    break
            
            # Update streak records
            st.session_state.session_data['progress']['current_streak'] = current_streak
            if current_streak > st.session_state.session_data['progress']['longest_streak']:
                st.session_state.session_data['progress']['longest_streak'] = current_streak
                
        except Exception as e:
            logger.error(f"Streak update failed: {e}")
    
    def _check_achievements(self) -> None:
        """Check and award achievements based on user progress"""
        try:
            achievements = st.session_state.session_data['achievements']
            current_time = datetime.now().isoformat()
            
            # Define achievement criteria
            achievement_criteria = {
                'first_quiz': {
                    'condition': st.session_state.session_data['quizzes_taken'] >= 1,
                    'title': '🎯 First Quiz Completed',
                    'description': 'Completed your first NCC quiz'
                },
                'quiz_master': {
                    'condition': st.session_state.session_data['quizzes_taken'] >= 10,
                    'title': '🏆 Quiz Master',
                    'description': 'Completed 10 quizzes'
                },
                'curious_cadet': {
                    'condition': st.session_state.session_data['questions_asked'] >= 25,
                    'title': '❓ Curious Cadet',
                    'description': 'Asked 25 questions'
                },
                'study_streak_7': {
                    'condition': st.session_state.session_data['progress']['current_streak'] >= 7,
                    'title': '🔥 Week Warrior',
                    'description': '7-day study streak'
                },
                'high_scorer': {
                    'condition': any(score['score'] >= 90 for score in st.session_state.session_data['quiz_scores']),
                    'title': '⭐ High Scorer',
                    'description': 'Scored 90% or higher in a quiz'
                }
            }
            
            # Check each achievement
            for achievement_id, criteria in achievement_criteria.items():
                # Skip if already earned
                if any(ach['id'] == achievement_id for ach in achievements):
                    continue
                
                # Award achievement if criteria met
                if criteria['condition']:
                    new_achievement = {
                        'id': achievement_id,
                        'title': criteria['title'],
                        'description': criteria['description'],
                        'earned_at': current_time
                    }
                    achievements.append(new_achievement)
                    
                    # Show achievement notification
                    st.success(f"🎉 Achievement Unlocked: {criteria['title']}")
                    
        except Exception as e:
            logger.error(f"Achievement check failed: {e}")
    
    def get_session_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive session statistics.
        
        Returns:
            Dictionary with current session statistics
        """
        try:
            session_data = st.session_state.get('session_data', self.default_session)
            
            # Calculate session duration
            if session_data.get('session_start'):
                start_time = datetime.fromisoformat(session_data['session_start'])
                session_duration = (datetime.now() - start_time).total_seconds() / 60
            else:
                session_duration = 0
            
            # Calculate average quiz score
            quiz_scores = session_data.get('quiz_scores', [])
            avg_score = sum(score['score'] for score in quiz_scores) / len(quiz_scores) if quiz_scores else 0
            
            # Get today's study time
            today = datetime.now().date().isoformat()
            daily_progress = session_data.get('daily_progress', {})
            today_study_time = daily_progress.get(today, 0)
            
            return {
                'session_duration_minutes': round(session_duration, 1),
                'questions_asked': session_data.get('questions_asked', 0),
                'quizzes_taken': session_data.get('quizzes_taken', 0),
                'total_study_time': session_data.get('total_study_time', 0),
                'today_study_time': today_study_time,
                'average_quiz_score': round(avg_score, 1),
                'topics_studied_count': len(session_data.get('topics_studied', [])),
                'current_streak': session_data.get('progress', {}).get('current_streak', 0),
                'longest_streak': session_data.get('progress', {}).get('longest_streak', 0),
                'achievements_count': len(session_data.get('achievements', [])),
                'certificate_level': session_data.get('current_certificate_level', 'JD/JW'),
                'preferred_wing': session_data.get('preferred_wing', 'common')
            }
            
        except Exception as e:
            logger.error(f"Stats calculation failed: {e}")
            return {
                'session_duration_minutes': 0,
                'questions_asked': 0,
                'quizzes_taken': 0,
                'total_study_time': 0,
                'today_study_time': 0,
                'average_quiz_score': 0,
                'topics_studied_count': 0,
                'current_streak': 0,
                'longest_streak': 0,
                'achievements_count': 0,
                'certificate_level': 'JD/JW',
                'preferred_wing': 'common'
            }
    
    def update_preferences(self, preferences: Dict[str, Any]) -> None:
        """
        Update user preferences and settings.
        
        Args:
            preferences: Dictionary of preference updates
        """
        try:
            current_prefs = st.session_state.session_data.get('preferences', {})
            current_prefs.update(preferences)
            st.session_state.session_data['preferences'] = current_prefs
            
            # Save immediately for preference changes
            self.save_progress()
            
            logger.info("Preferences updated successfully")
            
        except Exception as e:
            logger.error(f"Preference update failed: {e}")
    
    def save_progress(self) -> None:
        """Save current session progress to persistent storage"""
        try:
            if 'session_data' not in st.session_state:
                return
            
            user_file = self.data_dir / f"{st.session_state.user_id}.json"
            
            # Prepare data for saving
            save_data = {
                'user_id': st.session_state.session_data['user_id'],
                'last_saved': datetime.now().isoformat(),
                'quiz_scores': st.session_state.session_data.get('quiz_scores', []),
                'topics_studied': st.session_state.session_data.get('topics_studied', []),
                'achievements': st.session_state.session_data.get('achievements', []),
                'preferences': st.session_state.session_data.get('preferences', {}),
                'progress': st.session_state.session_data.get('progress', {}),
                'study_goals': st.session_state.session_data.get('study_goals', {}),
                'total_study_time': st.session_state.session_data.get('total_study_time', 0),
                'daily_progress': st.session_state.session_data.get('daily_progress', {}),
                'current_certificate_level': st.session_state.session_data.get('current_certificate_level', 'JD/JW'),
                'preferred_wing': st.session_state.session_data.get('preferred_wing', 'common')
            }
            
            with open(user_file, 'w') as f:
                json.dump(save_data, f, indent=2)
            
            logger.info("Progress saved successfully")
            
        except Exception as e:
            logger.error(f"Progress save failed: {e}")
    
    def get_user_preferences(self) -> Dict[str, Any]:
        """Get current user preferences"""
        return st.session_state.session_data.get('preferences', self.default_session['preferences'])
    
    def get_study_progress(self) -> Dict[str, Any]:
        """Get detailed study progress information"""
        try:
            progress_data = st.session_state.session_data.get('progress', {})
            
            # Calculate overall progress based on topics studied
            total_topics = 50  # Approximate total topics in NCC syllabus
            topics_studied = len(st.session_state.session_data.get('topics_studied', []))
            overall_progress = min(100, (topics_studied / total_topics) * 100)
            
            return {
                'overall_progress': round(overall_progress, 1),
                'topics_completed': progress_data.get('topics_completed', {}),
                'current_streak': progress_data.get('current_streak', 0),
                'longest_streak': progress_data.get('longest_streak', 0),
                'recent_topics': st.session_state.session_data.get('topics_studied', [])[-5:],
                'quiz_performance': self._get_quiz_performance_summary()
            }
            
        except Exception as e:
            logger.error(f"Progress calculation failed: {e}")
            return {
                'overall_progress': 0,
                'topics_completed': {},
                'current_streak': 0,
                'longest_streak': 0,
                'recent_topics': [],
                'quiz_performance': {}
            }
    
    def _get_quiz_performance_summary(self) -> Dict[str, Any]:
        """Calculate quiz performance summary"""
        try:
            quiz_scores = st.session_state.session_data.get('quiz_scores', [])
            
            if not quiz_scores:
                return {'average': 0, 'best': 0, 'recent_trend': 'stable'}
            
            scores = [score['score'] for score in quiz_scores]
            average_score = sum(scores) / len(scores)
            best_score = max(scores)
            
            # Calculate trend (last 5 vs previous 5)
            if len(scores) >= 10:
                recent_avg = sum(scores[-5:]) / 5
                previous_avg = sum(scores[-10:-5]) / 5
                if recent_avg > previous_avg + 5:
                    trend = 'improving'
                elif recent_avg < previous_avg - 5:
                    trend = 'declining'
                else:
                    trend = 'stable'
            else:
                trend = 'insufficient_data'
            
            return {
                'average': round(average_score, 1),
                'best': best_score,
                'total_quizzes': len(quiz_scores),
                'recent_trend': trend
            }
            
        except Exception as e:
            logger.error(f"Quiz performance calculation failed: {e}")
            return {'average': 0, 'best': 0, 'recent_trend': 'stable'}
    
    def cleanup_session(self) -> None:
        """Cleanup session data and save final progress"""
        try:
            # Save final progress
            self.save_progress()
            
            # Log session summary
            stats = self.get_session_stats()
            logger.info(f"Session ended - Duration: {stats['session_duration_minutes']} min, "
                       f"Questions: {stats['questions_asked']}, Quizzes: {stats['quizzes_taken']}")
            
        except Exception as e:
            logger.error(f"Session cleanup failed: {e}")
    
    def reset_progress(self, reset_type: str = 'partial') -> None:
        """
        Reset user progress data.
        
        Args:
            reset_type: 'partial' (keep preferences) or 'complete' (reset all)
        """
        try:
            if reset_type == 'complete':
                st.session_state.session_data = self.default_session.copy()
                st.session_state.session_data['user_id'] = st.session_state.user_id
            else:
                # Partial reset - keep preferences and achievements
                preferences = st.session_state.session_data.get('preferences', {})
                achievements = st.session_state.session_data.get('achievements', [])
                
                st.session_state.session_data = self.default_session.copy()
                st.session_state.session_data['user_id'] = st.session_state.user_id
                st.session_state.session_data['preferences'] = preferences
                st.session_state.session_data['achievements'] = achievements
            
            # Save reset data
            self.save_progress()
            
            logger.info(f"Progress reset completed: {reset_type}")
            
        except Exception as e:
            logger.error(f"Progress reset failed: {e}")
