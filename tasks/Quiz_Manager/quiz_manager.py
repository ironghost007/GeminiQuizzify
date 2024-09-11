import streamlit as st
import os 
import sys
import json
sys.path.append(os.path.abspath('../../'))
from tasks.Document_Ingestion.document_ingestion import DocumentProcessor
from tasks.Embedding_Client_Creator.embedding_client_creator import EmbeddingClient
from tasks.Chroma_Collection_Creator.chroma_collection_creator import ChromaCollectionCreator
from tasks.Quiz_Algo.quiz_algo import QuizGenerator

class QuizManager:
    """
    A class to manage quiz questions.
    
    This class is responsible for storing a list of quiz questions, navigating between them, 
    and retrieving the current quiz question based on its index.
    
    Attributes:
    - questions: A list of dictionaries where each dictionary represents a quiz question.
    - total_questions: The total number of questions in the quiz.
    """
    
    def __init__(self, questions: list):
        """
        Initializes the QuizManager with a list of questions and calculates the total number of questions.

        :param questions: List of dictionaries where each dictionary contains the details of a quiz question.
        """
        self.questions= questions
        self.total_questions= len(self.questions)
        
    def get_question_at_index(self, index: int):
        """
        Retrieves a quiz question based on the given index.

        If the index exceeds the total number of questions, it wraps around using modulo arithmetic.

        :param index: The index of the quiz question to retrieve.
        :return: A dictionary representing the quiz question at the specified index.
        """
        valid_index= index % self.total_questions
        return self.questions[valid_index]
    
    def next_question_index(self, direction=1):
        """
        Adjusts the current quiz question index based on the specified direction (next/previous).
        
        The method updates the question index stored in Streamlit's session state.

        :param direction: The direction to move in the quiz. 1 for next, -1 for previous.
        """
        current_question_index=  st.session_state["question_index"]
        new_index= (current_question_index + direction) % self.total_questions
        st.session_state["question_index"]= new_index
        
if __name__ == "__main__":
    
    """
    Main application to generate and display a quiz question on the proper web interface.
    
    This script uses Streamlit for the front-end interface. It integrates multiple components from other tasks to:
    1. Ingest PDFs and embed the content.
    2. Generate quiz questions using the Chroma collection.
    3. Allow users to answer the generated quiz questions.
    """
    
    embed_config= {
        "model_name": "textembedding-gecko@003",
        "project": "gemini-quizzify-21082024",
        "location": "us-central1"
    }
    
    screen = st.empty()
    with screen.container():
        st.header("Quiz Builder")
        processor = DocumentProcessor()
        processor.ingest_documents()
    
        embed_client = EmbeddingClient(**embed_config) 
    
        chroma_creator = ChromaCollectionCreator(processor, embed_client)

        question = None
        question_bank = None
    
        with st.form("Load Data to Chroma"):
            st.subheader("Quiz Builder")
            st.write("Select PDFs for Ingestion, the topic for the quiz, and click Generate!")
            
            topic_input = st.text_input("Topic for Generative Quiz", placeholder="Enter the topic of the document")
            questions = st.slider("Number of Questions", min_value=1, max_value=10, value=1)
            
            submitted = st.form_submit_button("Submit")
            if submitted:
                chroma_creator.create_chroma_collection()
                
                st.write(f"Generating {questions} questions for the topic {topic_input}....")
                
                # Test the Quiz Generator
                generator = QuizGenerator(topic_input, questions, chroma_creator)
                question_bank = generator.generate_quiz()

    if question_bank:
        screen.empty()
        with st.container():
            st.header("Generated Quiz Question: ")
            
            quiz_manager = QuizManager(question_bank) 
            with st.form("Multiple Choice Question"):
                index_question = quiz_manager.get_question_at_index(0)
                
                choices = []
                for choice in index_question['choices']:

                    key = choice["key"]
                    value = choice["value"]

                    choices.append(f"{key}) {value}")
                
                st.subheader(index_question['question'])
                
                answer = st.radio( 
                    'Choose the correct answer',
                    choices
                )
                
                st.form_submit_button("Submit")
                
                if submitted: 
                    correct_answer_key = index_question['answer']
                    if answer.startswith(correct_answer_key): 
                        st.success("Correct!")
                    else:
                        st.error("Incorrect!")
                