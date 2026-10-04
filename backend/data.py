import json
from pathlib import Path


CLINIC_FILE = Path(__file__).parent.parent / "clinic.json"

clinic_data = None


def start_session():
    global clinic_data

    with open(CLINIC_FILE, "r", encoding="utf-8") as file:
        clinic_data = json.load(file)

    return clinic_data


def load_clinic():
    if clinic_data is None:
        start_session()

    return clinic_data