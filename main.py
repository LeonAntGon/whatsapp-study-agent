import os
import httpx
import asyncio
from fastapi import FastAPI, Request, Query, BackgroundTasks
from fastapi.responses import PlainTextResponse
from dotenv import load_dotenv
from ai_brain import get_ai_response

load_dotenv()

app = FastAPI()

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
VERSION = "v25.0"

async def send_whatsapp_message(to: str, text: str):
    url = f"https://graph.facebook.com/{VERSION}/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text}
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, headers=headers, json=data)
            if response.status_code == 200:
                print(f"✅ Respuesta enviada con éxito a {to}")
            else:
                print(f"❌ Error de Meta {response.status_code}: {response.text}")
        except Exception as e:
            print(f"❌ Error interno enviando a WhatsApp: {e}")


def process_ai_and_respond(user_phone: str, user_text: str):
    print(f"Consultando a (OpenRouter) para {user_phone}...")
    
    respuesta_ia = get_ai_response(user_text)
    
    print("\n" + "=" * 40)
    print(f"[RESPUESTA GENERADA POR IA]:\n{respuesta_ia}")
    print("=" * 40 + "\n")
    
    asyncio.run(send_whatsapp_message(user_phone, respuesta_ia))
    
@app.get("/webhook")
async def verify_webhook(
    mode: str = Query(None, alias="hub.mode"),
    token: str = Query(None, alias="hub.verify_token"),
    challenge: str = Query(None, alias="hub.challenge")
):
    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("✅ Webhook verificado correctamente por Meta.")
        return PlainTextResponse(content=challenge)
    return {"error": "Token de verificación inválido"}

@app.post("/webhook")
async def receive_message(request: Request, background_tasks: BackgroundTasks):
    body = await request.json()
    
    try:
        entry = body['entry'][0]
        changes = entry['changes'][0]
        value = changes['value']
        
        if "messages" in value:
            message = value['messages'][0]
    
            raw_phone = message['from']
            user_text = message['text']['body']
            
            # --- FIX ARGENTINA 🇦🇷 ---
            if raw_phone.startswith("549"):
                user_phone = "54" + raw_phone[3:]
            else:
                user_phone = raw_phone
            
            print(f"📩 Recibido de {raw_phone} -> Respondiendo a: {user_phone}")
            print(f"📝 Mensaje: {user_text}")
            background_tasks.add_task(process_ai_and_respond, user_phone, user_text)

        return {"status": "ok"}
    except Exception:
        return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    # Render.com asigna un puerto dinámico a través de la variable de entorno PORT
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)