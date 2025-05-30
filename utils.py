import os
import google.generativeai as genai
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import re
import streamlit as st

def setup_gemini():
    """Initialize Gemini API with API key from environment variables"""
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key or api_key == "your_api_key_here":
            return None, "Please set up your GEMINI_API_KEY in the .env file"
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        return model, None
    except Exception as e:
        return None, f"Error initializing Gemini: {str(e)}"

def get_ncc_response(model, model_error, question: str) -> str:
    """Get AI-powered response about NCC topics"""
    if not model:
        return f"Error: {model_error}"
    
    try:
        prompt = f"""You are an expert NCC (National Cadet Corps) assistant with in-depth knowledge of:
- NCC syllabus for A, B, and C certificates
- Drill commands and procedures
- Map reading and field craft
- Weapon training and safety
- First aid and field engineering
- Military history and current affairs
- Leadership and discipline
- Adventure activities and camps

Provide accurate, helpful, and detailed responses to all NCC-related queries. 
Keep responses informative but concise, and include practical examples where relevant.

Question: {question}

Provide a comprehensive answer"""
        
        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.3,
                "max_output_tokens": 1000,
            }
        )
        return response.text
    except Exception as e:
        error_msg = str(e)
        if "quota" in error_msg.lower() or "429" in error_msg:
            return (
                "⚠️ **API Rate Limit Reached**\n\n"
                "You've exceeded the free tier quota for the Gemini API. Please:\n"
                "1. Wait a few minutes and try again\n"
                "2. Check your API usage at: https://ai.google.dev/\n"
                "3. Consider upgrading your plan if needed\n\n"
                "Try asking simpler questions or wait before making more requests."
            )
        return f"Error generating response: {error_msg}"

def can_make_api_call(st_session_state) -> tuple[bool, str]:
    """Check if we can make an API call based on rate limiting"""
    if not st_session_state.last_api_call:
        return True, ""
    
    time_since_last = datetime.now() - st_session_state.last_api_call
    cooldown_minutes = 2  # Reduced cooldown for better UX
    
    if time_since_last < timedelta(minutes=cooldown_minutes):
        remaining = cooldown_minutes - (time_since_last.seconds // 60)
        return False, f"Please wait {remaining} more minute(s) before generating another quiz."
    
    return True, ""

def generate_quiz_questions(model, model_error, st_session_state, topic: str, num_questions: int = 5) -> List[Dict]:
    """Generate quiz questions with error handling and validation"""
    if not model:
        st.error(f"Model initialization error: {model_error}")
        return []
    
    # Check rate limiting
    can_call, message = can_make_api_call(st_session_state)
    if not can_call:
        st.warning(message)
        return []
    
    try:
        prompt = f"""Create exactly {num_questions} multiple choice questions about "{topic}" in NCC context.

Format each question EXACTLY like this:
Q: [Question text here]
A) [First option]
B) [Second option] 
C) [Third option]
D) [Fourth option]
ANSWER: [A/B/C/D]
EXPLANATION: [Brief explanation of why this answer is correct]

---

Make sure questions cover different aspects of {topic} and are appropriate for NCC cadets.
Each question should be clear and unambiguous."""

        with st.spinner(f"Generating {num_questions} questions about {topic}..."):
            response = model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.4,
                    "max_output_tokens": 2000,
                }
            )
            
            st_session_state.last_api_call = datetime.now()
            
            # Parse the response
            questions = parse_quiz_response(response.text)
            
            if len(questions) == 0:
                st.error("Failed to generate valid questions. Please try a different topic.")
                return []
            
            st.success(f"Generated {len(questions)} questions successfully!")
            return questions
            
    except Exception as e:
        error_msg = str(e)
        if "quota" in error_msg.lower() or "429" in error_msg:
            st.error("⚠️ API quota exceeded. Please wait before generating more quizzes.")
        else:
            st.error(f"Error generating quiz: {error_msg}")
        return []

def parse_quiz_response(response_text: str) -> List[Dict]:
    """Parse the AI response into structured quiz questions"""
    questions = []
    
    # First, try to split by question markers
    question_blocks = []
    
    # Try different patterns to split questions
    patterns = [
        r'Q\d*:',  # Q: or Q1:, Q2:, etc.
        r'Question \d+:',  # Question 1:, Question 2:, etc.
        '---',  # Separator
        '\n\n'  # Double newline
    ]
    
    # Try each pattern until we find one that works
    for pattern in patterns:
        blocks = [b.strip() for b in re.split(pattern, response_text) if b.strip()]
        if len(blocks) > 1:
            question_blocks = blocks
            break
    else:
        # If no pattern worked, treat the whole text as one question
        question_blocks = [response_text]
    
    # Parse each block
    for block in question_blocks:
        # Clean up the block
        block = block.strip()
        if not block:
            continue
            
        # Try to parse as a question
        question_data = parse_single_question(block)
        if question_data:
            questions.append(question_data)
    
    return questions

def parse_single_question(question_text: str) -> Optional[Dict]:
    """Parse a single question block into structured data"""
    lines = [line.strip() for line in question_text.split('\n') if line.strip()]
    
    question_data = {
        'question': '',
        'options': {},
        'answer': '',
        'explanation': ''
    }
    
    current_option = None
    
    try:
        for line in lines:
            line_upper = line.upper()
            
            # Check for question (Q:, Question, etc.)
            if line_upper.startswith(('Q:', 'QUESTION')):
                # Extract the question text after the first colon
                question_text = line[line.find(':') + 1:].strip()
                question_data['question'] = question_text
            
            # Check for options (A), B), etc.)
            elif re.match(r'^[A-D][\)\.]', line_upper):
                option = line_upper[0]  # Get A, B, C, or D
                option_text = line[2:].strip()
                question_data['options'][option] = option_text
                current_option = option
            
            # Check for answer (ANSWER: A, Correct Answer: A, etc.)
            elif any(x in line_upper for x in ['ANSWER:', 'CORRECT ANSWER:']):
                # Extract the answer letter (A, B, C, or D)
                answer = re.search(r'[A-D]', line_upper)
                if answer:
                    question_data['answer'] = answer.group()
            
            # Check for explanation
            elif line_upper.startswith(('EXPLANATION:', 'EXPLANATION', 'NOTE:')):
                explanation = line[line.find(':') + 1:].strip()
                question_data['explanation'] = explanation
            
            # If line doesn't match any pattern but we're in an option, append to current option
            elif current_option and current_option in question_data['options']:
                question_data['options'][current_option] += ' ' + line.strip()
        
        # Validate that we have all required components
        if (question_data['question'] and 
            len(question_data['options']) >= 2 and  # At least 2 options
            question_data['answer'] in question_data['options']):
            return question_data
        
        # If we couldn't find a valid question, try to extract from the first line
        if not question_data['question'] and lines:
            question_data['question'] = lines[0]
            if question_data['question'] and len(question_data['options']) >= 2:
                return question_data
        
    except Exception as e:
        try:
            st.warning(f"Error parsing question: {e}")
        except (NameError, RuntimeError):
            # Handle case when Streamlit is not available
            print(f"Error parsing question: {e}")
    
    return None
