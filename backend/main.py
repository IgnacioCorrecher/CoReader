from fastapi import FastAPI, HTTPException, status, WebSocket, File, UploadFile
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from RAGChain import vector_store, text_splitter, rag_chain
import logging
import asyncio
from DocProcessing import DocProcessing

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Init App
app = FastAPI()

# CORS Configuration
origins = [
    "http://localhost:5173",  # Frontend origin
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=[
        "GET",
        "POST",
        "PUT",
        "DELETE",
        "OPTIONS",
    ],
    allow_headers=["*"],
)


@app.get("/", tags=["General"])
def root():
    return RedirectResponse("/docs")


@app.post("/upload_file", tags=["VectorDB"])
async def upload_file(file: UploadFile = File(...)):
    """
    Upload a single file and save it to the 'uploads' directory.
    """
    # Read file bytes
    content_bytes = await file.read()

    # Process file
    doc_processor = DocProcessing(file.filename, content_bytes)
    file_str = doc_processor.process_doc()

    # Split text into chunks/documents
    texts = text_splitter.create_documents([file_str])

    # Add to vector store and get generated IDs
    ids = vector_store.add_documents(texts)

    return {"status": status.HTTP_201_CREATED, "uploaded_ids": ids}


class SearchRequest(BaseModel):
    search_str: str  # String to search
    n: int = 3  # Number of similarity chunks to return


@app.post("/vector_search", tags=["VectorDB"])
def similarity_search(request: SearchRequest):
    try:
        docs = rag_chain.get_retrieved_documents(query=request.search_str)

        return {"status": status.HTTP_200_OK, "results": docs}
    except Exception as e:
        logger.error(f"Error in /vector_search: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error in request: {str(e)}",
        )


class RAGRequest(BaseModel):
    query: str


@app.post("/rag", tags=["RAG"])
async def rag_chain_invoke(request: RAGRequest):

    # Get Query
    query = request.query
    if not query:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty or None String Value in Query...",
        )

    # Query the RAG Chain
    response = rag_chain.process_query(query=query, stream_response=False)

    # Return Success
    return {"status": status.HTTP_200_OK, "response": response}


@app.post("/clear_memory", tags=["RAG"])
async def clear_memory():
    """Clear the RAG chain memory to reset conversation history."""
    try:
        rag_chain.clear_memory()
        return {"status": status.HTTP_200_OK, "message": "Memory cleared successfully"}
    except Exception as e:
        logger.error(f"Error clearing memory: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error clearing memory: {str(e)}",
        )


@app.websocket("/ws/stream")
async def chat(websocket: WebSocket):
    await websocket.accept()
    try:
        response = ""
        while True:
            # Get frontend data
            data = await websocket.receive_json()

            # Check if data has "query" attribute (needed)
            if "query" not in data:
                await websocket.send_text("<<E:NO_QUERY>>")
                break

            # Else get query
            query = data["query"]

            # Generate response in real time
            for token in rag_chain.process_query(query=query, stream_response=True):
                await websocket.send_text(token.content)
                await asyncio.sleep(0)
                response += token.content

            # End of response
            await websocket.send_text("<<END>>")

    except Exception as e:
        print(f"Error in WebSocket Connection: {e}")
