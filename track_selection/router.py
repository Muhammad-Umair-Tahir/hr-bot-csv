from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List

# Import the TrackSelectionAI class
from track_selection.track_bot import TrackSelectionAI
from database.connect import get_db_session
from sqlalchemy.ext.asyncio import AsyncSession
from database.faculty_track_decision import save_faculty_track_decision

router = APIRouter(prefix="/api/v1/track-selection", tags=["Track Selection"])

# Initialize the AI once (reuse across requests)
ai = TrackSelectionAI()


class EvaluateRequest(BaseModel):
    faculty_id: int = Field(..., gt=0, description="Database ID of the faculty member")
    track_id: int = Field(..., gt=0, description="Database ID of the track")
    track_level_id: Optional[int] = Field(None, description="Optional track level ID")
    academic_year_id: Optional[int] = Field(None, description="Optional academic year ID; if absent, use current year")


class EvaluateResponse(BaseModel):
    decision: str = Field(..., description="APPROVED BY AI or NOT APPROVED BY AI")
    remarks: str = Field(..., description="Detailed policy-based reasoning")


@router.post("/evaluate", response_model=EvaluateResponse)
async def evaluate_track_selection(payload: EvaluateRequest, session: AsyncSession = Depends(get_db_session)):
    """Evaluate eligibility for a track using faculty_id and track_id."""
    try:
        result = await ai.evaluate_track_eligibility(
            faculty_id=payload.faculty_id, track_id=payload.track_id
        )

        # Basic normalization of decision text
        decision = (result.get("decision") or "NOT APPROVED").strip().upper()
        if decision not in {"APPROVED", "NOT APPROVED"}:
            decision = "NOT APPROVED"

        raw = result.get("remarks") or ""

        # Enforce 3–4 one-line bullets in remarks
        def normalize_bullets(text: str) -> str:
            lines = [l.strip() for l in text.splitlines() if l.strip()]
            # Extract lines starting with '-' or '*' or looks like bullet-ish
            bullets: List[str] = []
            for l in lines:
                if l.startswith(("- ", "* ")):
                    bullets.append(l[2:].strip())
                elif l[:2].isdigit() and "." in l[:4]:
                    # "1. something" -> convert
                    bullets.append(l.split(".", 1)[1].strip())
                elif l.lower().startswith("remarks:"):
                    continue
            if not bullets:
                # Fallback: take up to first 4 meaningful lines
                bullets = [l for l in lines if len(l) > 10][:4]
            # Trim each bullet to one line and length bound
            norm = []
            for b in bullets:
                one = " ".join(b.split())
                if len(one) > 160:
                    one = one[:157].rstrip() + "..."
                norm.append(f"- {one}")
            # Ensure 3–4 bullets
            if len(norm) < 3 and lines:
                for l in lines:
                    if l not in bullets and len(norm) < 3:
                        one = " ".join(l.split())
                        if len(one) > 160:
                            one = one[:157].rstrip() + "..."
                        norm.append(f"- {one}")
            return "\n".join(norm[:4])

        remarks = normalize_bullets(raw)

        # Persist decision to DB (use base decision without the AI suffix)
        await save_faculty_track_decision(
            session,
            faculty_id=payload.faculty_id,
            track_id=payload.track_id,
            track_level_id=payload.track_level_id,
            academic_year_id=payload.academic_year_id,
            decision=decision,
            remarks=remarks,
        )

        # Return decision with explicit AI provenance
        decision_out = decision if decision.endswith(" BY AI") or decision.endswith("BY AI") else f"{decision} BY AI"
        return EvaluateResponse(decision=decision_out, remarks=remarks)
    except HTTPException:
        raise
    except Exception as e:
        # Log in server console and return generic 500
        print(f"Track selection evaluation error: {e}")
        raise HTTPException(status_code=500, detail="Failed to evaluate track selection.")


@router.get("/health")
async def health_check():
    return {"status": "ok"}
