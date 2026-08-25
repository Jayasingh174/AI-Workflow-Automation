import os
import shutil
import uuid
from fastapi import APIRouter, UploadFile, File, BackgroundTasks
from app.pipeline.automation_pipeline import process_document_workflow
from app.db.session import async_session_maker # Import your session maker directly

router = APIRouter(prefix="/api/v1/workflow", tags=["Automation"])

# This wrapper ensures the background task gets its own, fresh DB connection
async def run_workflow_safely(file_path: str, filename: str):
    async with async_session_maker() as db:
        try:
            await process_document_workflow(file_path, filename, db)
        finally:
            # Optional: Clean up the temporary file after processing is done
            if os.path.exists(file_path):
                os.remove(file_path)

@router.post("/process", summary="Trigger Automated AI Pipeline")
async def trigger_workflow(
    background_tasks: BackgroundTasks, 
    file: UploadFile = File(...)
    # Note: We removed the `db: AsyncSession = Depends(get_db)` injection here
):
    """
    Uploads a document and starts the automated processing pipeline.
    Uses BackgroundTasks to immediately return a response while processing continues.
    """
    # 1. Ensure the uploads directory exists
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)

    # 2. Secure the filename to prevent collisions and path traversal
    safe_filename = f"{uuid.uuid4()}_{file.filename}"
    temp_path = os.path.join(upload_dir, safe_filename)
    
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 3. Add the safely wrapped workflow to background tasks
    background_tasks.add_task(run_workflow_safely, temp_path, file.filename) # type: ignore

    return {
        "status": "accepted",
        "message": f"Document {file.filename} uploaded successfully. Analysis is running in the background."
    }
