from fastapi import FastAPI, HTTPException, status, WebSocket, File, UploadFile
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from RAGChain import vector_store, text_splitter, rag_chain
import logging
import asyncio

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
    # Decode to string (adjust encoding if needed)
    try:
        file_str = content_bytes.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Could not decode file contents as UTF-8",
        )

    # Validate non-empty content
    if not file_str or file_str.strip() == "":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File is empty or contains only whitespace",
        )

    # Split text into chunks/documents
    texts = text_splitter.create_documents([file_str])

    # Add to vector store and get generated IDs
    ids = vector_store.add_documents(texts)

    return {"status": status.HTTP_201_CREATED, "uploaded_ids": ids}


class SearchRequest(BaseModel):
    search_str: str  # String to search
    n: int = 2  # Number of similarity chunks to return


@app.post("/vector_search", tags=["VectorDB"])
def similarity_search(request: SearchRequest):
    try:
        results = vector_store.similarity_search(request.search_str, k=request.n)

        return {"status": status.HTTP_200_OK, "results": results}
    except Exception as e:
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
    response = rag_chain.invoke(query)

    # Return Success
    return {"status": status.HTTP_200_OK, "response": response}


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
            for token in rag_chain.stream(query):
                await websocket.send_text(token.content)
                await asyncio.sleep(0)
                response += token.content

            # End of response
            await websocket.send_text("<<END>>")

    except Exception as e:
        print(f"Error in WebSocket Connection: {e}")
