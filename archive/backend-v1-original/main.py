from chat_agent_simple import app  # Importiere die FastAPI-App aus chat_agent.py

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)