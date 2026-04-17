import os
from dotenv import load_dotenv
from openai import OpenAI
from notion_client import Client

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_PAGE_ID = os.getenv("NOTION_PAGE_ID")

client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=OPENROUTER_API_KEY)
notion = Client(auth=NOTION_TOKEN)

def get_notion_knowledge():
    """Extrae el texto de todos los bloques de la página de Notion"""
    print("Leyendo Notion...")
    try:
        response = notion.blocks.children.list(block_id=NOTION_PAGE_ID)
        full_text = ""
        
        for block in response["results"]:
            block_type = block["type"]
            if "rich_text" in block[block_type]:
                parts = block[block_type]["rich_text"]
                for p in parts:
                    full_text += p["plain_text"] + " "
                full_text += "\n"
        
        return full_text
    except Exception as e:
        print(f"❌❌❌Error leyendo Notion: {e}")
        return ""

def get_ai_response(user_message):
    knowledge_base = get_notion_knowledge()
    
    if not knowledge_base:
        return "Lo siento, no pude acceder a mi base de conocimientos en Notion."

    system_prompt = f"""
    Eres un asistente educativo experto para WhatsApp, así que ajusta tu escritura para ser claro y útil en WhatsApp.
    REGLA: Responde basándote ÚNICAMENTE en estos apuntes de Notion:
    
    === APUNTES DE NOTION ===
    {knowledge_base}
    =========================
    """

    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b:free",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"❌❌❌Error en la IA: {e}")
        return "Error técnico en la IA."