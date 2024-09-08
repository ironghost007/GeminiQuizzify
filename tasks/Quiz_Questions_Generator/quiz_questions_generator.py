import streamlit as st
from langchain_google_vertexai import VertexAI
from langchain_core.prompts import PromptTemplate
import os
import sys
sys.path.append(os.path.abspath('../../'))

# This file generates generates multiple-choice quiz questions with explanations. 
# The file also handles the document ingestion and embedding process, creating a Chroma collection for storing and retrieving relevant data from the PDFs.


class QuizGenerator:
    def __init__(self, topic= None, num_questions=1, vectorstore= None):
        
    # Attributes:
    # topic (str): The topic on which to generate quiz questions.
    # num_questions (int): The number of questions to generate (maximum of 10).
    # vectorstore (object): A vectorstore instance for querying information about the quiz topic.
    # llm (VertexAI): The language model instance (VertexAI) used for generating questions.
    # system_template (str): The template used to guide question generation.
        
        if not topic:
            self.topic= "General Knowledge"
        else:
            self.topic= topic
            
        if num_questions > 10:
            raise ValueError("No. of questions cannot exceed 10!!")
        
        self.num_questions= num_questions
        
        self.vectorstore= vectorstore
        self.llm= None
        
        # Define a template for generating the quiz.
        self.system_template= """
            You are a subject matter expert on the topic: {topic}
            
            Follow the instructions to create a quiz question:
            1. Generate a question beased on the topic provided and context as key "question"
            2. Provide 4 multiple choice answers to the question as a list of key-value pairs "choice" 
            3. Provide the correct answer for the question form the list of answers as key "anwser"
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
                "answer": "<answer key from choice list>",
                "explanation": "<explanation as to why the answer is correct>"
                
            }}
            
            Context: {context}
            """
    
    def init_llm(self):
        # Initialize the VertexAI language model with specific configuration settings.
        my_config= {
            "temperature": 0.3,
            "max_output_tokens": 1000
        }
        
        self.llm= VertexAI(mode_name= 'gemini-pro', **my_config)
    
    
    
    def generate_question_with_vectorstore(self):
        
        # Generates quiz questions using a vectorstore for context retrieval and the VertexAI language model for question generation.
        # Returns:
        # dict: The generated quiz question in JSON format.
        
        self.init_llm()
        
        if not self.vectorstore:
            raise ValueError("Vectorstore not provided")

        from langchain_core.runnables import RunnablePassthrough, RunnableParallel
        
        # Use the vectorstore as a retriever to query relevant information.
        retriever= self.vectorstore.as_retriever()
        
        # Create a prompt template for generating the quiz.
        promt= PromptTemplate.from_template(self.system_template)
        
        # Set up parallel execution to retrieve context and topic information.
        setup_and_retrieval = RunnableParallel(
            {"context": retriever, "topic": RunnablePassthrough()}
        )
        
        # Generate the question by invoking the chain with the topic using Langchain Expression Language.
        chain= setup_and_retrieval | promt | self.llm
        
        response= chain.invoke(self.topic)
        return response
    

if __name__ == "__main__":
    from tasks.Document_Ingestion.document_ingestion import DocumentProcessor
    from tasks.Embedding_Client_Creator.embedding_client_creator import EmbeddingClient
    from tasks.Chroma_Collection_Creator.chroma_collection_creator import ChromaCollectionCreator

    
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
    
        with st.form("Load Data to Chroma"):
            st.subheader("Quiz Builder")
            st.write("Select PDFs for Ingestion, the topic for the quiz, and click Generate!")
            
            topic_input = st.text_input("Topic for Generative Quiz", placeholder="Enter the topic of the document")
            questions = st.slider("Number of Questions", min_value=1, max_value=10, value=1)
            
            submitted = st.form_submit_button("Submit")
            if submitted:
                chroma_creator.create_chroma_collection()
                
                st.write(topic_input)
                
                # Test the Quiz Generator
                generator = QuizGenerator(topic_input, questions, chroma_creator)
                question = generator.generate_question_with_vectorstore()

    if question:
        screen.empty()
        with st.container():
            st.header("Generated Quiz Question: ")
            st.write(question)