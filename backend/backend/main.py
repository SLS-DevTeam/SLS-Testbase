import os
from fastapi import FastAPI, HTTPException, Depends, Request
from pydantic import BaseModel
import logging
from auth import verify_supabase_token
from drive import list_drive_files
from chat import process_chat_query
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Legal Research MVP API")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ----- Models -----
class ChatRequest(BaseModel):
    query: str
    context: str = ""
    enable_web_search: bool = False

class ChatResponse(BaseModel):
    response: str

class FolderRequest(BaseModel):
    folder_id: str

# ----- Endpoints -----

# This endpoint expects that the user has already signed in via Supabase Google OAuth
# The Supabase client on the front end passes the JWT token in the Authorization header.
@app.get("/drive-files")
async def drive_files(folder_id: str, request: Request):
    # Verify token using Supabase (our helper in auth.py)
    user = verify_supabase_token(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        files = list_drive_files(folder_id, user)
        return {"files": files}
    except Exception as e:
        logger.error("Error fetching drive files: %s", str(e))
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.post("/chat", response_model=ChatResponse)
async def chat(chat_req: ChatRequest, request: Request):
    # Verify user via Supabase token
    user = verify_supabase_token(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        response = process_chat_query(chat_req.query, chat_req.context, chat_req.enable_web_search)
        return {"response": response}
    except Exception as e:
        logger.error("Chat processing error: %s", str(e))
        raise HTTPException(status_code=500, detail="Internal Server Error")
