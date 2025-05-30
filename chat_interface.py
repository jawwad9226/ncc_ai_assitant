import streamlit as st
from typing import List, Dict, Optional
from datetime import datetime, timedelta

def display_chat_interface(model, model_error, get_ncc_response, st_session_state):
    """Display the chat interface"""
    st.header("💬 Chat with NCC Assistant")
    st.write("Ask me anything about NCC - from drill commands to leadership principles!")
    
    # Sample questions
    with st.expander("📝 Sample Questions"):
        sample_questions = [
            "What are the basic drill commands in NCC?",
            "Explain the NCC pledge and its significance",
            "What are the different types of NCC certificates?",
            "How to read a military map?",
            "What is the importance of discipline in NCC?",
            "Explain the rank structure in NCC"
        ]
        
        for i, question in enumerate(sample_questions, 1):
            if st.button(f"{i}. {question}", key=f"sample_{i}"):
                st_session_state.messages.append({"role": "user", "content": question})
                with st.spinner("Getting response..."):
                    response = get_ncc_response(question)
                    st_session_state.messages.append({"role": "assistant", "content": response})
                st.experimental_rerun()
    
    # Display chat messages
    for message in st_session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask about NCC..."):
        # Add user message
        st_session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get and display AI response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = get_ncc_response(prompt)
                st.markdown(response)
                st_session_state.messages.append({"role": "assistant", "content": response})
                st.experimental_rerun()
