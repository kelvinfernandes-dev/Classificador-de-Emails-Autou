# Classificador de E-mails com Gemini AI: Automação para Setor Financeiro

Este projeto é uma Solução Digital desenvolvida para o desafio da AutoU, visando automatizar a leitura e classificação de um alto volume de e-mails em um contexto de setor financeiro, liberando a equipe de suporte de tarefas manuais.

A solução utiliza Inteligência Artificial (Google Gemini) para classificar o teor de um e-mail e gerar respostas sugeridas em tempo real.

## Destaques e Funcionalidades Adicionais

Este projeto ultrapassa os requisitos básicos do desafio (Produtivo e Improdutivo) com as seguintes implementações:

1.  **Suporte à Categoria "Spam" (Segurança):** O sistema classifica e-mails suspeitos, fraudulentos ou promocionais como **SPAM**. Para essa categoria, ele sugere uma **Ação Automática de Segurança**: "Mover para lixeira e bloquear remetente."
2.  **Histórico de Classificações (UX/Persistência):** Implementa um painel lateral (`Últimas Classificações`) que armazena as últimas 10 análises, oferecendo transparência e usabilidade ao usuário.
3.  **Ambiente Containerizado:** Toda a aplicação é empacotada em **Docker**, garantindo portabilidade e um *deploy* consistente em qualquer plataforma de nuvem (como Render ou Google Cloud Run).

## Categorias Implementadas

| Categoria | Propósito | Resposta Sugerida |
| :--- | :--- | :--- |
| **Produtivo** | Requer ação, suporte técnico ou solução. | Resposta específica e relevante para o caso. |
| **Improdutivo** | Mensagens sociais, felicitações ou sem ação imediata. | Resposta educada de agradecimento/dispensa. |
| **Spam (Adicional)** | Phishing, fraude, promoções genéricas, conteúdo suspeito. | "Mover para lixeira e bloquear remetente." |

## Stack Tecnológica

| Componente | Tecnologia | Função |
| :--- | :--- | :--- |
| **Inteligência Artificial** | **Google Gemini API** (`gemini-2.0-flash`) | Classificação e Geração de Resposta via Prompt Engineering. |
| **Backend/API** | **FastAPI** (Python) | Servidor robusto para gerenciar requisições e a lógica de classificação. |
| **Frontend/UX** | **HTML, CSS, JavaScript** | Interface web com cores dinâmicas para cada categoria e painel de histórico. |
| **Containerização** | **Docker** | Empacotamento para *deploy* na nuvem. |

---

## Como Executar a Aplicação Localmente (Docker)

Siga os passos abaixo para rodar a aplicação em sua máquina:

### Pré-requisitos
* **Docker** instalado e em execução.
* Uma chave válida da **Google Gemini API**.

### 1. Build da Imagem Docker

Navegue até o diretório raiz do projeto (onde está o `Dockerfile`) e execute o comando para construir a imagem através do seu terminal:

docker build -t email-classifier-autou .

### 2. Execução do Container

Execute o container mapeando a porta 8000 e substituindo SUA_CHAVE_GEMINI_API_AQUI pela sua chave real:

docker run -p 8000:8000 -e GEMINI_API_KEY="SUA_CHAVE_GEMINI_API_AQUI" --name email-classifier-final-run email-classifier-autou


