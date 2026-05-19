from fastapi import APIRouter
from app.core.knowledge_loader import get_status, KNOWLEDGE_FILES

router = APIRouter()


@router.get("/knowledge/status", tags=["Knowledge"], summary="Knowledge base status")
async def knowledge_status():
    """
    Check whether all knowledge base files are present and non-empty.
    No authentication required.
    """
    file_status = get_status()
    all_ok = all(v["status"] == "ok" for v in file_status.values())
    return {
        "knowledge_base": "loaded" if all_ok else "incomplete",
        "expected_files": KNOWLEDGE_FILES,
        "files": file_status,
    }
