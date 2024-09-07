from langchain_google_vertexai import VertexAIEmbeddings


# This file creates the vector embeddings leveraging google cloud platform's VertexAI

class EmbeddingClient:
    
    def __init__(self, model_name, project, location):
        self.client= VertexAIEmbeddings(
            model_name= model_name,
            project= project,
            location= location
        )
        
    # creates vector embedding for the user's query
    def embed_query(self, query):
        vectors= self.client.embed_query(query)
        return vectors
    
    # creates vector embedding for the processed documents
    def embed_documents(self, documents):
        try:
            self.client.embed_documents(documents)
        except AttributeError:
            print("Method embed_documents not defined for the client.")
            return None
        

if __name__ == "__main__":
    model_name= "textembedding-gecko@003"
    project= "gemini-quizzify-21082024"
    location= "us-central1"
    

    embedding_client= EmbeddingClient(model_name, project, location)
    

    vectors= embedding_client.embed_query("Hello World!")

    if vectors:
        print(vectors)
        print("Successfully used the embedding client!")