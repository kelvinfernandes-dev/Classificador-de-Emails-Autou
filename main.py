# main.py

import os
import json
import datetime
from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import FileResponse
from google import genai
from google.genai.errors import APIError

# --- Configurações ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)
app = FastAPI(title="Email Classifier AutoU")

HISTORY_FILE = "history.json" # Arquivo para persistência do histórico

# --- Funções de Histórico ---

def load_history():
    """Carrega o histórico de classificações do arquivo JSON."""
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            # Retorna as últimas 10 entradas, na ordem mais recente primeiro
            return json.load(f)[:10] 
    except (json.JSONDecodeError, FileNotFoundError):
        return []

def save_history(entry):
    """Adiciona uma nova entrada ao histórico e salva."""
    history = load_history()
    
    # Prepara a entrada com timestamp
    entry_with_time = {
        "timestamp": datetime.datetime.now().strftime("%H:%M:%S"),
        "date": datetime.datetime.now().strftime("%Y-%m-%d"),
        "input": entry.get("input", "N/A"),
        "classification": entry.get("classification", "ERRO"),
        "status": entry.get("status", "OK")
    }
    
    # Adiciona a entrada como a mais recente
    history.insert(0, entry_with_time) 
    
    # Mantém apenas as últimas 10 entradas
    history = history[:10] 
    
    try:
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=4)
    except IOError as e:
        print(f"ERRO ao salvar histórico: {e}")


# --- Rota para o frontend ---
@app.get("/")
async def read_index():
    return FileResponse("index.html")

# --- Rota para o Histórico (NOVA ROTA) ---
@app.get("/history")
async def get_history():
    """Retorna o histórico de classificações para o frontend."""
    return load_history()

# --- API Route para Classificação ---
@app.post("/classify")
async def classify_email(email_text: str = Form(...)):
    """
    Recebe o texto do e-mail e usa o modelo Gemini para classificar e sugerir a resposta.
    """
    if not email_text.strip():
        raise HTTPException(status_code=400, detail="O campo de e-mail não pode estar vazio.")
    
    # Prepara entrada básica para histórico
    history_entry = {"input": email_text[:50] + "...", "status": "ERRO API"}

    if not GEMINI_API_KEY:
        result = {
            "CLASSIFICACAO": "IMPRODUTIVO (Mocked)",
            "RESPOSTA_SUGERIDA": "Chave de API não configurada. A classificação foi simulada para teste.",
            "mocked": True
        }
        history_entry.update({"classification": "Mocked", "status": "OK"})
        save_history(history_entry)
        return result


    try:
        full_prompt = f"""
        Você é um assistente de IA sênior de uma empresa financeira.
        Sua tarefa é analisar o e-mail fornecido e executar duas ações:
        1. CLASSIFICAR: O e-mail em uma das três categorias EXATAS: 
           - 'Produtivo' (requer uma ação, suporte ou solução).
           - 'Improdutivo' (mensagem social, agradecimento, felicitação).
           - 'Spam' (e-mails não solicitados, phishing, promoções genéricas, conteúdo suspeito ou fraudulento).
        2. GERAR RESPOSTA: Gerar uma RESPOSTA_SUGERIDA curta (máximo 4 frases). Se a classificação for 'Spam', a resposta sugerida deve ser EXATAMENTE: 'Mover para lixeira e bloquear remetente.'

        Sua resposta DEVE ser um objeto JSON válido, sem texto extra, no formato EXATO:
        {{
            "CLASSIFICACAO": "[Produtivo, Improdutivo ou Spam]",
            "RESPOSTA_SUGERIDA": "[Sua sugestão de resposta ou instrução para Spam]"
        }}

        ---
        E-mail a classificar:
        {email_text}
        """
        
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=full_prompt
        )

        # LÓGICA DE PARSING
        try:
            raw_text = response.text.strip()
            if '```json' in raw_text:
                raw_text = raw_text.split('```json')[1].split('```')[0]
            elif '```' in raw_text:
                raw_text = raw_text.split('```')[1].split('```')[0]
                
            ai_output = json.loads(raw_text)
            
            if 'CLASSIFICACAO' not in ai_output:
                raise ValueError("JSON incompleto.")
            
            # Sucesso: Salva no histórico antes de retornar
            history_entry.update({"classification": ai_output["CLASSIFICACAO"], "status": "OK"})
            save_history(history_entry)
            
            return ai_output
            
        except (json.JSONDecodeError, ValueError) as e:
            # Erro de Parsing: Salva o erro no histórico
            history_entry.update({"classification": "Erro Parsing", "status": "FALHA"})
            save_history(history_entry)
            
            return {
                "CLASSIFICACAO": "Erro de IA",
                "RESPOSTA_SUGERIDA": "A IA não retornou um formato válido."
            }
            
    except APIError as e:
        # Erro de API: Salva o erro no histórico
        history_entry.update({"classification": "Erro API", "status": "FALHA"})
        save_history(history_entry)
        raise HTTPException(status_code=500, detail=f"Erro de comunicação com a API do Gemini: {str(e)}")
        
    except Exception as e:
        # Erro Geral: Salva o erro no histórico
        history_entry.update({"classification": "Erro Geral", "status": "FALHA"})
        save_history(history_entry)
        raise HTTPException(status_code=500, detail=f"Ocorreu um erro inesperado: {str(e)}")