import yaml
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from typing import Dict, Any
from pydantic import BaseModel, Field, validator

class EasyModeConfig(BaseModel):
    """Validiert die 5 essenziellen User-Eingaben"""
    
    environment: str = Field(..., pattern="^(DEV|TST|PRD)$")
    sap_sid: str = Field(..., pattern="^[A-Z0-9]{3}$")
    sap_product_id: str = Field(..., pattern="^(S4HANA2023|S4HANA2022|SAP_NETWEAVER_750)$")
    location: str = Field(..., pattern="^(westeurope|northeurope|germanywestcentral)$")
    sizing: str = Field(..., pattern="^(small|medium|large)$")

def load_defaults() -> Dict[str, Any]:
    """Lädt alle Default-Werte aus YAML (Pfad ist im Container /app/templates)"""
    defaults_path = Path("/app/templates/easy_defaults.yaml")
    
    if not defaults_path.exists():
        raise FileNotFoundError(f"Datei nicht gefunden: {defaults_path}. Verfügbare Dateien: {list(defaults_path.parent.glob('*'))}")
    
    return yaml.safe_load(defaults_path.read_text())

def get_sizing_config(sizing: str) -> Dict[str, str]:
    """VM-Größen basierend auf Sizing-Profil"""
    sizings = {
        "small": {
            "app_tier_sku": "Standard_D4s_v3",
            "database_tier_sku": "Standard_E16s_v3",
            "scs_tier_sku": "Standard_D2s_v3",
        },
        "medium": {
            "app_tier_sku": "Standard_D8s_v3",
            "database_tier_sku": "Standard_E32s_v3",
            "scs_tier_sku": "Standard_D4s_v3",
        },
        "large": {
            "app_tier_sku": "Standard_D16s_v3",
            "database_tier_sku": "Standard_E64s_v3",
            "scs_tier_sku": "Standard_D8s_v3",
        }
    }
    return sizings[sizing]

def build_config(user_input: Dict[str, str]) -> Dict[str, Any]:
    """
    Baut komplette TFVARS-Konfiguration aus 5 User-Werten
    
    Beispiel-Input:
    {
        "environment": "DEV",
        "sap_sid": "X01",
        "sap_product_id": "S4HANA2023",
        "location": "westeurope",
        "sizing": "small"
    }
    """
    # 1. Lade Defaults
    config = load_defaults()
    
    # 2. Überschreibe mit User-Werten
    config.update({
        "workload_environment": user_input["environment"],
        "sap_sid": user_input["sap_sid"],
        "sap_product_id": user_input["sap_product_id"],
        "location": user_input["location"],
        "_sizing_profile": user_input["sizing"],  # Meta-Info
        "_timestamp": "2025-01-01T12:00:00Z"  # Wird später dynamisch
    })
    
    # 3. Ableitete Werte
    config["sap_system_name"] = user_input["sap_sid"]
    config["database_sid"] = user_input["sap_sid"] + "DB"
    config["workload_zone"] = f"{user_input['environment']}-WEEU-{user_input['sap_sid']}"
    config["network_logical_name"] = user_input["sap_sid"]
    
    # 4. Sizing anwenden
    sizing_config = get_sizing_config(user_input["sizing"])
    config.update(sizing_config)
    
    # 5. Validiere
    EasyModeConfig(**user_input)
    
    return config

# Beispiel-Test
if __name__ == "__main__":
    user = {
        "environment": "DEV",
        "sap_sid": "X01",
        "sap_product_id": "S4HANA2023",
        "location": "westeurope",
        "sizing": "small"
    }
    cfg = build_config(user)
    print(f"✓ Konfiguration erzeugt: {cfg['sap_sid']}")
    print(f"✓ VM Size DB: {cfg['database_tier_sku']}")


def generate_tfvars_string(config: dict) -> str:
    """
    Generiert TFVARS-Inhalt mit Jinja2 Template
    """
    # ✅ Wichtig: Pfad ist im Docker Container /app/templates
    templates_dir = Path("/app/templates")
    
    if not templates_dir.exists():
        raise FileNotFoundError(f"Template-Verzeichnis nicht gefunden: {templates_dir}")
    
    # Prüfe ob Datei existiert
    template_file = templates_dir / "sap.tfvars.j2"
    if not template_file.exists():
        raise FileNotFoundError(f"Template-Datei nicht gefunden: {template_file}. "
                              f"Verfügbare Dateien: {list(templates_dir.glob('*.j2'))}")
    
    env = Environment(loader=FileSystemLoader(templates_dir))
    
    try:
        template = env.get_template("sap.tfvars.j2")
        return template.render(config=config)
    except Exception as e:
        raise RuntimeError(f"Fehler beim Rendern des Templates 'sap.tfvars.j2': {e}")