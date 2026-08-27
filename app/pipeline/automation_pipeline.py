import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.model import DocumentAnalysis
from app.brain.document_service import process_document 
from app.brain.agent_service import run_sequential_pipeline

logger = logging.getLogger(__name__)

async def process_document_workflow(file_path: str, filename: str, db: AsyncSession) -> dict:
    """
    Automated workflow: Upload -> Extract -> DB -> AI Analysis -> DB Update
    """
    # Initialize variables at the top to avoid UnboundLocalError in the except block
    doc_id = None
    new_doc = None
    
    try:
        # Step 1: Extract Text
        logger.info(f"Extracting text from {filename}...")
        raw_text = await process_document(file_path) 
        
        # Step 2: Initial DB Storage (Status: Processing)
        new_doc = DocumentAnalysis(
            filename=filename,
            raw_text=raw_text,
            status="processing"
        )
        db.add(new_doc)
        await db.commit()
        await db.refresh(new_doc)
        doc_id = new_doc.id

        # Step 3: Run AI Analysis
        logger.info(f"Running AI analysis for ID: {doc_id}...")
        analysis_result = await run_sequential_pipeline(file_path)
        
        if "error" in analysis_result:
            raise Exception(analysis_result["error"])
        

        if new_doc is not None:  # <--- This satisfies the static type checker
            new_doc.ai_analysis = analysis_result # pyright: ignore[reportAttributeAccessIssue]
            new_doc.status = "completed" # pyright: ignore[reportAttributeAccessIssue]
            
            db.add(new_doc)
            await db.commit()

        logger.info(f"Workflow completed successfully for ID: {doc_id}")
        return {"status": "success", "document_id": doc_id, "data": analysis_result}
    
    except Exception as e:
        logger.error(f"Workflow failed: {str(e)}")
        
        # Step 5: Graceful Error Handling in DB
        if new_doc is not None:
            try:
                # Fix: Always rollback the session first! 
                # If a DB error caused the exception, the session is in an invalid state.
                await db.rollback() 
                
                # Now we can safely update the status to failed
                new_doc.status = "failed" # type: ignore
                new_doc.ai_analysis = {"error": str(e)} # type: ignore
                
                db.add(new_doc)
                await db.commit()
            except Exception as inner_e:
                # Fix: Catch the specific exception rather than a bare 'except:'
                logger.error(f"Failed to update document status to 'failed' in DB: {str(inner_e)}")
            
        return {"status": "error", "message": str(e)}
