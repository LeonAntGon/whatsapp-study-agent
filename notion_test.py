import os
import time
from dotenv import load_dotenv
from notion_client import Client

# 1. Cargar configuración desde el .env
load_dotenv()
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
PAGE_ID = os.getenv("NOTION_PAGE_ID")

# 2. Inicializar el cliente oficial de Notion
notion = Client(auth=NOTION_TOKEN)

def extract_text_from_notion(block_id, level=0):
    """
    Función recursiva que extrae texto de bloques y entra en subpáginas.
    'level' se usa para dar formato visual a la consola (identación).
    """
    indent = "  " * level
    # Algunos bloques de child_page no tienen título directamente accesible 
    # sin hacer una llamada extra, pero el ID siempre está.
    print(f"{indent}📂 Explorando bloque/página: {block_id}...")
    
    texto_acumulado = ""
    
    try:
        # Paginación básica: Notion devuelve hasta 100 bloques por vez.
        # Por ahora lo mantenemos simple, pero en ingeniería se usaría 'start_cursor'.
        response = notion.blocks.children.list(block_id=block_id)
        
        for block in response.get('results', []):
            block_type = block.get('type')
            
            # --- CASO 1: Bloques de texto comunes ---
            text_blocks = [
                'paragraph', 'heading_1', 'heading_2', 'heading_3', 
                'bulleted_list_item', 'numbered_list_item', 'to_do', 'quote'
            ]
            
            if block_type in text_blocks:
                rich_text = block[block_type].get('rich_text', [])
                for text_item in rich_text:
                    texto_acumulado += text_item.get('plain_text', '') + " "
                texto_acumulado += "\n"
            
            # --- CASO 2: Subpáginas (Recursividad) ---
            elif block_type == 'child_page':
                sub_page_title = block['child_page'].get('title', 'Sin Título')
                texto_acumulado += f"\n{'='*10} INICIO SUBPÁGINA: {sub_page_title} {'='*10}\n"
                
                # LLAMADA RECURSIVA: La función se llama a sí misma con el ID de la subpágina
                # Añadimos un pequeño delay para evitar el "Rate Limit" de la API de Notion
                time.sleep(0.1) 
                texto_acumulado += extract_text_from_notion(block['id'], level + 1)
                
                texto_acumulado += f"\n{'='*10} FIN SUBPÁGINA: {sub_page_title} {'='*10}\n"

        return texto_acumulado

    except Exception as e:
        print(f"{indent}❌ Error en bloque {block_id}: {e}")
        return ""

if __name__ == "__main__":
    print("🚀 Iniciando extracción recursiva de Notion...")
    
    if not NOTION_TOKEN or not PAGE_ID:
        print("❌ Error: Verifica que NOTION_TOKEN y NOTION_PAGE_ID estén en el .env")
    else:
        start_time = time.time()
        
        # Llamada inicial a la página raíz
        contenido_final = extract_text_from_notion(PAGE_ID)
        
        end_time = time.time()
        
        print("\n" + "#"*40)
        print("✅ EXTRACCIÓN COMPLETADA CON ÉXITO")
        print(f"⏱️ Tiempo tomado: {round(end_time - start_time, 2)} segundos")
        print("#"*40 + "\n")
        
        # Guardamos el resultado en un archivo txt para que puedas revisarlo
        with open("notion_content.txt", "w", encoding="utf-8") as f:
            f.write(contenido_final)
            
        print("📄 El contenido ha sido guardado en 'notion_content.txt'")
        # También imprimimos un pequeño preview en consola
        print("\n--- PREVIEW DEL CONTENIDO ---")
        print(contenido_final[:500] + "...")