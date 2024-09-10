import streamlit as st
import os
import sys
import json
import time
import re
        
sys.path.append(os.path.abspath('../../'))

from tasks.Document_Ingestion.document_ingestion import DocumentProcessor
from tasks.Embedding_Client_Creator.embedding_client_creator import EmbeddingClient
from tasks.Chroma_Collection_Creator.chroma_collection_creator import ChromaCollectionCreator

from langchain_core.prompts import PromptTemplate
from langchain_google_vertexai import VertexAI

# Run this file to check wheather the Google's api key is being authenticated as expected 
key_path = "/Users/suryaae/Radical AI/GeminiQuizzify/auth_key.json"

if os.path.exists(key_path):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = key_path
else:
    raise FileNotFoundError(f"The file {key_path} does not exist.")

from google.auth import credentials
from google.auth.exceptions import DefaultCredentialsError
import google.auth

try:
    credentials, project = google.auth.default()
    print(f"Authenticated with project: {project}")
except DefaultCredentialsError as e:
    print(f"Failed to authenticate: {e}")


# This file generates generates multiple-choice quiz questions with explanations.  


class QuizGenerator:
    def __init__(self, topic=None, num_questions=1, vectorstore=None):
        """
        # Initializes the QuizGenerator with a required topic, the number of questions for the quiz,
        # and an optional vectorstore for querying related information.

        # :param topic: A string representing the required topic of the quiz.
        # :param num_questions: An integer representing the number of questions to generate for the quiz, up to a maximum of 10.
        # :param vectorstore: An optional vectorstore instance (e.g., ChromaDB) to be used for querying information related to the quiz topic.
        """
        if not topic:
            self.topic = "General Knowledge"
        else:
            self.topic = topic

        if num_questions > 10:
            raise ValueError("Number of questions cannot exceed 10.")
        self.num_questions = num_questions

        self.vectorstore = vectorstore
        self.llm = None
        self.question_bank = [] # Initialize the question bank to store questions
        self.system_template = """
            You are a subject matter expert on the topic: {topic}
            
            Follow the instructions to create a quiz question:
            1. Generate a question based on the topic provided and context as key "question"
            2. Provide 4 multiple choice answers to the question as a list of key-value pairs "choices"
            3. Provide the correct answer for the question from the list of answers as key "answer"
            4. Provide an explanation as to why the answer is correct as key "explanation"
            
            You must respond as a JSON object with the following structure:
            {{
                "question": "<question>",
                "choices": [
                    {{"key": "A", "value": "<choice>"}},
                    {{"key": "B", "value": "<choice>"}},
                    {{"key": "C", "value": "<choice>"}},
                    {{"key": "D", "value": "<choice>"}}
                ],
                "answer": "<answer key from choices list>",
                "explanation": "<explanation as to why the answer is correct>"
            }}
            
            Context: {context}
            """
    
    def init_llm(self):
        """
        Initializes and configures the Large Language Model (LLM) for generating quiz questions.

        This method should handle any setup required to interact with the LLM, including authentication,
        setting up any necessary parameters, or selecting a specific model.
        
        :return: An instance or configuration for the LLM.
        """
        self.llm = VertexAI(
            model_name = "gemini-pro",
            temperature = 0.5, 
            max_output_tokens = 1000
        )

    def generate_question_with_vectorstore(self):
        """
        Generates a quiz question based on the topic provided using a vectorstore
        :return: A JSON object representing the generated quiz question.
        """
        if not self.llm:
            self.init_llm()
        if not self.vectorstore:
            raise ValueError("Vectorstore not provided.")
        
        from langchain_core.runnables import RunnablePassthrough, RunnableParallel

        retriever = self.vectorstore.as_retriever()
        
        # Use the system template to create a PromptTemplate
        prompt = PromptTemplate.from_template(self.system_template)
        
        setup_and_retrieval = RunnableParallel(
            {"context": retriever, "topic": RunnablePassthrough()}
        )
        # Create a chain with the Retriever, PromptTemplate, and LLM
        chain = setup_and_retrieval | prompt | self.llm 

        # Invoke the chain with the topic as input
        response = chain.invoke(self.topic)
        
        return response
    
    def generate_quiz(self) -> list:
        """
        This method generates the questions for the quiz
        :return: a list of JSON object
        """
        
        self.question_bank = []
        for _ in range(self.num_questions): 
                           
            question_str= self.generate_question_with_vectorstore()

            # sometimes the json output generates " ```json|```" so this needs to be removed
            cleaned_question_str = re.sub(r"```json|```", "", question_str).strip()
            
            try: 
               question= json.loads(cleaned_question_str)
            
            except json.JSONDecodeError:
                print("Failed to decode question JSON")
                continue 
            
            # Each generated question is validated in the question bank to check for duplicates
            if self.validate_question(question):
                print("Successfully generated unique question")
                
                self.question_bank.append(question)
            
            # if the dupilicate is deducted then model is made to regenerate questions for next 3 tries
            else:
                print("Duplicate or invalid question detected")
                
                for i in range(3): #Retry limit of 3 attempts
                    question_str = self.generate_question_with_vectorstore()
                    cleaned_question_str = re.sub(r"```json|```", "", question_str).strip()
                    
                    try:
                        question = json.loads(cleaned_question_str)
                    
                    except json.JSONDecodeError:
                        print("Failed to decode question JSON.")
                        continue 
                    
                    if self.validate_question(question):
                        print("Successfully generated unique question")
                        self.question_bank.append(question)
                        break
                    
                    else:
                        print("Duplicate or invalid question detected")
                        continue
            
            # Time delay introduced to reduce request rate, preventing 429 ResourceExhausted error
            time.sleep(8)
                             
        return self.question_bank  
    
    def validate_question(self, question: dict) -> bool:
        """
        This method checks for any duplicate questions from generated question bank
        :return: Bool value
        """
        if 'question' not in question:
            raise ValueError("The provided dictionary must contain a 'question' key.")

        question_text = question['question']
        is_unique = True

        for existing_question in self.question_bank:
            if existing_question['question'] == question_text:
                is_unique = False  
                break
            
        return is_unique      
    

if __name__ == "__main__":
    
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
                
                st.write(f"generating {questions} question/s on {topic_input}")
                
                # Test the Quiz Generator
                generator = QuizGenerator(topic_input, questions, chroma_creator)
                question_bank = generator.generate_quiz()
                question = question_bank[0]

    if question_bank:
        screen.empty()
        with st.container():
            st.header("Generated Quiz Question: ")
            for question in question_bank:
                st.write(question)
    
     
                 
            