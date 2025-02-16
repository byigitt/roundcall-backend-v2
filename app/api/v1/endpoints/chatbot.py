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
                "role": "customer",
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
    # Oturumu kontrol et
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

    # Temsilci (trainee) yanıtını kaydet
    agent_message = {
        "role": "agent",
        "content": message,
        "timestamp": datetime.now(UTC)
    }
    
    # Model'i başlat
    model = initialize_model()
    
    # Temsilci yanıtını analiz et
    conversation_history = "\n".join([
        f"{msg['content']}"
        for msg in session["messages"][-2:] if msg  # Sadece son 2 mesajı al
    ])
    
    analysis = analyze_agent_response(model, message, conversation_history)
    
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

    # Müşterinin bir sonraki yanıtını oluştur
    next_customer_message = generate_customer_response(
        model, 
        message,  # Sadece son mesajı gönder
        HAPPY_CUSTOMER_PROFILE["profil"],
        collected_info
    )

    # Müşteri yanıtını kaydet
    customer_message = {
        "role": "customer",
        "content": next_customer_message,
        "timestamp": datetime.now(UTC)
    }

    # Veritabanını güncelle
    await db[settings.DATABASE_NAME]["chatSessions"].update_one(
        {"_id": ObjectId(session_id)},
        {
            "$push": {"messages": {"$each": [agent_message, customer_message]}},
            "$set": {
                "updatedAt": datetime.now(UTC),
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
    """Kullanıcının yanıtını analiz eder ve hangi bilgilerin toplandığını belirler."""
    prompt = f"""
    Aşağıdaki müşteri yanıtını analiz et ve hangi bilgilerin sorulduğunu belirle:
    
    Yanıt: {response}
    
    Şu konularda bilgi var mı (True/False olarak döndür):
    - Fiyat bilgisi
    - Taahhüt süresi
    - İnternet hızı
    - Kurulum detayları
    - Cayma bedeli
    """
    
    result = model.generate_content(prompt)
    try:
        analysis = {
            "fiyat": "fiyat" in response.lower() or "tl" in response.lower() or "lira" in response.lower(),
            "taahhut": "taahhüt" in response.lower() or "süre" in response.lower(),
            "hiz": "hız" in response.lower() or "mbps" in response.lower(),
            "kurulum": "kurulum" in response.lower() or "montaj" in response.lower(),
            "cayma_bedeli": "cayma" in response.lower() or "iptal" in response.lower()
        }
        return analysis
    except:
        return {
            "fiyat": False,
            "taahhut": False,
            "hiz": False,
            "kurulum": False,
            "cayma_bedeli": False
        }

def analyze_agent_response(model, response, conversation_history):
    """Temsilcinin yanıtını analiz eder ve performans metriklerini hesaplar."""
    prompt = f"""
    Bir müşteri temsilcisi adayının yanıtını değerlendir.
    
    Konuşma Geçmişi:
    {conversation_history}
    
    Temsilci Yanıtı:
    {response}
    
    Aşağıdaki kriterlere göre 1-10 arası puan ver ve detaylı açıklama yap:
    
    1. Profesyonellik (1-10):
    - Uygun selamlama kullanımı
    - Nazik ve saygılı dil
    - Profesyonel kelime seçimi
    
    2. Empati (1-10):
    - Müşteriyi dinleme ve anlama
    - Müşterinin duygularını anlama
    - Uygun duygusal tepkiler
    
    3. Çözüm Odaklılık (1-10):
    - Müşterinin ihtiyaçlarını anlama
    - Doğru bilgileri verme
    - Uygun çözümler sunma
    
    4. İletişim Becerisi (1-10):
    - Açık ve anlaşılır ifadeler
    - Akıcı diyalog
    - İkna edici konuşma
    
    Her kriter için detaylı geri bildirim ver.
    """
    
    try:
        result = model.generate_content(prompt)
        return {
            "profesyonellik": 8,  # Bu değerler model tarafından belirlenecek
            "empati": 7,
            "cozum_odaklilik": 8,
            "iletisim": 7,
            "genel_puan": 7.5,
            "detayli_analiz": result.text
        }
    except:
        return {
            "profesyonellik": 5,
            "empati": 5,
            "cozum_odaklilik": 5,
            "iletisim": 5,
            "genel_puan": 5,
            "detayli_analiz": "Analiz yapılamadı"
        }

def generate_customer_response(model, last_message, profile, collected_info):
    """Müşterinin bir sonraki yanıtını/sorusunu oluşturur."""
    remaining_info = [
        key for key, value in collected_info.items() 
        if not value
    ]
    
    prompt = f"""
    Sen bir internet servis sağlayıcısıyla görüşen potansiyel bir müşterisin.
    Temsilcinin son mesajına doğal bir şekilde yanıt ver:

    Temsilcinin son mesajı: {last_message}
    
    Profil özelliklerin:
    {json.dumps(profile, indent=2, ensure_ascii=False)}
    
    Henüz sormadığın konular:
    {', '.join(remaining_info)}
    
    Lütfen:
    1. Doğal ve kısa bir yanıt ver
    2. Her seferinde sadece bir konu hakkında soru sor
    3. Temsilcinin cevabına uygun şekilde yanıt ver
    4. Eğer bir konuda bilgi aldıysan, yeni bir konu hakkında nazikçe soru sor
    """
    
    try:
        result = model.generate_content(prompt)
        return result.text.strip()
    except:
        return "Anlıyorum, peki internet paketlerinizin fiyatları nasıl?" 