"""
V2 Helper Functions - Portiert nach V3
=======================================

Funktionen aus V2 die in V3 benötigt werden:
- generate_sdaf_filename()
- generate_confirmation_summary()
- generate_final_summary()
"""

from typing import Dict, Any


def get_region_code(location: str) -> str:
    """Get 4-letter region code from Azure location"""
    region_codes = {
        "westeurope": "WEEU",
        "northeurope": "NOEU",
        "germanywestcentral": "GEWC",
        "germanycentral": "GEC",
        "eastus": "EAUS",
        "eastus2": "EAU2",
        "westus": "WEUS",
        "westus2": "WEU2",
        "centralus": "CEUS",
        "southcentralus": "SCUS",
        "northcentralus": "NCUS",
        "ukwest": "UKWE",
        "uksouth": "UKSO",
        "francecentral": "FRCE",
        "francesouth": "FRSO",
        "switzerlandnorth": "SWNO",
        "switzerlandwest": "SWWE",
        "norwayeast": "NOEA",
        "norwaywest": "NOWE",
        "swedencentral": "SWCE",
        "brazilsouth": "BRSO",
        "canadacentral": "CACE",
        "canadaeast": "CAEA",
        "australiaeast": "AUEA",
        "australiasoutheast": "AUSE",
        "australiacentral": "AUCE",
        "japaneast": "JAEA",
        "japanwest": "JAWE",
        "southeastasia": "SOEA",
        "eastasia": "EAAS",
        "centralindia": "CEIN",
        "southindia": "SOIN",
        "westindia": "WEIN",
        "koreacentral": "KOCE",
        "koreasouth": "KOSO",
        "southafricanorth": "SANO",
        "southafricawest": "SAWE",
        "uaenorth": "UANO",
        "uaecentral": "UACE",
    }

    # Normalize location (lowercase, remove spaces)
    location_normalized = location.lower().replace(" ", "").replace("-", "")

    return region_codes.get(location_normalized, location[:4].upper())


def generate_sdaf_filename(user_data: Dict[str, Any]) -> str:
    """
    Generate SDAF-compliant filename: ENV-LOCATION-NETWORK-SID.tfvars

    Examples:
    - PRD-WEEU-SAP01-X00.tfvars
    - DEV-NOEU-SAP02-P01.tfvars
    """
    env = user_data.get("environment", "DEV").upper()[:5]
    location = user_data.get("location", "westeurope")
    region_code = get_region_code(location)
    network = user_data.get("network_logical_name", "SAP01").upper()[:7]
    sid = user_data.get("sid", "X00").upper()

    return f"{env}-{region_code}-{network}-{sid}.tfvars"


def generate_confirmation_summary(user_data: Dict[str, Any]) -> str:
    """Generate summary for user confirmation BEFORE generating tfvars"""

    # Build server counts
    db_count = user_data.get("database_server_count", 1)
    scs_count = user_data.get("scs_server_count", 1)
    app_count = user_data.get("application_server_count", 0)

    # HA indicators
    ha_db = "✓ Ja" if user_data.get("database_high_availability") else "✗ Nein"
    ha_scs = "✓ Ja" if user_data.get("scs_high_availability") else "✗ Nein"

    # Generate filename preview
    filename = generate_sdaf_filename(user_data)

    summary = f"""## 📋 Bitte überprüfe deine Konfiguration

Ich habe alle Informationen gesammelt. Hier ist die Zusammenfassung:

### 🌍 Umgebung
| Parameter | Wert |
|-----------|------|
| **Environment** | {user_data.get('environment', 'N/A')} |
| **Azure Region** | {user_data.get('location', 'N/A')} |
| **Netzwerkname** | {user_data.get('network_logical_name', 'N/A')} |

### 💾 SAP System
| Parameter | Wert |
|-----------|------|
| **Application SID** | {user_data.get('sid', 'N/A')} |
| **Database SID** | {user_data.get('database_sid', 'N/A')} |
| **Database Platform** | {user_data.get('database_platform', 'N/A')} |
| **Database Size** | {user_data.get('database_size', 'N/A')} |

### 🏗️ Architektur
| Komponente | Anzahl | High Availability |
|------------|--------|-------------------|
| **Database Server** | {db_count} | {ha_db} |
| **Central Services** | {scs_count} | {ha_scs} |
| **Application Server** | {app_count} | - |
| **Typ** | {user_data.get('architecture_type', 'standalone').capitalize()} | - |

### 🌐 Netzwerk & OS
| Parameter | Wert |
|-----------|------|
| **Netzwerk-Typ** | {user_data.get('network_type', 'greenfield').capitalize()} |
| **Betriebssystem** | {user_data.get('os_publisher', 'SUSE')} {user_data.get('os_offer', 'sles-sap-15-sp5')} |

### 📁 Dateiname
Die generierte Datei wird heißen: **`{filename}`**

---

## ✅ Ist alles korrekt?

Antworte mit:
- **"Ja"** oder **"Bestätigen"** → Download wird freigegeben
- **"Nein"** oder **"Ändern"** → Du kannst Werte korrigieren

Was sagst du? 🤔
"""

    return summary


def generate_final_summary(user_data: Dict[str, Any]) -> str:
    """Generate final summary AFTER confirmation with download link"""

    # Build server counts
    db_count = user_data.get("database_server_count", 1)
    scs_count = user_data.get("scs_server_count", 1)
    app_count = user_data.get("application_server_count", 0)

    # HA indicator
    ha_db = "✓" if user_data.get("database_high_availability") else "✗"
    ha_scs = "✓" if user_data.get("scs_high_availability") else "✗"

    # Generate SDAF filename
    filename = generate_sdaf_filename(user_data)

    summary = f"""## ✅ Konfiguration abgeschlossen!

Deine SAP Deployment Konfiguration ist fertig! 🎉

### 📋 Zusammenfassung
| Parameter | Wert |
|-----------|-------|
| **Environment** | {user_data.get('environment', 'N/A')} |
| **Azure Region** | {user_data.get('location', 'N/A')} |
| **Network Name** | {user_data.get('network_logical_name', 'N/A')} |

### 🖥️ SAP System
| Parameter | Wert |
|-----------|-------|
| **Application SID** | {user_data.get('sid', 'N/A')} |
| **Database SID** | {user_data.get('database_sid', 'N/A')} |
| **Database Platform** | {user_data.get('database_platform', 'N/A')} |
| **Database Size** | {user_data.get('database_size', 'N/A')} |

### 🏗️ Architektur
| Komponente | Anzahl | High Availability |
|-----------|-------|-------------------|
| **Database Servers** | {db_count} | {ha_db} |
| **Central Services (SCS)** | {scs_count} | {ha_scs} |
| **Application Servers** | {app_count} | - |
| **Deployment Type** | {user_data.get('architecture_type', 'standalone').capitalize()} | - |

### 🌐 Netzwerk & OS
| Parameter | Wert |
|-----------|-------|
| **Network Type** | {user_data.get('network_type', 'greenfield').capitalize()} |
| **Operating System** | {user_data.get('os_publisher', 'SUSE')} {user_data.get('os_offer', 'sles-sap-15-sp5')} |

---

### 📥 Download
Deine **SDAF-konforme tfvars Datei** ist bereit: **`{filename}`**

Nutze den Download-Button unten um deine Konfigurationsdatei herunterzuladen!

💡 *Diese Datei enthält 180+ vorkonfigurierte SDAF Parameter mit Best-Practice Defaults.*
"""

    return summary
