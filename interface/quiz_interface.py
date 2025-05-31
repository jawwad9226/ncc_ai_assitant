"""
NCC Assistant Pro - Quiz Interface Module
==========================================

Complete quiz system with AI-generated questions, progress tracking,
and comprehensive NCC syllabus coverage.

Features:
- AI-powered question generation
- Multiple difficulty levels
- Progress tracking and analytics
- Certificate-specific content (A/B/C)
- Detailed explanations and feedback
- Session persistence
- Rate limiting and error handling

Author: NCC Assistant Pro Team
Version: 2.0 - Enhanced Architecture
"""

import streamlit as st
import json
import re
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum

# Import core modules with fallback handling
try:
    from core.gemini_client import GeminiClient
    from core.session_manager import SessionManager
    from utils.quiz_generator import QuizGenerator
    from config.ncc_syllabus import NCCSyllabus
except ImportError as e:
    # Graceful degradation when modules aren't available
    GeminiClient = None
    SessionManager = None
    QuizGenerator = None
    NCCSyllabus = None

class DifficultyLevel(Enum):
    """Quiz difficulty levels"""
    BEGINNER = "Beginner"
    INTERMEDIATE = "Intermediate" 
    ADVANCED = "Advanced"

class CertificateLevel(Enum):
    """NCC Certificate levels"""
    A_CERTIFICATE = "A Certificate (JD/JW)"
    B_CERTIFICATE = "B Certificate (SD/SW)"
    C_CERTIFICATE = "C Certificate"

@dataclass
class QuizQuestion:
    """Structure for quiz questions"""
    question: str
    options: Dict[str, str]  # {'A': 'option1', 'B': 'option2', ...}
    correct_answer: str
    explanation: str
    difficulty: str = "Intermediate"
    topic: str = ""
    certificate_level: str = "B Certificate"

@dataclass
class QuizSession:
    """Quiz session data structure"""
    questions: List[QuizQuestion]
    current_question_idx: int = 0
    user_answers: Dict[int, str] = None
    start_time: datetime = None
    end_time: Optional[datetime] = None
    topic: str = ""
    difficulty: str = "Intermediate"
    certificate_level: str = "B Certificate"
    
    def __post_init__(self):
        if self.user_answers is None:
            self.user_answers = {}
        if self.start_time is None:
            self.start_time = datetime.now()

@dataclass
class QuizResults:
    """Quiz results structure"""
    total_questions: int
    correct_answers: int
    score_percentage: float
    time_taken: timedelta
    topic: str
    difficulty: str
    certificate_level: str
    detailed_results: List[Dict]
    recommendations: List[str]

