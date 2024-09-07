import sys 
import os
import streamlit as st

sys.path.append(os.path.abspath('../../'))

from tasks.Document_Ingestion.document_ingestion import DocumentProcessor
from tasks.Embedding_Client_Creator.embedding_client_creator import EmbeddingClient
from tasks.Chroma_Collection_Creator.chroma_collection_creator import ChromaCollectionCreator


# This file is the Quiz builder.
# 1 > creates a form for users to upload their files.
# 2 > User can input their topic/s for quiz generation i.e. user's query in textbox
# 3 > user can also select number of questions to generate  


if __name__ == "__main__":
    st.header("Gemini Quizzify")

    embed_config= {
        "model_name": "textembedding-gecko@003",
        "project": "gemini-quizzify-21082024",
        "location": "us-central1"
    }    
    
    screen= st.empty()
    with screen.container():
        
        processor= DocumentProcessor()
        embed_client= EmbeddingClient(**embed_config)
        chroma_creator= ChromaCollectionCreator(processor, embed_client)
        
        # Collecting user's files
        processor.ingest_documents()
        
        # creates a form to let user to input their quiz topic and number of questions
        with st.form("Load Data to Chroma"):
            st.subheader("Quiz Builder")
            st.write("Select PDFs for Ingestion, then topic for the quiz, and click Generate Quiz!")
            quiz_topic= st.text_input("Give a Topic for Quiz Generation:", label_visibility= "visible")
            num_of_questions= st.slider('Select no. of questions',
                                               value=5, 
                                               min_value= 1,
                                               max_value= 10,
                                               step= 1)        

            submitted= st.form_submit_button("Generate Quiz!")

            # the 'document' variable has the first page of the content related to the users topic generation query 
            document= None            
        
            if submitted:
                chroma_creator.create_chroma_collection()
                
                document= chroma_creator.query_chroma_collection(quiz_topic)
                
            
    if document:
        screen.empty()
        with st.container():
            st.header("Query Chroma for Topic, top Document: ")
            st.write(document)       
                
                
                
            
        
        
    
