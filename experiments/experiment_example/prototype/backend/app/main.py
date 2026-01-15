from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import create_tables
from app.routers import api

app = FastAPI(
    title="SeaChain Traceability API",
    description="Enterprise seafood traceability platform for SIMP/IUU compliance",
    version="1.0.0",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://frontend:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(api.router, prefix="/api/v1")


@app.on_event("startup")
async def startup_event():
    """Create database tables on startup."""
    await create_tables()


@app.get("/health")
async def health_check():
    """Health check endpoint for container orchestration."""
    return {"status": "healthy", "service": "seachain-api"}


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {"message": "SeaChain Traceability API", "version": "1.0.0", "docs": "/docs"}
