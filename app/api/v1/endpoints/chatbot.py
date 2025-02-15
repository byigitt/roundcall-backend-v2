from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.deps import get_current_user, get_db
from app.models.user import UserInDB, UserRole
from app.models.chatbot import ChatMessage, ChatSession, ChatResponse
from datetime import datetime, UTC
from typing import List, Dict
import google.generativeai as genai
from app.core.config import settings
import json
from bson import ObjectId

router = APIRouter()

# Happy Customer profili
HAPPY_CUSTOMER_PROFILE = {
    "profil": {
        "Duygusal Durum": "Olumlu, pozitif, neşeli",
        "Sabır Seviyesi": 8,
        "İkna Edilebilirlik": 8,
        "Konuşkanlık": 9,
        "Zaman Duyarlılığı": 3,
        "Teknik Bilgi": 6,
        "Memnuniyet Eşiği": 5
    },
    "başlangıç": "İyi günler! Komşum sizin kampanyanızdan bahsetti, memnun kalmış. Ben de fiber internet düşünüyorum."
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

    # Yeni bir sohbet oturumu oluştur
    session = {
        "traineeID": current_user.id,
        "characterType": character_type,
        "messages": [
            {
                "role": "assistant",
                "content": HAPPY_CUSTOMER_PROFILE["başlangıç"],
                "timestamp": datetime.now(UTC)
            }
        ],
        "createdAt": datetime.now(UTC),
        "updatedAt": datetime.now(UTC),
        "isActive": True,
        "collectedInfo": {
            "fiyat": False,
            "taahhut": False,
            "hiz": False,
            "kurulum": False,
            "cayma_bedeli": False
        }
    }

    result = await db.chatSessions.insert_one(session)
    session["id"] = str(result.inserted_id)
    
    return ChatSession(**session)

@router.post("/{session_id}/message", response_model=ChatResponse)
async def send_message(
    session_id: str,
    message: str,
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_db)
):
    # Oturumu kontrol et
    session = await db.chatSessions.find_one({"_id": ObjectId(session_id)})
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

    # Mesajı kaydet
    new_message = {
        "role": "user",
        "content": message,
        "timestamp": datetime.now(UTC)
    }
    
    # Model'i başlat
    model = initialize_model()
    
    # Mesajı analiz et
    analysis = analyze_agent_response(model, message, "\n".join([msg["content"] for msg in session["messages"]]))
    
    # Bilgi toplama durumunu güncelle
    info_analysis = analyze_response(model, message)
    collected_info = session.get("collectedInfo", {
        "fiyat": False,
        "taahhut": False,
        "hiz": False,
        "kurulum": False,
        "cayma_bedeli": False
    })
    
    for key in collected_info:
        if info_analysis.get(key, False):
            collected_info[key] = True

    # Chatbot yanıtını oluştur
    conversation_history = "\n".join([
        f"[{'Müşteri' if msg['role'] == 'assistant' else 'Temsilci'}]: {msg['content']}"
        for msg in session["messages"]
    ])
    bot_response = generate_agent_response(
        model, 
        conversation_history, 
        HAPPY_CUSTOMER_PROFILE["profil"],
        collected_info
    )

    # Chatbot yanıtını kaydet
    bot_message = {
        "role": "assistant",
        "content": bot_response,
        "timestamp": datetime.now(UTC)
    }

    # Veritabanını güncelle
    await db.chatSessions.update_one(
        {"_id": ObjectId(session_id)},
        {
            "$push": {"messages": {"$each": [new_message, bot_message]}},
            "$set": {
                "updatedAt": datetime.now(UTC),
                "collectedInfo": collected_info
            }
        }
    )

    return ChatResponse(
        message=bot_response,
        analysis=analysis,
        collectedInfo=collected_info
    )

@router.get("/sessions", response_model=List[ChatSession])
async def get_chat_sessions(
    current_user: UserInDB = Depends(get_current_user),
    db=Depends(get_db)
):
    sessions = await db.chatSessions.find({
        "traineeID": current_user.id
    }).to_list(length=None)
    
    return [ChatSession(**{**session, "id": str(session["_id"])}) for session in sessions]

# Happy Customer'dan alınan yardımcı fonksiyonları buraya ekleyin
def analyze_response(model, response):
    # happy_customer.py'dan kopyalanan fonksiyon
    pass

def analyze_agent_response(model, response, conversation_history):
    # happy_customer.py'dan kopyalanan fonksiyon
    pass

def generate_agent_response(model, conversation_history, profile, collected_info):
    # happy_customer.py'dan kopyalanan fonksiyon
    pass 