# router.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
import asyncio

# Import the HR_AI class
from bot.hr import HR_AI

router = APIRouter()

# Initialize the HR_AI agent once
hr_agent = HR_AI()


class MessageRequest(BaseModel):
    role: str = Field(..., example="user")
    message: str
    session_id: str = "default"


class MessageResponse(BaseModel):
    role: str = "AI"
    message: str


@router.post("/api/v1/chat", response_model=MessageResponse)
async def chat(request: MessageRequest):
    if request.role.lower() != "user":
        raise HTTPException(status_code=400, detail="Only 'user' role is allowed in request")

    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    try:
        # Call the .generate() method from HR_AI
        response_text = await hr_agent.generate(request.message, request.session_id)
        return MessageResponse(role="AI", message=response_text)
    except Exception as e:
        # Log the error for debugging
        print(f"An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail="An internal server error occurred.")
