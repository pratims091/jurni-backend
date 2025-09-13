"""Main FastAPI application for Jurni Backend."""

import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn
from dotenv import load_dotenv

from app.routes.auth import router as auth_router
from app.routes.trips import router as trips_router
from app.routes.travel_planner import router as travel_planner_router

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    print("🚀 Jurni Backend starting up...")
    yield
    print("🛑 Jurni Backend shutting down...")


app = FastAPI(
    title="Jurni Backend API",
    description="Backend service for Jurni application with Firebase authentication",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors."""
    print(f"Global exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "An internal server error occurred",
            "error_code": "INTERNAL_ERROR"
        }
    )


@app.get("/")
async def root():
    """Root endpoint for health check."""
    return {
        "message": "Jurni Backend API is running",
        "version": "0.1.0",
        "status": "healthy"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": os.getenv("APP_START_TIME", "unknown")
    }


app.include_router(auth_router)
app.include_router(trips_router)
app.include_router(travel_planner_router)


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8001))
    host = os.getenv("HOST", "0.0.0.0")
    
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )
