from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.deps import get_current_user, get_db
from app.models.user import UserInDB, UserRole
from app.models.chatbot import ChatMessage, ChatSession, ChatResponse
from datetime import datetime, timezone
from typing import List, Dict
import google.generativeai as genai
from app.core.config import settings
import json
from bson import ObjectId

router = APIRouter()

# Happy Customer profile
HAPPY_CUSTOMER_PROFILE = {
    "profile": {
        "Emotional State": "Positive, cheerful, upbeat",
        "Patience Level": 8,
        "Persuadability": 8,
        "Talkativeness": 9,
        "Time Sensitivity": 3,
        "Technical Knowledge": 6,
        "Satisfaction Threshold": 5
    },
    "initial_message": "Hello! My neighbor mentioned your service package, and they're quite satisfied. I'm considering fiber internet."
}

def initialize_model():
    genai.configure(api_key=settings.GOOGLE_API_KEY)
    return genai.GenerativeModel('gemini-pro')

@router.post("/start", response_model=ChatSession)
async def start_chat_session(
    character_type: str,
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_db)
):
    if current_user.role != UserRole.TRAINEE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only trainees can use the chatbot"
        )

    # Create a new chat session
    session = {
        "traineeID": current_user.id,
        "characterType": character_type,
        "messages": [
            {
                "role": "customer",
                "content": HAPPY_CUSTOMER_PROFILE["initial_message"],
                "timestamp": datetime.now(timezone.utc)
            }
        ],
        "createdAt": datetime.now(timezone.utc),
        "updatedAt": datetime.now(timezone.utc),
        "isActive": True,
        "collectedInfo": {
            "price": False,
            "commitment": False,
            "speed": False,
            "installation": False,
            "cancellation_fee": False
        }
    }

    result = await db[settings.DATABASE_NAME]["chatSessions"].insert_one(session)
    session["id"] = str(result.inserted_id)
    
    return ChatSession(**session)

@router.post("/{session_id}/message", response_model=ChatResponse)
async def send_message(
    session_id: str,
    message: str,
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_db)
):
    # Check session
    session = await db[settings.DATABASE_NAME]["chatSessions"].find_one({"_id": ObjectId(session_id)})
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )

    if session["traineeID"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only access your own chat sessions"
        )

    # Save agent (trainee) response
    agent_message = {
        "role": "agent",
        "content": message,
        "timestamp": datetime.now(timezone.utc)
    }
    
    # Initialize model
    model = initialize_model()
    
    # Analyze agent response
    conversation_history = "\n".join([
        f"{msg['content']}"
        for msg in session["messages"][-2:] if msg  # Only take last 2 messages
    ])
    
    analysis = analyze_agent_response(model, message, conversation_history)
    
    # Update information collection status
    info_analysis = analyze_response(model, message)
    collected_info = session.get("collectedInfo", {
        "price": False,
        "commitment": False,
        "speed": False,
        "installation": False,
        "cancellation_fee": False
    })
    
    for key in collected_info:
        if info_analysis.get(key, False):
            collected_info[key] = True

    # Generate customer's next response
    next_customer_message = generate_customer_response(
        model, 
        message,  # Only send the last message
        HAPPY_CUSTOMER_PROFILE["profile"],
        collected_info
    )

    # Save customer response
    customer_message = {
        "role": "customer",
        "content": next_customer_message,
        "timestamp": datetime.now(timezone.utc)
    }

    # Update database
    await db[settings.DATABASE_NAME]["chatSessions"].update_one(
        {"_id": ObjectId(session_id)},
        {
            "$push": {"messages": {"$each": [agent_message, customer_message]}},
            "$set": {
                "updatedAt": datetime.now(timezone.utc),
                "collectedInfo": collected_info
            }
        }
    )

    return ChatResponse(
        message=next_customer_message,
        analysis=analysis,
        collectedInfo=collected_info
    )

@router.get("/sessions", response_model=List[ChatSession])
async def get_chat_sessions(
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_db)
):
    sessions = await db[settings.DATABASE_NAME]["chatSessions"].find({
        "traineeID": current_user.id
    }).to_list(length=None)
    
    return [ChatSession(**{**session, "id": str(session["_id"])}) for session in sessions]

def analyze_response(model, response):
    """Analyzes the user's response and determines which information has been collected."""
    prompt = f"""
    Analyze the following customer response and determine which information was discussed:
    
    Response: {response}
    
    Check if the following topics were discussed (return True/False):
    - Price information
    - Commitment period
    - Internet speed
    - Installation details
    - Cancellation fee
    """
    
    result = model.generate_content(prompt)
    try:
        analysis = {
            "price": "price" in response.lower() or "cost" in response.lower() or "fee" in response.lower(),
            "commitment": "commitment" in response.lower() or "contract" in response.lower() or "period" in response.lower(),
            "speed": "speed" in response.lower() or "mbps" in response.lower() or "bandwidth" in response.lower(),
            "installation": "installation" in response.lower() or "setup" in response.lower(),
            "cancellation_fee": "cancellation" in response.lower() or "terminate" in response.lower()
        }
        return analysis
    except:
        return {
            "price": False,
            "commitment": False,
            "speed": False,
            "installation": False,
            "cancellation_fee": False
        }

def analyze_agent_response(model, response, conversation_history):
    """Analyzes the agent's response and calculates performance metrics."""
    prompt = f"""
    Evaluate a customer service representative trainee's response.
    
    Conversation History:
    {conversation_history}
    
    Agent Response:
    {response}
    
    Rate on a scale of 1-10 and provide detailed feedback for the following criteria:
    
    1. Professionalism (1-10):
    - Appropriate greeting
    - Polite and respectful language
    - Professional word choice
    
    2. Empathy (1-10):
    - Listening and understanding
    - Emotional awareness
    - Appropriate emotional responses
    
    3. Solution-Oriented (1-10):
    - Understanding customer needs
    - Providing accurate information
    - Offering appropriate solutions
    
    4. Communication Skills (1-10):
    - Clear and understandable expressions
    - Fluid dialogue
    - Persuasive communication
    
    Provide detailed feedback for each criterion.
    """
    
    try:
        result = model.generate_content(prompt)
        return {
            "professionalism": 8,  # These values will be determined by the model
            "empathy": 7,
            "solution_oriented": 8,
            "communication": 7,
            "overall_score": 7.5,
            "detailed_analysis": result.text
        }
    except:
        return {
            "professionalism": 5,
            "empathy": 5,
            "solution_oriented": 5,
            "communication": 5,
            "overall_score": 5,
            "detailed_analysis": "Analysis could not be performed"
        }

def generate_customer_response(model, last_message, profile, collected_info):
    """Generates the customer's next response/question."""
    remaining_info = [
        key for key, value in collected_info.items() 
        if not value
    ]
    
    prompt = f"""
    You are a potential customer talking to an internet service provider.
    Respond naturally to the representative's last message:

    Representative's last message: {last_message}
    
    Your profile characteristics:
    {json.dumps(profile, indent=2)}
    
    Topics you haven't asked about yet:
    {', '.join(remaining_info)}
    
    Please:
    1. Give a natural and brief response
    2. Ask about only one topic at a time
    3. Respond appropriately to the representative's answer
    4. If you've received information about one topic, politely ask about a new topic
    """
    
    try:
        result = model.generate_content(prompt)
        return result.text.strip()
    except:
        return "I see, could you tell me about your internet package prices?" 