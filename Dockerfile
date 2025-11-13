# Dockerfile

FROM python:3.11-slim

WORKDIR /app

# Instala dependências do sistema necessárias para compilação (como gcc)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copia e instala as dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Garante que python-multipart está instalado (crucial para Form(...))
RUN pip install python-multipart

# Copia o código da sua aplicação e o frontend
COPY main.py .
COPY index.html .

# Define a porta que o FastAPI irá expor
EXPOSE 8000

# Comando para rodar a aplicação com Uvicorn (servidor ASGI)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]