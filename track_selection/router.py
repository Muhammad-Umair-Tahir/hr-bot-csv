from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

# Import the TrackSelectionAI class
from track_selection.track_bot import TrackSelectionAI

router = APIRouter(prefix="/api/v1/track-selection", tags=["Track Selection"])

# Initialize the AI once (reuse across requests)
ai = TrackSelectionAI()


class EvaluateRequest(BaseModel):
    faculty_id: int = Field(..., gt=0, description="Database ID of the faculty member")
    track_id: int = Field(..., gt=0, description="Database ID of the track")


class EvaluateResponse(BaseModel):
    decision: str = Field(..., description="APPROVED or NOT APPROVED")
    remarks: str = Field(..., description="Detailed policy-based reasoning")


@router.post("/evaluate", response_model=EvaluateResponse)
async def evaluate_track_selection(payload: EvaluateRequest):
    """Evaluate eligibility for a track using faculty_id and track_id."""
    try:
        result = await ai.evaluate_track_eligibility(
            faculty_id=payload.faculty_id, track_id=payload.track_id
        )

        # Basic normalization of decision text
        decision = (result.get("decision") or "NOT APPROVED").strip().upper()
        if decision not in {"APPROVED", "NOT APPROVED"}:
            decision = "NOT APPROVED"

        remarks = result.get("remarks") or ""
        return EvaluateResponse(decision=decision, remarks=remarks)
    except HTTPException:
        raise
    except Exception as e:
        # Log in server console and return generic 500
        print(f"Track selection evaluation error: {e}")
        raise HTTPException(status_code=500, detail="Failed to evaluate track selection.")


@router.get("/health")
async def health_check():
    return {"status": "ok"}
