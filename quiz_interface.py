import streamlit as st
from typing import List, Dict, Optional
from datetime import datetime, timedelta

def display_quiz_interface(model, model_error, generate_quiz_questions, parse_quiz_response, st_session_state):
    """Display the quiz interface"""
    st.header("🎯 NCC Knowledge Quiz")
    st.write("Test your NCC knowledge with AI-generated questions!")
    
    # Quiz creation section
    if not st_session_state.quiz_questions or st_session_state.quiz_completed:
        display_quiz_creation(model, model_error, generate_quiz_questions, st_session_state)
    else:
        display_active_quiz(st_session_state)

def display_quiz_creation(model, model_error, generate_quiz_questions, st_session_state):
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
            questions = generate_quiz_questions(quiz_topic.strip(), num_questions)
            if questions:
                st_session_state.quiz_questions = questions
                st_session_state.quiz_topic = quiz_topic.strip()
                st_session_state.current_question = 0
                st_session_state.user_answers = {}
                st_session_state.quiz_submitted = False
                st_session_state.quiz_completed = False
                st.experimental_rerun()
        else:
            st.warning("Please enter a quiz topic.")
    
    # Show rate limiting info
    if st_session_state.last_api_call:
        time_since_last = datetime.now() - st_session_state.last_api_call
        if time_since_last < timedelta(minutes=2):
            remaining = 2 - (time_since_last.seconds // 60)
            st.info(f"ℹ️ Quiz generation available in {remaining} minute(s)")

def display_active_quiz(st_session_state):
    """Display the active quiz"""
    # Check if quiz is submitted and show results if true
    if st_session_state.get('quiz_submitted', False):
        show_current_answer_result(None, None, st_session_state)
        return
        
    if not st_session_state.quiz_questions:
        return
    
    questions = st_session_state.quiz_questions
    current_idx = st_session_state.current_question
    current_question = questions[current_idx]
    
    # Store current answer if it exists in session state
    answer_key = f"answer_{current_idx}"
    if answer_key in st_session_state:
        st_session_state.user_answers[current_idx] = st_session_state[answer_key]
    
    # Quiz header
    st.subheader(f"📚 Quiz: {st_session_state.quiz_topic}")
    
    # Progress bar
    progress = (current_idx + 1) / len(questions)
    st.progress(progress)
    st.write(f"Question {current_idx + 1} of {len(questions)}")
    
    # Question display
    st.markdown(f"### {current_question['question']}")
    
    # Get current answer if it exists
    current_answer = st_session_state.user_answers.get(current_idx)
    
    # Use a form for the current question
    with st.form(key=f'question_form_{current_idx}'):
        # Answer options
        selected_answer = st.radio(
            "Choose your answer:",
            options=['A', 'B', 'C', 'D'],
            format_func=lambda x: f"{x}) {current_question['options'][x]}",
            key=answer_key,
            index=['A', 'B', 'C', 'D'].index(current_answer) if current_answer else 0
        )
        
        # Navigation buttons
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            prev_clicked = st.form_submit_button("⬅️ Previous", 
                disabled=current_idx == 0,
                help="Go to previous question" if current_idx > 0 else "This is the first question")
        
        with col2:
            if current_idx < len(questions) - 1:
                next_clicked = st.form_submit_button("Next ➡️", help="Go to next question")
            else:
                finish_clicked = st.form_submit_button("🏁 Finish Quiz", type="primary")
        
        with col3:
            new_quiz_clicked = st.form_submit_button("🔄 New Quiz")
    
    # Handle navigation after form submission
    if 'prev_clicked' in locals() and prev_clicked and current_idx > 0:
        st_session_state.current_question -= 1
        st.experimental_rerun()
    
    if 'next_clicked' in locals() and next_clicked and current_idx < len(questions) - 1:
        st_session_state.user_answers[current_idx] = selected_answer
        st_session_state.current_question += 1
        st.experimental_rerun()
    
    if 'finish_clicked' in locals() and finish_clicked:
        st_session_state.user_answers[current_idx] = selected_answer
        st_session_state.quiz_submitted = True
        st.experimental_rerun()
    
    if 'new_quiz_clicked' in locals() and new_quiz_clicked:
        reset_quiz(st_session_state)
        st.experimental_rerun()
    
    # Show current question's answer if available
    if current_answer:
        show_current_answer_result(current_question, current_answer, st_session_state)

def calculate_and_show_results(st_session_state):
    """Calculate quiz results and display them"""
    questions = st_session_state.quiz_questions
    user_answers = st_session_state.user_answers
    
    correct_count = 0
    total_questions = len(questions)
    
    st_session_state.quiz_submitted = True
    st_session_state.quiz_completed = True
    
    # Calculate score
    for i, question in enumerate(questions):
        if user_answers.get(i) == question['answer']:
            correct_count += 1
    
    score_percentage = (correct_count / total_questions) * 100
    st_session_state.quiz_score = score_percentage
    
    # Store results in session state for display
    st_session_state.quiz_results = {
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
        is_correct = user_answer == correct_answer
        
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
                user_answer = results['user_answers'].get(i, "No answer")
                correct_answer = question['answer']
                is_correct = user_answer == correct_answer
                
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
    st_session_state.user_answers = {}
    st_session_state.quiz_submitted = False
    st_session_state.quiz_completed = False
    st_session_state.quiz_topic = ''
    st_session_state.quiz_score = 0
