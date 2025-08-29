# Standard library imports
import os
from datetime import datetime, timedelta
from typing import List
import json
import asyncio

# Third-party imports
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

# Local imports
from database.connect import get_db_session, init_db, close_db
from bot.router import router as hr_router
from csv_upload_router import router as csv_router
from track_selection.router import router as track_router

# Initialize FastAPI app
app = FastAPI(
    title="HR Bot with CSV Upload",
    description="HR Chatbot with CSV Upload Capabilities",
    version="1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(hr_router)
app.include_router(csv_router)
app.include_router(track_router)

@app.get("/")
async def root():
    return {"message": "Welcome to HR Bot with CSV Upload"}

# Application lifecycle hooks
@app.on_event("startup")
async def on_startup():
    """Initialize database on application startup"""
    await init_db()
    print("Application started and database initialized")

@app.on_event("shutdown")
async def on_shutdown():
    """Clean up database connections on application shutdown"""
    await close_db()
    print("Application shutting down, database connections closed")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
