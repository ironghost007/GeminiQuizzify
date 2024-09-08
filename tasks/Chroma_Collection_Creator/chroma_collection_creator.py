import os

# Creates a Chroma database collection for the vector enbeddings
# 1 > separate the documents into chunks
# 2 > create a chromaDB collection for the chunks

import sys
import streamlit as st
sys.path.append(os.path.abspath('../../'))
from tasks.Document_Ingestion.document_ingestion import DocumentProcessor
from tasks.Embedding_Client_Creator.embedding_client_creator import EmbeddingClient

from langchain_core.documents import Document
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.vectorstores import Chroma


class ChromaCollectionCreator:
    
    def __init__(self, processor, embed_model):
        
        self.processor= processor
        self.embed_model= embed_model
        self.db= None
        
    def create_chroma_collection(self):
        
        if len(self.processor.pages) == 0:
            st.error("No documents found!", icon= "🚨")
            return
        
        
        text_splitter = CharacterTextSplitter(
            separator="\n\n",
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            is_separator_regex=False
        )
        
        # Creating text chunks
        text_chunks = [page.page_content for page in self.processor.pages]
        texts = text_splitter.create_documents(text_chunks)
        
        if texts is not None:
            st.success(f"Successfully split pages to {len(texts)} documents!!", icon= "✅")
            
        self.db= Chroma.from_documents(documents= texts, embedding= self.embed_model.client)
        
        if self.db:
            st.success("Successfully created Chroma Collection!", icon="✅")
        
        else:
            st.error("Failed to create a Chroma Collection!!", icon= "🚨") 
        
    # to create a chroma collection for the user's query
    def query_chroma_collection(self, query)-> Document :
        
        if self.db:
            docs= self.db.similarity_search_with_relevance_scores(query)
            if docs:
                return docs[0]
            else:
                st.error("No matching documents found!", icon="🚨")
                
        else:
            st.error("Chroma Collection has not been created!", icon="🚨")
            
    def as_retriever(self):
        return self.db.as_retriever()   

if __name__ == "__main__":
    processor= DocumentProcessor()
    processor.ingest_documents()
    
    embed_config = {
        "model_name": "textembedding-gecko@003",
        "project": "gemini-quizzify-21082024",
        "location": "us-central1"  
    }
    
    embed_client= EmbeddingClient(**embed_config)
    
    chroma_creator = ChromaCollectionCreator(processor, embed_client)
    
    with st.form("Load Data to Chroma"):
        st.write("Select PDFs for ingestion, then click Submit")
        
        submitted= st.form_submit_button("Submit")
        
        if submitted:
            chroma_creator.create_chroma_collection()
    