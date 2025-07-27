from fastapi import APIRouter, HTTPException, UploadFile, File, Query, Header, Depends
from app.models.api_models import QARequest, QAResponse
from app.agent.agent import get_agent
from app.db.user_handler import get_user_service
from app.core.config import get_settings
from app.models.user_models import User
import os
import logging

router = APIRouter()
# Configure logger for the router
logger = logging.getLogger(__name__)


async def get_current_user(authorization: str = Header(...)) -> User:
    """
    Dependency to validate user token and return current user.

    Args:
        authorization: Authorization header containing the token

    Returns:
        The authenticated user

    Raises:
        HTTPException: If token is invalid or user not found
    """
    # Extract token from Authorization header
    # Expected format: "Bearer <token>" or just "<token>"
    token = authorization
    if authorization.startswith("Bearer "):
        token = authorization[7:]

    user_service = get_user_service()
    user = await user_service.authenticate_user(token)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return user


@router.post("/docs", response_model=dict)
async def agent_ingest_document(
    file: UploadFile = File(...), current_user: User = Depends(get_current_user)
):
    """Save uploaded file to watch folder for automatic ingestion."""
    logger.info(f"User {current_user.email} uploading document: {file.filename}")

    # Validate file size (2 MiB limit)
    if file.size and file.size > 2 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large (max 2 MiB)")

    # Get the watch folder path from settings
    settings = get_settings()
    watch_folder = settings.watch_folder
    
    # Ensure watch folder exists
    os.makedirs(watch_folder, exist_ok=True)
    
    # Save file to watch folder
    file_path = os.path.join(watch_folder, file.filename)
    content = await file.read()
    
    # Check if file already exists
    if os.path.exists(file_path):
        # Raise an error if file already exists
        raise HTTPException(
            status_code=400,
            detail=f"File {file.filename} already exists in watch folder"
        )
    
    # Write the file
    with open(file_path, "wb") as f:
        f.write(content)
    
    # Log the document upload in user history
    user_service = get_user_service()
    await user_service.add_qa_to_history(
        current_user.id,
        f"Uploaded document: {os.path.basename(file_path)}",
        "Document saved to watch folder for automatic ingestion"
    )

    return {"file_path": os.path.basename(file_path), "status": "uploaded"}


@router.get("/docs/{doc_id}/summary")
async def agent_get_summary(
    doc_id: str,
    length: int = Query(150, ge=50, le=500),
    current_user: User = Depends(get_current_user),
):
    """Agent writes fresh summary for a document."""
    logger.info(f"User {current_user.email} requesting summary for document: {doc_id}")

    agent = get_agent()
    prompt = f"Summarise the document {doc_id} in {length} words."

    result = await agent.arun(prompt)

    # Log the summary request in user history
    user_service = get_user_service()
    await user_service.add_qa_to_history(
        current_user.id,
        f"Requested summary for document {doc_id} ({length} words)",
        f"Summary generated: {result[:100]}..." if len(result) > 100 else result,
    )

    return {"summary": result}


@router.get("/docs/{doc_id}/topics")
async def agent_get_topics(doc_id: str, current_user: User = Depends(get_current_user)):
    """Agent fetches topic tags for a document."""
    logger.info(f"User {current_user.id} requesting topics for document: {doc_id}")

    agent = get_agent()
    prompt = f"List the topics of document {doc_id}."
    result = await agent.arun(prompt)

    # Assuming agent returns topics as a list or comma-separated string
    if isinstance(result, str):
        topics = [topic.strip() for topic in result.split(",")]
    else:
        topics = result

    # Log the topics request in user history
    user_service = get_user_service()
    await user_service.add_qa_to_history(
        current_user.id,
        f"Requested topics for document {doc_id}",
        f"Topics found: {', '.join(topics)}",
    )

    return {"topics": topics}


@router.post("/docs/{doc_id}/qa", response_model=QAResponse)
async def agent_qa(doc_id: str, request: QARequest, current_user: User = Depends(get_current_user)):
    """Agent answers a question about a specific document."""
    try:
        logger.info(
            f"User {current_user.email} asking question about document {doc_id}: {request.question}"
        )

        agent = get_agent()
        prompt = f"Answer the user {current_user.id} question '{request.question}' based on document {doc_id}. "
        result = await agent.arun(prompt)

        # Log the Q/A in user history
        user_service = get_user_service()
        await user_service.add_qa_to_history(current_user.id, request.question, result)

        return QAResponse(answer=result, doc_id=doc_id, session_id=request.session_id or "default")
    except Exception as e:
        logger.error(f"Error processing QA request for doc_id {doc_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing QA request: {str(e)}")


@router.post("/qa", response_model=QAResponse)
async def agent_general_qa(request: QARequest, current_user: User = Depends(get_current_user)):
    """Agent answers a general question, optionally about a specific document."""
    try:
        logger.info(f"User {current_user.email} asking general question: {request.question}")

        agent = get_agent()

        if request.doc_id:
            prompt = f"Answer the user {current_user.id} question '{request.question}' based on document {request.doc_id}."
        else:
            prompt = f"Answer the user {current_user.id} question: {request.question}"

        result = await agent.arun(prompt)

        # Log the Q/A in user history
        user_service = get_user_service()
        await user_service.add_qa_to_history(current_user.id, request.question, result)

        return QAResponse(
            answer=result, doc_id=request.doc_id, session_id=request.session_id or "default"
        )
    except Exception as e:
        logger.error(f"Error processing QA request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing QA request: {str(e)}")


@router.delete("/docs/{filename}", response_model=dict)
async def delete_document(
    filename: str, current_user: User = Depends(get_current_user)
):
    """Delete a document from the watch folder."""
    logger.info(f"User {current_user.email} deleting document: {filename}")
    
    # Get the watch folder path from settings
    settings = get_settings()
    watch_folder = settings.watch_folder
    
    # Build the full file path
    file_path = os.path.join(watch_folder, filename)
    
    # Check if the file exists
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"File not found: {filename}")
    
    # Check if it's a file (not a directory)
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=400, detail=f"Not a file: {filename}")
    
    # Delete the file
    try:
        os.unlink(file_path)
        
        # Log the document deletion in user history
        user_service = get_user_service()
        await user_service.add_qa_to_history(
            current_user.id,
            f"Deleted document: {filename}",
            "Document successfully deleted"
        )
        
        return {"filename": filename, "status": "deleted"}
    except Exception as e:
        logger.error(f"Error deleting document {filename}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting document: {str(e)}")
