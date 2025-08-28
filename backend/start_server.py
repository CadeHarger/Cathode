#!/usr/bin/env python3
"""
Start script for the Cathode Playlist API server
"""
import uvicorn
from api_server import app

if __name__ == "__main__":
    print("🎵 Starting Cathode Playlist API server...")
    print("📍 Server will be available at: http://localhost:8000")
    print("📖 API docs will be available at: http://localhost:8000/docs")
    print("🔄 Auto-reload is enabled for development")
    print()
    
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
