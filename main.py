import os
import json
import datetime
from fastapi import FastAPI, Form, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from google import genai
from google.genai.errors import APIError
from typing import Union
from io import BytesIO

# --- Configurações ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)
app = FastAPI(title="Email Classifier AutoU")

HISTORY_FILE = "history.json" 

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

# --- Rota para o Histórico ---
@app.get("/history")
async def get_history():
    """Retorna o histórico de classificações para o frontend."""
    return load_history()

# --- API Route para Classificação ---
@app.post("/classify")
async def classify_email(
    email_text: Union[str, None] = Form(None), 
    email_file: Union[UploadFile, None] = File(None) 
):
    
    email_content = ""
    
    # 1. PROCESSAMENTO DE ARQUIVO
    if email_file and email_file.filename:
        allowed_extensions = ["txt", "pdf"]
        file_extension = email_file.filename.split('.')[-1].lower()
        
        if file_extension not in allowed_extensions:
            raise HTTPException(status_code=400, detail=f"Extensão de arquivo não suportada: .{file_extension}. Use .txt ou .pdf.")
        
        try:
            # Tenta ler o conteúdo como texto (funciona para .txt)
            content_bytes = await email_file.read()
            email_content = content_bytes.decode("utf-8")
            
            # CORREÇÃO CRÍTICA: Fechamento explícito do stream para liberar recursos.
            # Se o FastAPI ou o uvicorn estiverem mantendo o stream aberto, isso pode 
            # interferir em requisições subsequentes à API externa.
            await email_file.close() 

        except Exception:
             raise HTTPException(status_code=400, detail="Erro ao ler o conteúdo do arquivo. Certifique-se de que é um texto válido (.txt). O suporte a PDF binário é limitado nesta versão.")

    # 2. PROCESSAMENTO DE TEXTO DIRETO
    elif email_text and email_text.strip():
        email_content = email_text
        
    else:
        raise HTTPException(status_code=400, detail="Forneça o texto do e-mail ou faça o upload de um arquivo (.txt ou .pdf).")

    if not email_content.strip():
        raise HTTPException(status_code=400, detail="O e-mail está vazio após o processamento.")

    # Prepara entrada básica para histórico
    history_entry = {"input": email_content[:50] + "...", "status": "ERRO API"}

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
        {email_content}
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