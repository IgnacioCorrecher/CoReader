from fastapi import FastAPI, HTTPException, status, WebSocket, File, UploadFile
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from RAGChain import vector_store, text_splitter, rag_chain
import logging
import asyncio
import uuid
from DocProcessing import DocProcessing
from langchain_core.documents import Document


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
    Upload a single file and save it to the vector store with metadata.
    """
    # Read file bytes
    content_bytes = await file.read()

    # Process file
    doc_processor = DocProcessing(file.filename, content_bytes)
    file_str = doc_processor.process_doc()

    # Generate unique file ID
    file_id = str(uuid.uuid4())

    # Split text into chunks/documents
    texts = text_splitter.create_documents([file_str])

    # Add metadata to each document chunk
    for doc in texts:
        doc.metadata = {
            "file_id": file_id,
            "filename": file.filename,
            "is_active": True,  # Files are active by default
        }

    # Add to vector store and get generated IDs
    ids = vector_store.add_documents(texts)

    return {
        "status": status.HTTP_201_CREATED,
        "uploaded_ids": ids,
        "file_id": file_id,
        "filename": file.filename,
    }


class ToggleFileStatusRequest(BaseModel):
    file_id: str
    is_active: bool


@app.post("/toggle_file_status", tags=["VectorDB"])
async def toggle_file_status(request: ToggleFileStatusRequest):
    """
    Toggle the active status of a file by updating all its document chunks.
    """
    try:
        # Get all documents for this file
        collection = vector_store.get()

        # Find document IDs that match this file_id
        doc_ids_to_update = []
        for i, metadata in enumerate(collection["metadatas"]):
            if metadata and metadata.get("file_id") == request.file_id:
                doc_ids_to_update.append(collection["ids"][i])

        # Check if file exists
        if not doc_ids_to_update:
            logger.warning(f"No documents found for file_id: {request.file_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No documents found for file_id: {request.file_id}. The file may have been deleted or corrupted.",
            )

        # Prepare documents for re-adding with updated metadata
        documents_to_read = []

        for i, metadata in enumerate(collection["metadatas"]):
            if metadata and metadata.get("file_id") == request.file_id:
                # Create updated metadata
                updated_metadata = metadata.copy()
                updated_metadata["is_active"] = request.is_active

                # Create document with updated metadata
                doc = Document(
                    page_content=collection["documents"][i], metadata=updated_metadata
                )
                documents_to_read.append(doc)

        # Delete old documents and re-add with updated metadata
        logger.info(
            f"Updating {len(doc_ids_to_update)} document chunks for file {request.file_id} to active={request.is_active}"
        )
        vector_store.delete(ids=doc_ids_to_update)
        vector_store.add_documents(documents_to_read, ids=doc_ids_to_update)

        return {
            "status": status.HTTP_200_OK,
            "message": f"File {request.file_id} active status updated to {request.is_active}",
            "updated_chunks": len(doc_ids_to_update),
        }

    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        logger.error(f"Error toggling file status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error toggling file status: {str(e)}",
        )


@app.get("/get_uploaded_files", tags=["VectorDB"])
async def get_uploaded_files():
    """
    Get list of all uploaded files with their active status.
    """
    try:
        collection = vector_store.get()

        # Group documents by file_id to get unique files and track active status
        files_dict = {}
        for metadata in collection["metadatas"]:
            if metadata and "file_id" in metadata:
                file_id = metadata["file_id"]
                is_active = metadata.get("is_active", True)

                if file_id not in files_dict:
                    files_dict[file_id] = {
                        "id": file_id,
                        "name": metadata.get("filename", "Unknown"),
                        "isActive": is_active,
                        "chunk_count": 1,
                        "active_chunks": 1 if is_active else 0,
                    }
                else:
                    files_dict[file_id]["chunk_count"] += 1
                    if is_active:
                        files_dict[file_id]["active_chunks"] += 1

                    # File is considered active if ALL chunks are active
                    files_dict[file_id]["isActive"] = (
                        files_dict[file_id]["active_chunks"]
                        == files_dict[file_id]["chunk_count"]
                    )

        # Clean up the response to only include necessary fields
        files_list = []
        for file_data in files_dict.values():
            files_list.append(
                {
                    "id": file_data["id"],
                    "name": file_data["name"],
                    "isActive": file_data["isActive"],
                }
            )

        logger.info(f"Found {len(files_list)} files in vector store")
        return {"status": status.HTTP_200_OK, "files": files_list}

    except Exception as e:
        logger.error(f"Error getting uploaded files: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting uploaded files: {str(e)}",
        )


@app.delete("/delete_file/{file_id}", tags=["VectorDB"])
async def delete_file(file_id: str):
    """
    Delete a file and all its document chunks from the vector store.
    """
    try:
        # Get all documents for this file
        collection = vector_store.get()

        # Find document IDs that match this file_id
        doc_ids_to_delete = []
        for i, metadata in enumerate(collection["metadatas"]):
            if metadata and metadata.get("file_id") == file_id:
                doc_ids_to_delete.append(collection["ids"][i])

        if not doc_ids_to_delete:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No documents found for file_id: {file_id}",
            )

        # Delete all chunks of this file
        vector_store.delete(ids=doc_ids_to_delete)

        return {
            "status": status.HTTP_200_OK,
            "message": f"File {file_id} deleted successfully",
            "deleted_chunks": len(doc_ids_to_delete),
        }

    except Exception as e:
        logger.error(f"Error deleting file: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting file: {str(e)}",
        )


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
    response, citations = rag_chain.process_query(query=query, stream_response=False)

    # Format citations
    formatted_citations = []
    for doc in citations:
        citation = {
            "content": doc.page_content,
            "filename": doc.metadata.get("filename", "Unknown"),
            "file_id": doc.metadata.get("file_id", ""),
        }
        formatted_citations.append(citation)

    # Return Success
    return {
        "status": status.HTTP_200_OK,
        "response": response,
        "citations": formatted_citations,
    }


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

            # Get citations first (but don't send them yet)
            retrieved_docs = rag_chain.get_citations_for_query(query)

            # Generate response in real time
            for token in rag_chain.process_query(query=query, stream_response=True):
                await websocket.send_text(token.content)
                await asyncio.sleep(0)
                response += token.content

            # Send citations after the response is complete
            if retrieved_docs:
                citations = []
                for doc in retrieved_docs:
                    citation = {
                        "content": doc.page_content,
                        "filename": doc.metadata.get("filename", "Unknown"),
                        "file_id": doc.metadata.get("file_id", ""),
                    }
                    citations.append(citation)

                import json

                await websocket.send_text(f"<<CITATIONS>>{json.dumps(citations)}")

            # End of response
            await websocket.send_text("<<END>>")

    except Exception as e:
        print(f"Error in WebSocket Connection: {e}")


@app.get("/debug_documents", tags=["VectorDB"])
async def debug_documents():
    """
    Debug endpoint to inspect all documents and their metadata.
    """
    try:
        collection = vector_store.get()

        debug_info = {"total_documents": len(collection["ids"]), "documents": []}

        for i, doc_id in enumerate(collection["ids"]):
            doc_info = {
                "id": doc_id,
                "content_preview": (
                    collection["documents"][i][:100] + "..."
                    if len(collection["documents"][i]) > 100
                    else collection["documents"][i]
                ),
                "metadata": (
                    collection["metadatas"][i] if collection["metadatas"] else None
                ),
            }
            debug_info["documents"].append(doc_info)

        return debug_info

    except Exception as e:
        logger.error(f"Error in debug_documents: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting debug info: {str(e)}",
        )


@app.get("/debug_file_status/{file_id}", tags=["VectorDB"])
async def debug_file_status(file_id: str):
    """
    Debug endpoint to inspect a specific file's status and chunks.
    """
    try:
        collection = vector_store.get()

        file_chunks = []
        for i, metadata in enumerate(collection["metadatas"]):
            if metadata and metadata.get("file_id") == file_id:
                chunk_info = {
                    "chunk_id": collection["ids"][i],
                    "is_active": metadata.get("is_active", "NOT_SET"),
                    "filename": metadata.get("filename", "NOT_SET"),
                    "content_preview": (
                        collection["documents"][i][:100] + "..."
                        if len(collection["documents"][i]) > 100
                        else collection["documents"][i]
                    ),
                    "content_length": len(collection["documents"][i]),
                    "full_metadata": metadata,
                }
                file_chunks.append(chunk_info)

        if not file_chunks:
            return {
                "file_id": file_id,
                "found": False,
                "message": "No chunks found for this file_id",
            }

        active_count = sum(1 for chunk in file_chunks if chunk["is_active"] is True)
        inactive_count = sum(1 for chunk in file_chunks if chunk["is_active"] is False)

        return {
            "file_id": file_id,
            "found": True,
            "total_chunks": len(file_chunks),
            "active_chunks": active_count,
            "inactive_chunks": inactive_count,
            "file_should_be_active": active_count == len(file_chunks),
            "chunks": file_chunks,
        }

    except Exception as e:
        logger.error(f"Error in debug_file_status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting file debug info: {str(e)}",
        )


@app.post("/debug_chunking", tags=["Debug"])
async def debug_chunking(text: str):
    """
    Debug endpoint to test how text would be chunked.
    """
    try:
        # Test the text formatter
        doc_processor = DocProcessing("test.txt", text.encode("utf-8"))
        formatted_text = doc_processor.text_formatter(text)

        # Test the text splitter
        chunks = text_splitter.create_documents([formatted_text])

        chunk_info = []
        for i, chunk in enumerate(chunks):
            chunk_info.append(
                {
                    "chunk_index": i,
                    "content_length": len(chunk.page_content),
                    "content_preview": (
                        chunk.page_content[:200] + "..."
                        if len(chunk.page_content) > 200
                        else chunk.page_content
                    ),
                    "content": chunk.page_content,
                }
            )

        return {
            "original_length": len(text),
            "formatted_length": len(formatted_text),
            "total_chunks": len(chunks),
            "formatted_text_preview": (
                formatted_text[:500] + "..."
                if len(formatted_text) > 500
                else formatted_text
            ),
            "chunks": chunk_info,
        }

    except Exception as e:
        logger.error(f"Error in debug_chunking: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error testing chunking: {str(e)}",
        )
