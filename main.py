import streamlit as st
import os
import sys
import json


# Import the necessary modules for document processing, embedding, quiz generation, and quiz management

from tasks.Document_Ingestion.document_ingestion import DocumentProcessor
from tasks.Embedding_Client_Creator.embedding_client_creator import EmbeddingClient
from tasks.Chroma_Collection_Creator.chroma_collection_creator import ChromaCollectionCreator
from tasks.Quiz_Algo.quiz_algo import QuizGenerator
from tasks.Quiz_Manager.quiz_manager import QuizManager

if __name__ == "__main__":
    
    # Embedding model configuration for Vertex AI
    embed_config= {
        "model_name": "textembedding-gecko@003",
        "project": "gemini-quizzify-21082024",
        "location": "us-central1"
    }
    
    # Check if the question bank exists in session state or if it's empty
    if 'question_bank' not in st.session_state or len(st.session_state['question_bank']) == 0:
        st.session_state['question_bank'] = []
        
        screen = st.empty()
        with screen.container():
            st.header("Quiz Builder")
            
            # Form to handle data ingestion and topic input for quiz generation
            with st.form("Load Data to Chroma"):
                st.write("Select PDFs for Ingestions, the topic for the quiz, and click Generate!")
                
                # Initialize the document processor to ingest PDFs
                processor= DocumentProcessor()
                processor.ingest_documents()
                
                # Initialize embedding client and Chroma collection creator
                embed_client= EmbeddingClient(**embed_config)
                chroma_creator= ChromaCollectionCreator(processor, embed_client)
                
                # Inputs for quiz topic and number of questions
                quiz_topic= st.text_input("Pls give the topic for the Quiz")
                questions= st.slider("Number of questions", min_value=1, max_value=10, value=1)
                
                submitted= st.form_submit_button("Submit")
                
                # Upon submission, generate the quiz questions
                if submitted:
                    chroma_creator.create_chroma_collection()
                    
                    if len(processor.pages) > 0:
                        st.write(f"Generating {questions} questions for topic {quiz_topic}")
                        
                    # Create a quiz generator to generate the quiz questions based on topic and Chroma collection
                    generator = QuizGenerator(quiz_topic, questions, chroma_creator)
                    question_bank = generator.generate_quiz()
                    
                    # Store the generated quiz questions and set display flags in session state
                    st.session_state["question_bank"]= question_bank
                    st.session_state["display_quiz"]= True                    
                    st.session_state["question_index"] = 0
    
                    st.rerun()
                    
                        
    # Display the quiz if the quiz has been generated and the display flag is set
    elif st.session_state["display_quiz"]:
        st.empty()
        with st.container():
            st.header("Generated Quiz Questions: ")
            
            # Initialize QuizManager with the stored question bank
            quiz_manager= QuizManager(st.session_state["question_bank"])
            
            # Form to display multiple-choice questions
            with st.form("MCQ"):
                index_question= quiz_manager.get_question_at_index(st.session_state['question_index'])
                
                # Prepare the choices for the current question
                choices= []
                for choice in index_question["choices"]:
                    key= choice['key']
                    value= choice['value']
                    choices.append(f"{key}) {value}")

                # Display the current question and its answer choices
                st.write(f"{st.session_state['question_index'] + 1}. {index_question['question']}")
                answer= st.radio(
                    "choose an answer",
                    choices,
                    index= None
                )                    
                
                # Create three columns for Previous, Submit, and Next buttons
                left, mid, right = st.columns([2,2,1], gap= "large", vertical_alignment= "bottom")
                
                with left:
                    st.form_submit_button(" ◀ ", on_click=lambda: quiz_manager.next_question_index(direction=-1))
                
                with right:
                    st.form_submit_button(" ▶ ", on_click=lambda: quiz_manager.next_question_index(direction=1))
                    
                with mid:
                    answer_choice= st.form_submit_button(" Submit ") 
                    
                
                # Process the answer choice
                if answer_choice and answer is not None:
                    # Retrieve the correct answer key and value
                    correct_answer_key= index_question['answer']
                    correct_answer_value = next((choice['value'] for choice in index_question['choices'] if choice['key'] == correct_answer_key), None)
                    
                    # Check if the submitted answer is correct
                    if answer.startswith(correct_answer_key):
                        st.success('Correct!')
                    else:
                        st.error("Incorrect!")
                    
                    # Display the correct answer and its explanation
                    st.write(f"Correct Answer: {correct_answer_key}) {correct_answer_value} ")
                    st.write(f"Explanation: {index_question['explanation']}") 