import asyncio
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
import json

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from api_hybrid_agent import run_hybrid_search_api

# Job status enum
class JobStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

# Request/Response models
class PlaylistRequest(BaseModel):
    prompt: str
    filters: Dict[str, Any]  # Contains genres list and exploration level

class PlaylistResponse(BaseModel):
    id: str
    title: str
    genres: List[str]
    songs: List[Dict[str, Any]]

class JobStatusResponse(BaseModel):
    job_id: str
    status: JobStatus
    progress: int
    message: str
    result: Optional[PlaylistResponse] = None
    error: Optional[str] = None
    created_at: datetime
    updated_at: datetime

# Global job storage (in production, use Redis or database)
jobs_store: Dict[str, Dict[str, Any]] = {}

app = FastAPI(title="Cathode Playlist API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def update_job_progress(job_id: str, progress: int, message: str, status: JobStatus = JobStatus.IN_PROGRESS):
    """Update job progress and status"""
    if job_id in jobs_store:
        jobs_store[job_id].update({
            "progress": progress,
            "message": message,
            "status": status,
            "updated_at": datetime.now()
        })

async def process_playlist_creation(job_id: str, prompt: str, genres: List[str]):
    """Background task to process playlist creation"""
    try:
        # Create progress callback function
        async def progress_callback(progress: int, message: str):
            update_job_progress(job_id, progress, message)
        
        # Run the actual hybrid search
        search_result = await run_hybrid_search_api(
            user_experience=prompt,
            genres=genres,
            top_k=8,
            progress_callback=progress_callback
        )
        
        if not search_result["success"]:
            raise Exception(search_result.get("error", "Unknown error occurred"))
        
        # Create the result
        result = PlaylistResponse(
            id=job_id,
            title=prompt[:50] if len(prompt) <= 50 else prompt[:47] + "...",
            genres=genres,
            songs=search_result["songs"]
        )
        
        # Mark job as completed
        jobs_store[job_id].update({
            "status": JobStatus.COMPLETED,
            "progress": 100,
            "message": "Playlist created successfully!",
            "result": result.dict(),
            "updated_at": datetime.now()
        })
        
    except Exception as e:
        # Mark job as failed
        jobs_store[job_id].update({
            "status": JobStatus.FAILED,
            "progress": 0,
            "message": "Failed to create playlist",
            "error": str(e),
            "updated_at": datetime.now()
        })

@app.post("/api/playlist", response_model=Dict[str, str])
async def create_playlist(request: PlaylistRequest, background_tasks: BackgroundTasks):
    """Start playlist creation job"""
    job_id = str(uuid.uuid4())
    
    # Initialize job in store
    jobs_store[job_id] = {
        "job_id": job_id,
        "status": JobStatus.PENDING,
        "progress": 0,
        "message": "Job queued",
        "result": None,
        "error": None,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "request": request.dict()
    }
    
    # Start background task
    genres = request.filters.get("genres", [])
    background_tasks.add_task(process_playlist_creation, job_id, request.prompt, genres)
    
    return {"job_id": job_id}

@app.get("/api/job/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """Get job status and result"""
    if job_id not in jobs_store:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job_data = jobs_store[job_id]
    
    return JobStatusResponse(
        job_id=job_data["job_id"],
        status=job_data["status"],
        progress=job_data["progress"],
        message=job_data["message"],
        result=PlaylistResponse(**job_data["result"]) if job_data["result"] else None,
        error=job_data["error"],
        created_at=job_data["created_at"],
        updated_at=job_data["updated_at"]
    )

@app.get("/api/jobs", response_model=List[JobStatusResponse])
async def list_jobs():
    """List all jobs (for debugging)"""
    return [
        JobStatusResponse(
            job_id=job_data["job_id"],
            status=job_data["status"],
            progress=job_data["progress"],
            message=job_data["message"],
            result=PlaylistResponse(**job_data["result"]) if job_data["result"] else None,
            error=job_data["error"],
            created_at=job_data["created_at"],
            updated_at=job_data["updated_at"]
        )
        for job_data in jobs_store.values()
    ]

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Cathode Playlist API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
