from data import load_clinic
from datetime import datetime, timedelta

def lookup_patient(name=None, phone=None, dob=None):
    data = load_clinic()
    patients = data["patients"]

    matches = []

    for patient in patients:
        if name and name.lower() not in patient["name"].lower():
            continue
        if phone and patient["phone"] != phone:
            continue
        if dob and patient["dob"] != dob:
            continue

        matches.append(patient)

    if len(matches) == 0:
        return {"status": "not_found"}

    if len(matches) > 1:
        return {
            "status": "ambiguous",
            "candidates": matches
        }

    return {
        "status": "found",
        "patient": matches[0]
    }

def search_slots(doctor_id, date):
    data = load_clinic()

    doctor = next(
        (d for d in data["doctors"] if d["id"] == doctor_id),
        None
    )

    if not doctor:
        return {"status": "error", "message": "Doctor not found"}

    if date in doctor.get("leave_dates", []):
        return {"status": "no_slots", "slots": []}

    day = datetime.strptime(date, "%Y-%m-%d").strftime("%a")

    windows = [
        w for w in doctor["windows"]
        if w["day"] == day
    ]

    slots = []

    for window in windows:
        current = datetime.strptime(
            f"{date} {window['start']}", "%Y-%m-%d %H:%M"
        )
        finish = datetime.strptime(
            f"{date} {window['end']}", "%Y-%m-%d %H:%M"
        )

        while current < finish:
            slots.append(current.strftime("%Y-%m-%dT%H:%M"))
            current += timedelta(minutes=15)

    booked = {
        a["start"]
        for a in data["appointments"]
        if a["doctor_id"] == doctor_id
        and a["status"] == "booked"
        and a["start"].startswith(date)
    }

    available = [slot for slot in slots if slot not in booked]

    return {
        "status": "ok",
        "doctor_id": doctor_id,
        "date": date,
        "slots": available
    }

def book_appointment(patient_id, doctor_id, start):
    data = load_clinic()

    patient = next(
        (p for p in data["patients"] if p["id"] == patient_id),
        None
    )

    if not patient:
        return {"status": "error", "message": "Patient not found"}

    for appointment in data["appointments"]:
        if (
            appointment["doctor_id"] == doctor_id
            and appointment["start"] == start
            and appointment["status"] == "booked"
        ):
            return {
                "status": "error",
                "message": "Slot already booked"
            }

    appointment_id = f"ap_{len(data['appointments']) + 1:04d}"

    appointment = {
        "id": appointment_id,
        "patient_id": patient_id,
        "doctor_id": doctor_id,
        "start": start,
        "status": "booked"
    }

    data["appointments"].append(appointment)

    return {
        "status": "booked",
        "appointment_id": appointment_id,
        "patient_id": patient_id,
        "doctor_id": doctor_id,
        "start": start
    }

def reschedule_appointment(appointment_id, new_start):
    data = load_clinic()

    appointment = next(
        (a for a in data["appointments"] if a["id"] == appointment_id),
        None
    )

    if not appointment:
        return {"status": "error", "message": "Appointment not found"}

    if appointment["status"] != "booked":
        return {"status": "error", "message": "Appointment is not active"}

    for a in data["appointments"]:
        if (
            a["id"] != appointment_id
            and a["doctor_id"] == appointment["doctor_id"]
            and a["start"] == new_start
            and a["status"] == "booked"
        ):
            return {"status": "error", "message": "Slot already booked"}

    appointment["start"] = new_start

    return {
        "status": "rescheduled",
        "appointment_id": appointment_id,
        "patient_id": appointment["patient_id"],
        "doctor_id": appointment["doctor_id"],
        "start": new_start
    }


def cancel_appointment(appointment_id):
    data = load_clinic()

    appointment = next(
        (a for a in data["appointments"] if a["id"] == appointment_id),
        None
    )

    if not appointment:
        return {"status": "error", "message": "Appointment not found"}

    if appointment["status"] != "booked":
        return {"status": "error", "message": "Appointment is not active"}

    appointment["status"] = "cancelled"

    return {
        "status": "cancelled",
        "appointment_id": appointment_id,
        "patient_id": appointment["patient_id"]
    }

def escalate_to_human(reason, summary):
    return {
        "status": "escalated",
        "reason": reason,
        "summary": summary
    }