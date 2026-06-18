import asyncio
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
import json
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from api_hybrid_agent import run_hybrid_search_api
from data_manager import initialize_data_manager, get_data_manager

# Job status enum
class JobStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

# Request/Response models
class PlaylistRequest(BaseModel):
    prompt: str
    filters: Dict[str, Any]  # Contains genres list and exploration level

class CreateJobResponse(BaseModel):
    job_id: str
    initial_song_count: int

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

# Store background tasks for cancellation
active_tasks: Dict[str, asyncio.Task] = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events for FastAPI"""
    # Startup: Initialize data manager with preloaded embeddings and FAISS index
    print("🚀 Starting Cathode Playlist API...")
    print("📊 Loading embeddings and metadata into memory...")
    print("🔍 Building FAISS index for fast vector search...")
    
    try:
        initialize_data_manager()
        data_manager = get_data_manager()
        print(f"✅ Startup complete! Ready to serve {data_manager.get_total_songs():,} songs")
    except Exception as e:
        print(f"❌ Failed to initialize data manager: {e}")
        raise
    
    yield
    
    # Shutdown
    print("🛑 Shutting down Cathode Playlist API...")

app = FastAPI(
    title="Cathode Playlist API", 
    version="1.0.0",
    lifespan=lifespan
)

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
        # Create progress callback function that checks for cancellation
        async def progress_callback(progress: int, message: str):
            # Check if job was cancelled
            if job_id in jobs_store and jobs_store[job_id]["status"] == JobStatus.CANCELLED:
                raise asyncio.CancelledError("Job was cancelled by user")
            update_job_progress(job_id, progress, message)
        
        # Check for cancellation before starting
        if job_id in jobs_store and jobs_store[job_id]["status"] == JobStatus.CANCELLED:
            return
        
        # Run the actual hybrid search
        search_result = await run_hybrid_search_api(
            user_experience=prompt,
            genres=genres,
            top_k=25,
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
        
        # Check one more time before marking as completed
        if job_id in jobs_store and jobs_store[job_id]["status"] == JobStatus.CANCELLED:
            return
        
        # Mark job as completed
        jobs_store[job_id].update({
            "status": JobStatus.COMPLETED,
            "progress": 100,
            "message": "Playlist created successfully!",
            "result": result.dict(),
            "updated_at": datetime.now()
        })
        
    except asyncio.CancelledError:
        # Job was cancelled, don't update status (it's already CANCELLED)
        print(f"Job {job_id} was cancelled during execution")
        
    except Exception as e:
        # Only mark as failed if not already cancelled
        if job_id in jobs_store and jobs_store[job_id]["status"] != JobStatus.CANCELLED:
            jobs_store[job_id].update({
                "status": JobStatus.FAILED,
                "progress": 0,
                "message": "Failed to create playlist",
                "error": str(e),
                "updated_at": datetime.now()
            })
    finally:
        # Clean up background task reference
        if job_id in active_tasks:
            del active_tasks[job_id]

@app.post("/api/playlist", response_model=CreateJobResponse)
async def create_playlist(request: PlaylistRequest, background_tasks: BackgroundTasks):
    """Start playlist creation job"""
    job_id = str(uuid.uuid4())
    
    # Get the total song count from preloaded data manager
    try:
        data_manager = get_data_manager()
        initial_song_count = data_manager.get_total_songs()
    except Exception:
        initial_song_count = 0

    # Initialize job in store
    jobs_store[job_id] = {
        "job_id": job_id,
        "status": JobStatus.PENDING,
        "progress": 0,
        "message": f"Dataset loaded with {initial_song_count:,} total songs",
        "result": None,
        "error": None,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "request": request.dict()
    }
    
    # Create and store the background task for cancellation
    genres = request.filters.get("genres", [])
    task = asyncio.create_task(process_playlist_creation(job_id, request.prompt, genres))
    active_tasks[job_id] = task
    
    return {"job_id": job_id, "initial_song_count": initial_song_count}

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

@app.delete("/api/job/{job_id}")
async def cancel_job(job_id: str):
    """Cancel a job and stop its computation"""
    if job_id not in jobs_store:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job_data = jobs_store[job_id]
    
    # Only cancel if job is still running
    if job_data["status"] in [JobStatus.PENDING, JobStatus.IN_PROGRESS]:
        # Update job status first
        jobs_store[job_id].update({
            "status": JobStatus.CANCELLED,
            "progress": 0,
            "message": "Job cancelled by user",
            "updated_at": datetime.now()
        })
        
        # Cancel the actual background task if it exists
        if job_id in active_tasks:
            task = active_tasks[job_id]
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass  # Expected when cancelling
            del active_tasks[job_id]
        
        return {"message": "Job cancelled successfully"}
    else:
        return {"message": f"Job is already {job_data['status']}, cannot cancel"}

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

@app.get("/health")
async def health_check():
    """Simple health check endpoint"""
    return {
        "status": "healthy",
        "service": "Cathode Playlist API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080, reload=True)
