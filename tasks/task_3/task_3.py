import streamlit as st
from langchain_community.document_loaders import PyPDFLoader
import os
import tempfile
import uuid

class DocumentProcessor:
    
    def __init__(self):
        self.pages = []
        
    def ingest_documents(self):
        uploaded_files= st.file_uploader("Choose your PDF files", type= ['pdf'], 
                                        accept_multiple_files= True)
        
        if uploaded_files is not None:
            
            for uploaded_file in uploaded_files:
                unique_id = uuid.uuid4().hex
                original_name, file_extention = os.path.splitext(uploaded_file.name)
                temp_file_name= f"{original_name}_{unique_id}{file_extention}"
                temp_file_path= os.path.join(tempfile.gettempdir(), temp_file_name)    
                
                # print(temp_file_name,"/n")
                # print(temp_file_path)
                
                with open(temp_file_path, 'wb') as f:
                    f.write(uploaded_file.getvalue())
                
                loader = PyPDFLoader(temp_file_path)
                pages = loader.load_and_split() 
                
                self.pages.extend(pages) 
                
                os.unlink(temp_file_path)  
            
            st.write(f"Total pages processed: {len(self.pages)}")
            # for i, page in enumerate(self.pages):
            #     st.write(f"Page {i+1} content:")
            #     st.write(page.page_content)


if __name__ == "__main__":
    processor = DocumentProcessor()
    processor.ingest_documents()
        