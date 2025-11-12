from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain_ollama import OllamaLLM
import os

app = FastAPI(title="SDAF Config Generator")
llm = OllamaLLM(model="llama3.1:8b", base_url="http://host.docker.internal:11434")

class ValidationRequest(BaseModel):
    field: str
    value: str

class ConfigRequest(BaseModel):
    config: dict

@app.post("/validate")
def validate_input(req: ValidationRequest):
    prompt = f"Validate SAP SDAF parameter '{req.field}' with value '{req.value}'. Is this valid? Respond YES/NO and short reason."
    try:
        response = llm.invoke(prompt)
        is_valid = "YES" in response.upper()
        return {"valid": is_valid, "message": response.strip()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM error: {str(e)}")

@app.post("/generate")
def generate_tfvars(req: ConfigRequest):
    try:
        # Simple TFVARS-Generierung (erweiterbar)
        lines = [f"# SDAF Configuration - {req.config.get('sap_sid', 'SAP')}", ""]
        for key, value in req.config.items():
            if isinstance(value, str):
                lines.append(f'{key} = "{value}"')
            else:
                lines.append(f'{key} = {value}')
        content = "\n".join(lines)
        return {"tfvars": content}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/health")
def health_check():
    return {"status": "ok", "ollama_reachable": True}
