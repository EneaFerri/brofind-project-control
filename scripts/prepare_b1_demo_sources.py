from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "demo" / "b1" / "assets"
TARGET = ROOT / "data_sources" / "DEMO-B1-001"

FILES = {
    "Galileo": "DEMO-B1-001_control.xlsx",
    "Documenti": "DEMO-B1-001_contract.pdf",
    "Outlook": "DEMO-B1-001_payment_followup.eml",
}

for folder, name in FILES.items():
    destination = TARGET / folder
    destination.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ASSETS / name, destination / name)

print(f"Fonti demo predisposte in: {TARGET}")
for folder, name in FILES.items():
    print(f"- {folder}: {name}")
