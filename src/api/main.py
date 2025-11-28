"""FastAPI application for Market Intelligence API."""

import uuid
from datetime import datetime
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.schemas import (
    AnalysisRequest,
    AnalysisResponse,
    StatusResponse,
    HistoryResponse,
    HistoryItem,
)
from src.workflows.market_analysis import MarketIntelligenceWorkflow
from src.utils.logging import setup_logger

logger = setup_logger(__name__)

# API application
app = FastAPI(
    title="Market Intelligence API",
    description="AI-powered competitive intelligence in 15 minutes",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage (replace with database in production)
analysis_store: dict[str, dict] = {}


@app.get("/")
async def root():
    """API root endpoint."""
    return {
        "name": "Market Intelligence API",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


async def run_analysis_task(run_id: str, request: AnalysisRequest):
    """Background task to run analysis."""
    try:
        # Update status to running
        analysis_store[run_id]["status"] = "running"
        analysis_store[run_id]["current_agent"] = "research"

        logger.info(f"Starting analysis {run_id} for {request.company_name}")

        # Create workflow
        workflow = MarketIntelligenceWorkflow(max_budget=request.max_budget)

        # Run analysis
        result = await workflow.run(
            company_name=request.company_name,
            industry=request.industry,
            thread_id=run_id,
        )

        # Update store with results
        analysis_store[run_id].update(
            {
                "status": "completed" if not result.get("errors") else "failed",
                "executive_summary": result.get("executive_summary"),
                "full_report": result.get("full_report"),
                "total_cost": result.get("total_cost", 0.0),
                "total_tokens": result.get("total_tokens", 0),
                "sources_count": len(result.get("raw_sources", [])),
                "errors": result.get("errors", []),
                "approved": result.get("approved", False),
                "current_agent": result.get("current_agent"),
                "completed_at": datetime.now().isoformat(),
            }
        )

        logger.info(f"Analysis {run_id} completed")

    except Exception as e:
        logger.error(f"Analysis {run_id} failed: {e}")
        analysis_store[run_id].update(
            {
                "status": "failed",
                "errors": [str(e)],
            }
        )


@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_company(request: AnalysisRequest, background_tasks: BackgroundTasks):
    """
    Start market intelligence analysis for a company.

    Returns immediately with run_id. Check status via /status/{run_id}.
    """
    # Generate unique run ID
    run_id = str(uuid.uuid4())

    # Initialize analysis record
    analysis_store[run_id] = {
        "run_id": run_id,
        "company_name": request.company_name,
        "industry": request.industry,
        "model": request.model,
        "max_budget": request.max_budget,
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "executive_summary": None,
        "full_report": None,
        "total_cost": 0.0,
        "total_tokens": 0,
        "sources_count": 0,
        "errors": [],
        "approved": False,
    }

    # Start analysis in background
    background_tasks.add_task(run_analysis_task, run_id, request)

    logger.info(f"Analysis {run_id} queued for {request.company_name}")

    return AnalysisResponse(**analysis_store[run_id])


@app.get("/status/{run_id}", response_model=StatusResponse)
async def get_status(run_id: str):
    """
    Get status of a running or completed analysis.
    """
    if run_id not in analysis_store:
        raise HTTPException(status_code=404, detail="Analysis not found")

    analysis = analysis_store[run_id]

    # Calculate progress based on agent
    progress_map = {
        "research": 0.2,
        "analysis": 0.5,
        "writing": 0.8,
        "human_review": 0.9,
        "completed": 1.0,
    }

    current_agent = (
        str(analysis.get("current_agent")) if analysis.get("current_agent") else None
    )
    progress = progress_map.get(current_agent, 0.0) if current_agent else 0.0
    if analysis["status"] == "completed":
        progress = 1.0

    return StatusResponse(
        run_id=run_id,
        status=analysis["status"],
        current_agent=current_agent,
        progress=progress,
        message=f"Currently processing: {current_agent}" if current_agent else None,
    )


@app.get("/result/{run_id}", response_model=AnalysisResponse)
async def get_result(run_id: str):
    """
    Get full results of a completed analysis.
    """
    if run_id not in analysis_store:
        raise HTTPException(status_code=404, detail="Analysis not found")

    analysis = analysis_store[run_id]

    if analysis["status"] not in ["completed", "failed"]:
        raise HTTPException(
            status_code=425,
            detail=f"Analysis still {analysis['status']}, check /status/{run_id}",
        )

    return AnalysisResponse(**analysis)


@app.get("/history", response_model=HistoryResponse)
async def get_history(limit: int = 10, offset: int = 0):
    """
    Get history of past analyses.
    """
    # Sort by created_at descending
    sorted_analyses = sorted(
        analysis_store.values(), key=lambda x: x.get("created_at", ""), reverse=True
    )

    # Paginate
    paginated = sorted_analyses[offset : offset + limit]

    history_items = [
        HistoryItem(
            run_id=a["run_id"],
            company_name=a["company_name"],
            created_at=a["created_at"],
            status=a["status"],
            total_cost=a.get("total_cost", 0.0),
            approved=a.get("approved", False),
        )
        for a in paginated
    ]

    return HistoryResponse(analyses=history_items, total=len(analysis_store))


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