class QuizInterface:
    """
    Main Quiz Interface Class
    
    Handles all quiz-related functionality including:
    - Question generation and management
    - User interaction and navigation
    - Progress tracking and results
    - Session management
    - Error handling and recovery
    """
    
    def __init__(self):
        """Initialize quiz interface with component dependencies"""
        self.gemini_client = None
        self.session_manager = None
        self.quiz_generator = None
        self.syllabus = None
        
        # Initialize components if available
        self._initialize_components()
        
        # Quiz configuration
        self.max_questions_per_quiz = 15
        self.min_questions_per_quiz = 3
        self.rate_limit_minutes = 1  # Reduced for better UX
        
        # Predefined NCC topics organized by certificate level
        self.quiz_topics = self._get_quiz_topics()
    
    def _initialize_components(self):
        """Initialize available components with error handling"""
        try:
            if GeminiClient:
                self.gemini_client = GeminiClient()
            if SessionManager:
                self.session_manager = SessionManager()
            if QuizGenerator:
                self.quiz_generator = QuizGenerator()
            if NCCSyllabus:
                self.syllabus = NCCSyllabus()
        except Exception as e:
            st.warning(f"Some components unavailable: {e}")
    
    def _get_quiz_topics(self) -> Dict[str, List[str]]:
        """Get organized quiz topics by certificate level"""
        return {
            "A Certificate (JD/JW)": [
                "Drill and Commands",
                "First Aid Basics",
                "Map Reading Fundamentals",
                "NCC Organization and History",
                "Physical Training",
                "Basic Military Knowledge",
                "Discipline and Leadership",
                "National Integration"
            ],
            "B Certificate (SD/SW)": [
                "Advanced Drill Procedures",
                "Field Craft and Camping",
                "Weapon Training (Basic)",
                "Advanced First Aid",
                "Communication Methods",
                "Adventure Activities",
                "Service Knowledge",
                "Environmental Awareness",
                "Disaster Management",
                "Social Service"
            ],
            "C Certificate": [
                "Military History and Strategy",
                "Advanced Weapon Training",
                "Leadership and Management",
                "Navigation and Orientation",
                "Advanced Field Craft",
                "Military Law and Ethics",
                "International Relations",
                "Defense Studies",
                "Civil Defense",
                "Career Guidance in Armed Forces"
            ]
        }
    
    def render(self):
        """Main render method for the quiz interface"""
        try:
            # Page header with styling
            self._render_header()
            
            # Check system status
            if not self._check_system_status():
                self._render_setup_guidance()
                return
            
            # Initialize session state
            self._initialize_session_state()
            
            # Main quiz logic
            if self._is_quiz_active():
                self._render_active_quiz()
            elif self._has_completed_quiz():
                self._render_quiz_results()
            else:
                self._render_quiz_creation()
                
        except Exception as e:
            st.error(f"Quiz interface error: {str(e)}")
            self._render_error_recovery()
    
    def _render_header(self):
        """Render quiz interface header"""
        st.markdown("""
        <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 2rem; border-radius: 10px; margin-bottom: 2rem; color: white; text-align: center;'>
            <h1 style='margin: 0; font-size: 2.5rem;'>🎯 NCC Knowledge Quiz</h1>
            <p style='margin: 0.5rem 0 0 0; font-size: 1.2rem; opacity: 0.9;'>
                Test your NCC knowledge with AI-generated questions
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    def _check_system_status(self) -> bool:
        """Check if critical components are available"""
        if not self.gemini_client:
            return False
        return True
    
    def _render_setup_guidance(self):
        """Show setup guidance when components are missing"""
        st.error("""
        🔧 **Setup Required**
        
        The quiz system requires the Gemini AI client to generate questions.
        Please ensure:
        
        1. **API Key**: Set your `GEMINI_API_KEY` in environment variables
        2. **Dependencies**: Install required packages with `pip install -r requirements.txt`
        3. **Core Modules**: Create `core/gemini_client.py` for AI integration
        
        Check the README.md for detailed setup instructions.
        """)
        
        # Show demo mode option
        if st.button("🎮 Try Demo Mode", help="Use pre-built sample questions"):
            self._load_demo_questions()
    
    def _initialize_session_state(self):
        """Initialize quiz-related session state variables"""
        if 'quiz_session' not in st.session_state:
            st.session_state.quiz_session = None
        
        if 'quiz_results' not in st.session_state:
            st.session_state.quiz_results = None
        
        if 'last_quiz_generation' not in st.session_state:
            st.session_state.last_quiz_generation = None
        
        if 'quiz_history' not in st.session_state:
            st.session_state.quiz_history = []
    
    def _is_quiz_active(self) -> bool:
        """Check if a quiz is currently active"""
        return (st.session_state.quiz_session is not None and 
                not self._has_completed_quiz())
    
    def _has_completed_quiz(self) -> bool:
        """Check if current quiz is completed"""
        if not st.session_state.quiz_session:
            return False
        
        session = st.session_state.quiz_session
        return len(session.user_answers) >= len(session.questions)
    
    def _render_quiz_creation(self):
        """Render quiz creation interface"""
        st.subheader("📝 Create Your Quiz")
        
        # Quiz configuration form
        with st.form("quiz_config_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                # Certificate level selection
                certificate_level = st.selectbox(
                    "🎖️ Certificate Level",
                    options=list(CertificateLevel),
                    format_func=lambda x: x.value,
                    help="Choose your target NCC certificate level"
                )
                
                # Topic selection
                available_topics = self.quiz_topics.get(certificate_level.value, [])
                topic_options = ["Custom Topic"] + available_topics
                
                selected_topic = st.selectbox(
                    "📚 Quiz Topic",
                    options=topic_options,
                    help="Select a topic or choose custom to enter your own"
                )
                
                if selected_topic == "Custom Topic":
                    custom_topic = st.text_input(
                        "Enter Custom Topic",
                        placeholder="e.g., Signal Communications, Guard Duty",
                        help="Specify your custom quiz topic"
                    )
                    final_topic = custom_topic.strip()
                else:
                    final_topic = selected_topic
            
            with col2:
                # Difficulty level
                difficulty = st.selectbox(
                    "📊 Difficulty Level",
                    options=list(DifficultyLevel),
                    format_func=lambda x: x.value,
                    index=1,  # Default to Intermediate
                    help="Choose question difficulty level"
                )
                
                # Number of questions
                num_questions = st.slider(
                    "❓ Number of Questions",
                    min_value=self.min_questions_per_quiz,
                    max_value=self.max_questions_per_quiz,
                    value=7,
                    help=f"Select between {self.min_questions_per_quiz} and {self.max_questions_per_quiz} questions"
                )
                
                # Time estimate
                estimated_time = num_questions * 1.5  # 1.5 minutes per question
                st.info(f"⏱️ Estimated time: {estimated_time:.0f} minutes")
            
            # Generate quiz button
            st.markdown("---")
            
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                generate_clicked = st.form_submit_button(
                    "🚀 Generate Quiz",
                    type="primary",
                    use_container_width=True,
                    disabled=not final_topic
                )
        
        # Handle quiz generation
        if generate_clicked and final_topic:
            if self._can_generate_quiz():
                self._generate_new_quiz(
                    topic=final_topic,
                    certificate_level=certificate_level.value,
                    difficulty=difficulty.value,
                    num_questions=num_questions
                )
            else:
                remaining_time = self._get_remaining_cooldown()
                st.warning(f"⏳ Please wait {remaining_time} before generating another quiz.")
        
        # Show quiz history
        self._render_quiz_history_preview()
    
    def _can_generate_quiz(self) -> bool:
        """Check if user can generate a new quiz (rate limiting)"""
        if not st.session_state.last_quiz_generation:
            return True
        
        time_since_last = datetime.now() - st.session_state.last_quiz_generation
        return time_since_last >= timedelta(minutes=self.rate_limit_minutes)
    
    def _get_remaining_cooldown(self) -> str:
        """Get remaining cooldown time as string"""
        if not st.session_state.last_quiz_generation:
            return "0 seconds"
        
        time_since_last = datetime.now() - st.session_state.last_quiz_generation
        remaining = timedelta(minutes=self.rate_limit_minutes) - time_since_last
        
        if remaining.total_seconds() <= 0:
            return "0 seconds"
        
        minutes = int(remaining.total_seconds() // 60)
        seconds = int(remaining.total_seconds() % 60)
        
        if minutes > 0:
            return f"{minutes} minute(s) {seconds} second(s)"
        else:
            return f"{seconds} second(s)"
    
    def _generate_new_quiz(self, topic: str, certificate_level: str, 
                          difficulty: str, num_questions: int):
        """Generate a new quiz with AI"""
        try:
            with st.spinner(f"🤖 Generating {num_questions} questions about {topic}..."):
                # Generate questions using AI
                questions = self._generate_questions_with_ai(
                    topic, certificate_level, difficulty, num_questions
                )
                
                if questions:
                    # Create quiz session
                    quiz_session = QuizSession(
                        questions=questions,
                        topic=topic,
                        difficulty=difficulty,
                        certificate_level=certificate_level
                    )
                    
                    st.session_state.quiz_session = quiz_session
                    st.session_state.last_quiz_generation = datetime.now()
                    
                    st.success(f"✅ Generated {len(questions)} questions successfully!")
                    st.rerun()
                else:
                    st.error("Failed to generate questions. Please try again with a different topic.")
        
        except Exception as e:
            st.error(f"Error generating quiz: {str(e)}")
    
    def _generate_questions_with_ai(self, topic: str, certificate_level: str,
                                   difficulty: str, num_questions: int) -> List[QuizQuestion]:
        """Generate questions using AI with proper prompting"""
        if not self.gemini_client:
            return self._generate_fallback_questions(topic, num_questions)
        
        prompt = self._create_question_generation_prompt(
            topic, certificate_level, difficulty, num_questions
        )
        
        try:
            response = self.gemini_client.generate_content(prompt)
            questions = self._parse_ai_response(response, topic, difficulty, certificate_level)
            return questions[:num_questions]  # Ensure we don't exceed requested number
        
        except Exception as e:
            st.warning(f"AI generation failed: {e}. Using fallback questions.")
            return self._generate_fallback_questions(topic, num_questions)
    
    def _create_question_generation_prompt(self, topic: str, certificate_level: str,
                                         difficulty: str, num_questions: int) -> str:
        """Create detailed prompt for AI question generation"""
        return f"""
Generate exactly {num_questions} multiple-choice questions about "{topic}" for NCC cadets.

CONTEXT:
- Certificate Level: {certificate_level}
- Difficulty: {difficulty}
- Topic: {topic}

REQUIREMENTS:
1. Questions must be relevant to NCC syllabus and {certificate_level}
2. {difficulty} difficulty level appropriate for the certificate
3. Each question must have exactly 4 options (A, B, C, D)
4. Include clear explanations for correct answers
5. Cover different aspects of the topic

FORMAT (follow exactly):
```
QUESTION 1:
Q: [Clear, specific question about {topic}]
A) [First option]
B) [Second option]
C) [Third option]
D) [Fourth option]
ANSWER: [A/B/C/D]
EXPLANATION: [Why this answer is correct and relevant to NCC context]

QUESTION 2:
[Repeat format...]
```

GUIDELINES:
- Make questions practical and applicable to NCC training
- Avoid overly theoretical questions for {difficulty} level
- Include scenario-based questions when appropriate
- Ensure options are plausible but clearly distinguishable
- Keep explanations concise but informative

Generate exactly {num_questions} questions following this format.
"""
    
    def _parse_ai_response(self, response: str, topic: str, 
                          difficulty: str, certificate_level: str) -> List[QuizQuestion]:
        """Parse AI response into QuizQuestion objects"""
        questions = []
        
        # Split response into individual questions
        question_blocks = re.split(r'QUESTION \d+:', response, flags=re.IGNORECASE)
        
        for block in question_blocks[1:]:  # Skip first empty block
            question = self._parse_single_question_block(
                block.strip(), topic, difficulty, certificate_level
            )
            if question:
                questions.append(question)
        
        return questions
    
    def _parse_single_question_block(self, block: str, topic: str,
                                   difficulty: str, certificate_level: str) -> Optional[QuizQuestion]:
        """Parse a single question block into QuizQuestion object"""
        try:
            lines = [line.strip() for line in block.split('\n') if line.strip()]
            
            question_text = ""
            options = {}
            correct_answer = ""
            explanation = ""
            
            for line in lines:
                line_upper = line.upper()
                
                # Extract question
                if line_upper.startswith('Q:'):
                    question_text = line[2:].strip()
                
                # Extract options
                elif re.match(r'^[A-D]\)', line_upper):
                    option_letter = line[0].upper()
                    option_text = line[2:].strip()
                    options[option_letter] = option_text
                
                # Extract answer
                elif line_upper.startswith('ANSWER:'):
                    answer_match = re.search(r'[A-D]', line_upper)
                    if answer_match:
                        correct_answer = answer_match.group()
                
                # Extract explanation
                elif line_upper.startswith('EXPLANATION:'):
                    explanation = line[12:].strip()
            
            # Validate question completeness
            if (question_text and len(options) == 4 and 
                correct_answer and correct_answer in options):
                
                return QuizQuestion(
                    question=question_text,
                    options=options,
                    correct_answer=correct_answer,
                    explanation=explanation,
                    difficulty=difficulty,
                    topic=topic,
                    certificate_level=certificate_level
                )
        
        except Exception as e:
            st.warning(f"Error parsing question: {e}")
        
        return None
    
    def _generate_fallback_questions(self, topic: str, num_questions: int) -> List[QuizQuestion]:
        """Generate basic fallback questions when AI is unavailable"""
        fallback_questions = [
            QuizQuestion(
                question=f"What is the primary focus of {topic} in NCC training?",
                options={
                    'A': "Physical fitness only",
                    'B': "Theoretical knowledge only", 
                    'C': "Comprehensive skill development",
                    'D': "Memorization of facts"
                },
                correct_answer='C',
                explanation="NCC focuses on comprehensive skill development including practical and theoretical aspects.",
                topic=topic
            ),
            QuizQuestion(
                question=f"Which principle is most important when learning {topic}?",
                options={
                    'A': "Speed over accuracy",
                    'B': "Practice and consistency",
                    'C': "Individual effort only",
                    'D': "Avoiding mistakes"
                },
                correct_answer='B',
                explanation="Practice and consistency are fundamental to mastering any NCC skill.",
                topic=topic
            )
        ]
        
        return fallback_questions[:num_questions]
    
    def _render_active_quiz(self):
        """Render active quiz interface"""
        session = st.session_state.quiz_session
        current_idx = session.current_question_idx
        current_question = session.questions[current_idx]
        
        # Quiz progress header
        self._render_quiz_progress(session)
        
        # Current question
        with st.container():
            st.markdown(f"""
            <div style='background: white; padding: 2rem; border-radius: 10px; 
                        border-left: 5px solid #667eea; margin: 1rem 0;'>
                <h3 style='color: #333; margin-bottom: 1rem;'>
                    Question {current_idx + 1}: {current_question.question}
                </h3>
            </div>
            """, unsafe_allow_html=True)
            
            # Answer options
            with st.form(f"question_form_{current_idx}"):
                # Get current answer if exists
                current_answer = session.user_answers.get(current_idx)
                
                # Create radio buttons for options
                selected_answer = st.radio(
                    "Choose your answer:",
                    options=list(current_question.options.keys()),
                    format_func=lambda x: f"{x}) {current_question.options[x]}",
                    index=list(current_question.options.keys()).index(current_answer) if current_answer else 0,
                    key=f"answer_{current_idx}"
                )
                
                # Navigation buttons
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    prev_clicked = st.form_submit_button(
                        "⬅️ Previous",
                        disabled=current_idx == 0,
                        help="Go to previous question"
                    )
                
                with col2:
                    if current_idx < len(session.questions) - 1:
                        next_clicked = st.form_submit_button(
                            "Next ➡️",
                            help="Go to next question"
                        )
                    else:
                        next_clicked = False
                
                with col3:
                    if current_idx == len(session.questions) - 1:
                        finish_clicked = st.form_submit_button(
                            "🏁 Finish Quiz",
                            type="primary",
                            help="Complete and submit quiz"
                        )
                    else:
                        finish_clicked = False
                
                with col4:
                    restart_clicked = st.form_submit_button(
                        "🔄 Restart",
                        help="Start a new quiz"
                    )
            
            # Handle navigation
            self._handle_quiz_navigation(
                session, selected_answer, current_idx,
                prev_clicked, next_clicked, finish_clicked, restart_clicked
            )
    
    def _render_quiz_progress(self, session: QuizSession):
        """Render quiz progress indicators"""
        total_questions = len(session.questions)
        current_idx = session.current_question_idx
        answered_count = len(session.user_answers)
        
        # Progress bar
        progress = (current_idx + 1) / total_questions
        st.progress(progress)
        
        # Stats row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Question", f"{current_idx + 1}/{total_questions}")
        
        with col2:
            st.metric("Answered", f"{answered_count}/{total_questions}")
        
        with col3:
            elapsed_time = datetime.now() - session.start_time
            minutes = int(elapsed_time.total_seconds() // 60)
            st.metric("Time", f"{minutes} min")
        
        with col4:
            st.metric("Topic", session.topic)
    
    def _handle_quiz_navigation(self, session: QuizSession, selected_answer: str,
                               current_idx: int, prev_clicked: bool, next_clicked: bool,
                               finish_clicked: bool, restart_clicked: bool):
        """Handle quiz navigation logic"""
        # Save current answer
        session.user_answers[current_idx] = selected_answer
        
        if prev_clicked and current_idx > 0:
            session.current_question_idx -= 1
            st.rerun()
        
        elif next_clicked and current_idx < len(session.questions) - 1:
            session.current_question_idx += 1
            st.rerun()
        
        elif finish_clicked:
            self._complete_quiz(session)
            st.rerun()
        
        elif restart_clicked:
            self._restart_quiz()
            st.rerun()
    
    def _complete_quiz(self, session: QuizSession):
        """Complete quiz and calculate results"""
        session.end_time = datetime.now()
        
        # Calculate results
        results = self._calculate_quiz_results(session)
        
        # Save results and add to history
        st.session_state.quiz_results = results
        st.session_state.quiz_history.append({
            'timestamp': datetime.now(),
            'topic': session.topic,
            'score': results.score_percentage,
            'questions': len(session.questions)
        })
        
        # Clear active session
        st.session_state.quiz_session = None
    
    def _calculate_quiz_results(self, session: QuizSession) -> QuizResults:
        """Calculate comprehensive quiz results"""
        total_questions = len(session.questions)
        correct_count = 0
        detailed_results = []
        
        # Analyze each question
        for i, question in enumerate(session.questions):
            user_answer = session.user_answers.get(i, "")
            is_correct = user_answer == question.correct_answer
            
            if is_correct:
                correct_count += 1
            
            detailed_results.append({
                'question_num': i + 1,
                'question': question.question,
                'user_answer': user_answer,
                'correct_answer': question.correct_answer,
                'is_correct': is_correct,
                'explanation': question.explanation,
                'options': question.options
            })
        
        # Calculate metrics
        score_percentage = (correct_count / total_questions) * 100
        time_taken = session.end_time - session.start_time
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            score_percentage, session.topic, session.difficulty
        )
        
        return QuizResults(
            total_questions=total_questions,
            correct_answers=correct_count,
            score_percentage=score_percentage,
            time_taken=time_taken,
            topic=session.topic,
            difficulty=session.difficulty,
            certificate_level=session.certificate_level,
            detailed_results=detailed_results,
            recommendations=recommendations
        )
    
    def _generate_recommendations(self, score: float, topic: str, difficulty: str) -> List[str]:
        """Generate personalized study recommendations"""
        recommendations = []
        
        if score >= 90:
            recommendations.extend([
                f"🏆 Excellent mastery of {topic}! Consider moving to advanced topics.",
                "🎯 You're ready for higher difficulty challenges.",
                "📚 Help others by sharing your knowledge."
            ])
        elif score >= 75:
            recommendations.extend([
                f"👍 Good understanding of {topic}. Focus on weak areas for improvement.",
                "📖 Review explanations for incorrect answers.",
                "🔄 Practice similar topics to reinforce learning."
            ])
        elif score >= 60:
            recommendations.extend([
                f"📚 You have basic knowledge of {topic}. More study needed.",
                "🎯 Focus on fundamentals before moving to advanced concepts.",
                "📝 Create study notes for difficult topics."
            ])
        else:
            recommendations.extend([
                f"⚠️ {topic} needs significant attention. Start with basics.",
                "📖 Review NCC syllabus materials thoroughly.",
                "👥 Consider getting help from instructors or peers.",
                "🔄 Take practice quizzes regularly."
            ])
        
        return recommendations
    
    def _render_quiz_results(self):
        """Render comprehensive quiz results"""
        results = st.session_state.quiz_results
        
        # Results header with score
        self._render_results_header(results)
        
        # Detailed results section
        with st.expander("📊 View Detailed Results", expanded=True):
            self._render_detailed_results(results)
        
        # Recommendations section
        with st.expander("💡 Study Recommendations", expanded=True):
            self._render_recommendations(results)
        
        # Action buttons
        self._render_results_actions()
    
    def _render_results_header(self, results: QuizResults):
        """Render results header with score visualization"""
        # Determine performance level and color
        if results.score_percentage >= 80:
            performance = "Excellent"
            color = "#28a745"
            emoji = "🏆"
        elif results.score_percentage >= 60:
            performance = "Good"
            color = "#ffc107"
            emoji = "👍"
        else:
            performance = "Needs Improvement"
            color = "#dc3545"
            emoji = "📚"
        
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, {color}20, {color}10); 
                    padding: 2rem; border-radius: 15px; text-align: center; margin: 2rem 0;
                    border: 2px solid {color}40;'>
            <h1 style='color: {color}; margin: 0; font-size: 3rem;'>{emoji}</h1>
            <h2 style='color: #333; margin: 0.5rem 0;'>{performance}!</h2>
            <h3 style='color: {color}; margin: 0.5rem 0;'>
                {results.correct_answers}/{results.total_questions} 
                ({results.score_percentage:.1f}%)
            </h3>
            <p style='color: #666; margin: 0;'>
                Topic: {results.topic} | Difficulty: {results.difficulty} | 
                Time: {self._format_time_delta(results.time_taken)}
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    def _render_detailed_results(self, results: QuizResults):
        """Render detailed question-by-question results"""
        for result in results.detailed_results:
            # Question container
            with st.container():
                # Question header
                if result['is_correct']:
                    st.success(f"✅ Question {result['question_num']}: Correct")
                else:
                st.error(f"❌ Question {result['question_num']}: Incorrect")
                
                # Question text
                st.markdown(f"**Q{result['question_num']}:** {result['question']}")
                
                # Show options with highlighting
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**Your Answer:**")
                    if result['user_answer']:
                        user_option = result['options'].get(result['user_answer'], 'Not answered')
                        if result['is_correct']:
                            st.success(f"{result['user_answer']}) {user_option}")
                        else:
                            st.error(f"{result['user_answer']}) {user_option}")
                    else:
                        st.warning("Not answered")
                
                with col2:
                    st.markdown("**Correct Answer:**")
                    correct_option = result['options'].get(result['correct_answer'], 'Unknown')
                    st.success(f"{result['correct_answer']}) {correct_option}")
                
                # Show explanation
                if result['explanation']:
                    with st.expander("💡 Explanation"):
                        st.info(result['explanation'])
                
                st.markdown("---")
    
    def _render_recommendations(self, results: QuizResults):
        """Render personalized study recommendations"""
        st.markdown("### 🎯 Personalized Recommendations")
        
        for i, recommendation in enumerate(results.recommendations, 1):
            st.markdown(f"{i}. {recommendation}")
        
        # Additional study resources based on performance
        if results.score_percentage < 60:
            st.markdown("### 📚 Suggested Study Materials")
            st.markdown(f"""
            - **Focus Area**: {results.topic}
            - **Certificate Level**: {results.certificate_level}
            - **Recommended Study Time**: 2-3 hours daily
            - **Practice Frequency**: Take quizzes every 2-3 days
            """)
        
        # Performance trend (if quiz history available)
        if len(st.session_state.quiz_history) > 1:
            self._render_performance_trend()
    
    def _render_performance_trend(self):
        """Render performance trend chart"""
        try:
            import matplotlib.pyplot as plt
            import numpy as np
            
            history = st.session_state.quiz_history[-10:]  # Last 10 quizzes
            scores = [quiz['score'] for quiz in history]
            dates = [quiz['timestamp'].strftime('%m/%d') for quiz in history]
            
            fig, ax = plt.subplots(figsize=(10, 4))
            ax.plot(dates, scores, marker='o', linewidth=2, markersize=6)
            ax.set_title('Performance Trend (Last 10 Quizzes)')
            ax.set_ylabel('Score (%)')
            ax.set_xlabel('Date')
            ax.grid(True, alpha=0.3)
            ax.set_ylim(0, 100)
            
            # Add trend line
            if len(scores) > 2:
                z = np.polyfit(range(len(scores)), scores, 1)
                p = np.poly1d(z)
                ax.plot(dates, p(range(len(scores))), "--", alpha=0.7, color='red')
            
            st.pyplot(fig)
            plt.close()
            
        except ImportError:
            # Fallback without matplotlib
            st.markdown("### 📈 Performance Summary")
            if len(st.session_state.quiz_history) >= 2:
                recent_scores = [q['score'] for q in st.session_state.quiz_history[-5:]]
                avg_score = sum(recent_scores) / len(recent_scores)
                st.metric("Recent Average", f"{avg_score:.1f}%")
    
    def _render_results_actions(self):
        """Render action buttons after quiz completion"""
        st.markdown("### 🎮 What's Next?")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("🔄 Take Another Quiz", type="primary", use_container_width=True):
                self._restart_quiz()
                st.rerun()
        
        with col2:
            if st.button("📚 Study This Topic", use_container_width=True):
                # Store topic for study planner
                st.session_state.study_focus_topic = st.session_state.quiz_results.topic
                st.session_state.current_page = "📚 Study Planner"  # Navigate to study planner
                st.rerun()
        
        with col3:
            if st.button("📊 View All Results", use_container_width=True):
                self._show_detailed_history()
        
        with col4:
            if st.button("💬 Ask AI About Topic", use_container_width=True):
                # Navigate to chat with topic context
                st.session_state.chat_context = f"I just completed a quiz on {st.session_state.quiz_results.topic} and scored {st.session_state.quiz_results.score_percentage:.1f}%. Can you help me understand this topic better?"
                st.session_state.current_page = "💬 AI Chat"
                st.rerun()
    
    def _show_detailed_history(self):
        """Show detailed quiz history"""
        if not st.session_state.quiz_history:
            st.info("No quiz history available yet.")
            return
        
        st.subheader("📊 Quiz History")
        
        # Create history table
        history_data = []
        for i, quiz in enumerate(reversed(st.session_state.quiz_history[-20:]), 1):  # Last 20 quizzes
            history_data.append({
                "#": i,
                "Date": quiz['timestamp'].strftime('%Y-%m-%d %H:%M'),
                "Topic": quiz['topic'],
                "Questions": quiz['questions'],
                "Score": f"{quiz['score']:.1f}%",
                "Grade": self._get_grade(quiz['score'])
            })
        
        # Display as dataframe
        import pandas as pd
        df = pd.DataFrame(history_data)
        st.dataframe(df, use_container_width=True)
        
        # Summary statistics
        if len(st.session_state.quiz_history) > 0:
            scores = [q['score'] for q in st.session_state.quiz_history]
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Quizzes", len(st.session_state.quiz_history))
            with col2:
                st.metric("Average Score", f"{sum(scores)/len(scores):.1f}%")
            with col3:
                st.metric("Best Score", f"{max(scores):.1f}%")
            with col4:
                improvement = scores[-1] - scores[0] if len(scores) > 1 else 0
                st.metric("Improvement", f"{improvement:+.1f}%")
    
    def _get_grade(self, score: float) -> str:
        """Convert score to letter grade"""
        if score >= 90:
            return "A+"
        elif score >= 80:
            return "A"
        elif score >= 70:
            return "B"
        elif score >= 60:
            return "C"
        else:
            return "D"
    
    def _restart_quiz(self):
        """Reset quiz state to start fresh"""
        st.session_state.quiz_session = None
        st.session_state.quiz_results = None
    
    def _format_time_delta(self, time_delta) -> str:
        """Format time delta as human-readable string"""
        total_seconds = int(time_delta.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"
    
    def _render_quiz_history_preview(self):
        """Show a preview of recent quiz history"""
        if not st.session_state.quiz_history:
            return
        
        st.markdown("---")
        st.subheader("📈 Recent Performance")
        
        # Show last 3 quizzes
        recent_quizzes = st.session_state.quiz_history[-3:]
        
        cols = st.columns(len(recent_quizzes))
        for i, quiz in enumerate(recent_quizzes):
            with cols[i]:
                score_color = "#28a745" if quiz['score'] >= 70 else "#ffc107" if quiz['score'] >= 50 else "#dc3545"
                st.markdown(f"""
                <div style='padding: 1rem; border-radius: 8px; border-left: 4px solid {score_color}; background: #f8f9fa;'>
                    <strong>{quiz['topic'][:20]}{'...' if len(quiz['topic']) > 20 else ''}</strong><br>
                    <span style='color: {score_color}; font-size: 1.2em;'>{quiz['score']:.1f}%</span><br>
                    <small>{quiz['timestamp'].strftime('%m/%d %H:%M')}</small>
                </div>
                """, unsafe_allow_html=True)
    
    def _load_demo_questions(self):
        """Load demo questions when AI is not available"""
        demo_questions = [
            QuizQuestion(
                question="What does NCC stand for?",
                options={
                    'A': "National Cadet Corps",
                    'B': "National Civil Corps", 
                    'C': "National Combat Corps",
                    'D': "National Citizen Corps"
                },
                correct_answer='A',
                explanation="NCC stands for National Cadet Corps, which is a youth development movement in India.",
                topic="NCC Basics"
            ),
            QuizQuestion(
                question="What is the NCC motto?",
                options={
                    'A': "Service Before Self",
                    'B': "Unity and Discipline",
                    'C': "Duty, Honor, Country",
                    'D': "Strength Through Unity"
                },
                correct_answer='B',
                explanation="The NCC motto is 'Unity and Discipline' which emphasizes the core values of the organization.",
                topic="NCC Basics"
            ),
            QuizQuestion(
                question="When was NCC established?",
                options={
                    'A': "1947",
                    'B': "1948", 
                    'C': "1950",
                    'D': "1952"
                },
                correct_answer='B',
                explanation="NCC was established on 15 July 1948 under the NCC Act.",
                topic="NCC History"
            ),
            QuizQuestion(
                question="Which of the following is NOT an NCC wing?",
                options={
                    'A': "Army Wing",
                    'B': "Navy Wing",
                    'C': "Air Wing", 
                    'D': "Coast Guard Wing"
                },
                correct_answer='D',
                explanation="NCC has three wings: Army, Navy, and Air Wing. Coast Guard Wing is not part of NCC structure.",
                topic="NCC Organization"
            ),
            QuizQuestion(
                question="What is the duration of NCC 'B' Certificate camp?",
                options={
                    'A': "7 days",
                    'B': "10 days",
                    'C': "14 days",
                    'D': "21 days"
                },
                correct_answer='B',
                explanation="NCC 'B' Certificate camp is conducted for 10 days, which includes various training activities.",
                topic="NCC Training"
            )
        ]
        
        # Create demo quiz session
        quiz_session = QuizSession(
            questions=demo_questions,
            topic="NCC Demo Quiz",
            difficulty="Intermediate",
            certificate_level="B Certificate"
        )
        
        st.session_state.quiz_session = quiz_session
        st.session_state.last_quiz_generation = datetime.now()
        st.success("✅ Demo quiz loaded! Try out the quiz system.")
        st.rerun()

# Additional utility functions that might be needed

def export_quiz_results(results: QuizResults) -> str:
    """Export quiz results as JSON string for external use"""
    try:
        import json
        export_data = {
            'timestamp': datetime.now().isoformat(),
            'topic': results.topic,
            'certificate_level': results.certificate_level,
            'difficulty': results.difficulty,
            'score': results.score_percentage,
            'correct_answers': results.correct_answers,
            'total_questions': results.total_questions,
            'time_taken_seconds': results.time_taken.total_seconds(),
            'recommendations': results.recommendations
        }
        return json.dumps(export_data, indent=2)
    except Exception as e:
        return f"Export failed: {str(e)}"

def import_custom_questions(file_content: str) -> List[QuizQuestion]:
    """Import questions from JSON file content"""
    try:
        import json
        data = json.loads(file_content)
        questions = []
        
        for q_data in data.get('questions', []):
            question = QuizQuestion(
                question=q_data['question'],
                options=q_data['options'],
                correct_answer=q_data['correct_answer'],
                explanation=q_data.get('explanation', ''),
                difficulty=q_data.get('difficulty', 'Intermediate'),
                topic=q_data.get('topic', 'Custom'),
                certificate_level=q_data.get('certificate_level', 'B Certificate')
            )
            questions.append(question)
        
        return questions
    except Exception as e:
        st.error(f"Failed to import questions: {str(e)}")
        return []

# End of QuizInterface class and supporting functions
