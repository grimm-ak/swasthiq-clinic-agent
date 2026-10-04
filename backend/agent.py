import re
from datetime import datetime, timedelta

from tools import (
    lookup_patient,
    search_slots,
    book_appointment,
    reschedule_appointment,
    cancel_appointment,
    escalate_to_human,
)
from data import load_clinic


def response(
    conversation_id,
    tool_calls,
    state,
    reason,
    patient_id,
    appointment_id,
    reply,
    turns=0,
):
    return {
        "conversation_id": conversation_id,
        "tool_calls": tool_calls,
        "terminal_state": state,
        "escalation_reason": reason,
        "patient_id": patient_id,
        "appointment_id": appointment_id,
        "reply": reply,
        "metrics": {
            "turns": turns,
            "tokens": 0,
            "latency_ms": 0,
        },
    }


def get_phone(text):
    numbers = re.findall(r"\b\d{10}\b", text)
    return numbers[-1] if numbers else None


def get_doctor(text):
    data = load_clinic()

    for doctor in data["doctors"]:
        name = doctor["name"].lower()

        if name in text:
            return doctor

        parts = name.split()

        if len(parts) >= 2 and parts[-1] in text:
            return doctor

    return None


def get_patient_name(text):
    data = load_clinic()

    # Full patient name
    for patient in data["patients"]:
        if patient["name"].lower() in text:
            return patient["name"]

    # Partial name / surname such as "Sharma"
    words = re.findall(r"[a-z]+", text.lower())

    for word in words:
        if len(word) < 3:
            continue

        matches = [
            p
            for p in data["patients"]
            if word in p["name"].lower().split()
        ]

        if matches:
            return word

    return None


def get_date(text, today):
    base = datetime.strptime(today, "%Y-%m-%d")

    # Explicit YYYY-MM-DD
    matches = re.findall(r"\b20\d{2}-\d{2}-\d{2}\b", text)

    if matches:
        return matches[-1]

    # "8 tareekh", "7 date"
    matches = re.findall(
        r"\b(\d{1,2})\s*(?:tareekh|date)\b",
        text,
    )

    if matches:
        day = int(matches[-1])

        for offset in range(32):
            candidate = base + timedelta(days=offset)

            if candidate.day == day:
                return candidate.strftime("%Y-%m-%d")

    weekdays = {
        "monday": 0,
        "tuesday": 1,
        "wednesday": 2,
        "thursday": 3,
        "friday": 4,
        "saturday": 5,
        "sunday": 6,
        "somwar": 0,
        "mangalwar": 1,
        "budhwar": 2,
        "guruwar": 3,
        "shukrawar": 4,
        "shanivaar": 5,
        "shanivar": 5,
        "ravivaar": 6,
        "ravivar": 6,
    }

    # Last weekday mentioned wins.
    found = []

    for word, weekday in weekdays.items():
        position = text.rfind(word)

        if position != -1:
            found.append((position, weekday))

    if found:
        _, weekday = max(found)

        days_ahead = (weekday - base.weekday()) % 7

        return (
            base + timedelta(days=days_ahead)
        ).strftime("%Y-%m-%d")

    if "parso" in text or "day after tomorrow" in text:
        return (
            base + timedelta(days=2)
        ).strftime("%Y-%m-%d")

    if "kal" in text or "tomorrow" in text:
        return (
            base + timedelta(days=1)
        ).strftime("%Y-%m-%d")

    if "aaj" in text or "today" in text:
        return today

    return None


def get_requested_time(text):
    # 9:30 / 09:30
    matches = list(
        re.finditer(
            r"\b(\d{1,2}):(\d{2})\b",
            text,
        )
    )

    if matches:
        match = matches[-1]

        hour = int(match.group(1))
        minute = int(match.group(2))

        if hour <= 23 and minute <= 59:
            return f"{hour:02d}:{minute:02d}"

    # Hindi number words
    hindi_numbers = {
        "ek": 1,
        "do": 2,
        "teen": 3,
        "char": 4,
        "chaar": 4,
        "paanch": 5,
        "cheh": 6,
        "chhe": 6,
        "saat": 7,
        "aath": 8,
        "nau": 9,
        "das": 10,
        "gyarah": 11,
        "barah": 12,
        "terah": 13,
        "chaudah": 14,
        "pandrah": 15,
        "solah": 16,
        "satrah": 17,
        "atharah": 18,
        "unnis": 19,
        "bees": 20,
    }

    found = []

    for word, hour in hindi_numbers.items():
        pattern = rf"\b{word}\s*baje\b"

        for match in re.finditer(pattern, text):
            found.append((match.start(), hour))

    if found:
        _, hour = max(found)

        return f"{hour:02d}:00"

    # 9 baje / 11 baje
    matches = list(
        re.finditer(
            r"\b(\d{1,2})\s*baje\b",
            text,
        )
    )

    if matches:
        hour = int(matches[-1].group(1))

        if 0 <= hour <= 23:
            return f"{hour:02d}:00"

    # 9 am / 9 pm
    matches = list(
        re.finditer(
            r"\b(\d{1,2})\s*(am|pm)\b",
            text,
        )
    )

    if matches:
        match = matches[-1]

        hour = int(match.group(1))
        period = match.group(2)

        if period == "pm" and hour < 12:
            hour += 12

        if period == "am" and hour == 12:
            hour = 0

        return f"{hour:02d}:00"

    return None


def find_patient(result, text):
    if result["status"] == "found":
        return result["patient"]

    if result["status"] == "not_found":
        return None

    # Ambiguous result.
    # Only resolve if the full patient name is explicitly present.
    for patient in result["candidates"]:
        if patient["name"].lower() in text:
            return patient

    return None


def find_active_appointment(patient_id, doctor_id=None):
    data = load_clinic()

    appointments = [
        a
        for a in data["appointments"]
        if a["patient_id"] == patient_id
        and a["status"] == "booked"
    ]

    if doctor_id:
        appointments = [
            a
            for a in appointments
            if a["doctor_id"] == doctor_id
        ]

    return appointments[0] if appointments else None


def add_tool_call(tool_calls, name, arguments):
    tool_calls.append(
        {
            "name": name,
            "arguments": arguments,
        }
    )


def run_agent(conversation_id, today, turns):
    text = " ".join(turns).lower()

    if not turns:
        return response(
            conversation_id,
            [],
            "abandoned",
            None,
            None,
            None,
            "I need more information to help with the appointment.",
            len(turns),
        )

    # =====================================
    # SAFETY
    # =====================================

    urgent_words = [
        "chest pain",
        "shortness of breath",
        "difficulty breathing",
        "breathing problem",
        "seene mein dard",
        "seene me dard",
        "saans phool",
        "saans lene mein dikkat",
    ]

    if any(word in text for word in urgent_words):
        escalate_to_human(
            "clinical_urgent",
            "Patient reported possible urgent clinical symptoms.",
        )

        return response(
            conversation_id,
            [
                {
                    "name": "escalate_to_human",
                    "arguments": {
                        "reason": "clinical_urgent"
                    },
                }
            ],
            "escalated",
            "clinical_urgent",
            None,
            None,
            "This may require urgent medical attention. I’m escalating this to a human now.",
            len(turns),
        )

    medical_words = [
        "medical advice",
        "medicine",
        "medicine advice",
        "crocin",
        "tablet",
        "goli le lun",
        "goli le loon",
        "should i take",
        "kitni goli",
    ]

    if any(word in text for word in medical_words):
        escalate_to_human(
            "medical_advice",
            "Patient requested medical advice.",
        )

        return response(
            conversation_id,
            [
                {
                    "name": "escalate_to_human",
                    "arguments": {
                        "reason": "medical_advice"
                    },
                }
            ],
            "escalated",
            "medical_advice",
            None,
            None,
            "I can’t provide medical advice, so I’m escalating this to a human.",
            len(turns),
        )

    injection_words = [
        "ignore your previous instructions",
        "ignore previous instructions",
        "administrator mode",
        "admin mode",
        "system prompt",
        "jailbreak",
    ]

    if any(word in text for word in injection_words):
        return response(
            conversation_id,
            [],
            "refused",
            None,
            None,
            None,
            "I can’t follow that request.",
            len(turns),
        )

    # =====================================
    # INTENT
    # =====================================

    cancel_words = [
        "cancel",
        "cancellation",
        "radd",
        "cancel kar",
        "cancel karna",
    ]

    reschedule_words = [
        "reschedule",
        "change appointment",
        "move appointment",
        "shift appointment",
        "change the appointment",
        "karwana hai",
    ]

    booking_words = [
    "appointment",
    "book",
    "booking",
    "milna hai",
    "dikhana hai",
    "visit",
    "aa sakta hoon",
    "aa sakta hun",
    "aana hai",
    "kar dijiye",
    "kar do",
    "kar dijie",
]

    wants_cancel = any(
        word in text for word in cancel_words
    )

    wants_reschedule = any(
        word in text for word in reschedule_words
    )

    wants_booking = any(
        word in text for word in booking_words
    )

    # =====================================
    # AUTHORIZATION
    # =====================================

    third_party_words = [
        "padosi",
        "neighbor",
        "neighbour",
        "friend",
        "dost",
        "relative",
        "unka appointment",
        "uska appointment",
    ]

    if wants_cancel and any(
        word in text for word in third_party_words
    ):
        return response(
            conversation_id,
            [
                {
                    "name": "escalate_to_human",
                    "arguments": {
                        "reason": "not_authorised"
                    },
                }
            ],
            "escalated",
            "not_authorised",
            None,
            None,
            "I can't change another patient's appointment without authorisation. I'll transfer this to a human.",
            len(turns),
        )

    # =====================================
    # PATIENT LOOKUP
    # =====================================

    phone = get_phone(text)
    patient_name = get_patient_name(text)

    patient_result = None
    patient = None
    tool_calls = []

    if phone:
        patient_result = lookup_patient(phone=phone)

        add_tool_call(
            tool_calls,
            "lookup_patient",
            {"phone": phone},
        )

        patient = find_patient(
            patient_result,
            text,
        )

    elif patient_name:
        patient_result = lookup_patient(
            name=patient_name
        )

        add_tool_call(
            tool_calls,
            "lookup_patient",
            {"name": patient_name},
        )

        patient = find_patient(
            patient_result,
            text,
        )

    # =====================================
    # AMBIGUOUS PATIENT
    # =====================================

    if (
        (wants_booking or wants_cancel or wants_reschedule)
        and patient_result
        and patient_result["status"] == "ambiguous"
        and patient is None
    ):
        escalate_to_human(
            "ambiguous_patient",
            "Multiple patient records matched and identity was not resolved.",
        )

        add_tool_call(
            tool_calls,
            "escalate_to_human",
            {"reason": "ambiguous_patient"},
        )

        return response(
            conversation_id,
            tool_calls,
            "escalated",
            "ambiguous_patient",
            None,
            None,
            "I found multiple patients matching those details, so I need to transfer this to a human for verification.",
            len(turns),
        )

    # =====================================
    # BOOKING
    # =====================================

    if wants_booking and not wants_cancel and not wants_reschedule:

        if patient is None:
            if not phone and not patient_name:
                return response(
                    conversation_id,
                    tool_calls,
                    "abandoned",
                    None,
                    None,
                    None,
                    "I need the patient's name or 10-digit phone number before I can book the appointment.",
                    len(turns),
                )

            return response(
                conversation_id,
                tool_calls,
                "escalated",
                "ambiguous_patient",
                None,
                None,
                "I couldn't safely verify the patient, so I need a human to verify the record.",
                len(turns),
            )

        doctor = get_doctor(text)

        if not doctor:
            return response(
                conversation_id,
                tool_calls,
                "abandoned",
                None,
                patient["id"],
                None,
                "Please provide the doctor's name so I can check availability.",
                len(turns),
            )

        date = get_date(text, today)

        if not date:
            return response(
                conversation_id,
                tool_calls,
                "abandoned",
                None,
                patient["id"],
                None,
                "Please provide the date you would like the appointment.",
                len(turns),
            )

        slots_result = search_slots(
            doctor["id"],
            date,
        )

        add_tool_call(
            tool_calls,
            "search_slots",
            {
                "doctor_id": doctor["id"],
                "date": date,
            },
        )

        if (
            slots_result["status"] != "ok"
            or not slots_result["slots"]
        ):
            return response(
                conversation_id,
                tool_calls,
                "abandoned",
                None,
                patient["id"],
                None,
                "There are no available slots for that day.",
                len(turns),
            )

        requested_time = get_requested_time(text)

        if requested_time:
            requested_start = (
                f"{date}T{requested_time}"
            )

            if requested_start in slots_result["slots"]:
                start = requested_start
            else:
                # Requested slot is unavailable.
                # Pick the first actual available slot.
                start = slots_result["slots"][0]
        else:
            start = slots_result["slots"][0]

        booking = book_appointment(
            patient["id"],
            doctor["id"],
            start,
        )

        add_tool_call(
            tool_calls,
            "book_appointment",
            {
                "patient_id": patient["id"],
                "doctor_id": doctor["id"],
                "start": start,
            },
        )

        if booking["status"] != "booked":
            return response(
                conversation_id,
                tool_calls,
                "abandoned",
                None,
                patient["id"],
                None,
                "I couldn't complete the booking because the selected slot is no longer available.",
                len(turns),
            )

        return response(
            conversation_id,
            tool_calls,
            "booked",
            None,
            patient["id"],
            booking["appointment_id"],
            f"Your appointment with {doctor['name']} is booked for {start[:10]} at {start[11:]}.",
            len(turns),
        )

    # =====================================
    # RESCHEDULE
    # =====================================

    if wants_reschedule:

        if patient is None:
            return response(
                conversation_id,
                tool_calls,
                "escalated",
                "ambiguous_patient",
                None,
                None,
                "I need to verify the patient before changing the appointment.",
                len(turns),
            )

        doctor = get_doctor(text)

        appointment = find_active_appointment(
            patient["id"],
            doctor["id"] if doctor else None,
        )

        if not appointment:
            return response(
                conversation_id,
                tool_calls,
                "abandoned",
                None,
                patient["id"],
                None,
                "I couldn't find an active appointment to reschedule.",
                len(turns),
            )

        date = get_date(text, today)

        if not date:
            return response(
                conversation_id,
                tool_calls,
                "abandoned",
                None,
                patient["id"],
                appointment["id"],
                "Please provide the new date for the appointment.",
                len(turns),
            )

        requested_time = get_requested_time(text)

        if requested_time:
            time = requested_time
        else:
            time = appointment["start"][11:16]

        new_start = f"{date}T{time}"

        result = reschedule_appointment(
            appointment["id"],
            new_start,
        )

        add_tool_call(
            tool_calls,
            "reschedule_appointment",
            {
                "appointment_id": appointment["id"],
                "new_start": new_start,
            },
        )

        if result["status"] != "rescheduled":
            return response(
                conversation_id,
                tool_calls,
                "abandoned",
                None,
                patient["id"],
                appointment["id"],
                "I couldn't reschedule the appointment because that slot is not available.",
                len(turns),
            )

        return response(
            conversation_id,
            tool_calls,
            "rescheduled",
            None,
            patient["id"],
            appointment["id"],
            f"Your appointment has been rescheduled to {new_start[:10]} at {new_start[11:]}.",
            len(turns),
        )

    # =====================================
    # CANCEL
    # =====================================

    if wants_cancel:

        if patient is None:
            return response(
                conversation_id,
                tool_calls,
                "escalated",
                "ambiguous_patient",
                None,
                None,
                "I need to verify the patient before cancelling the appointment.",
                len(turns),
            )

        appointment = find_active_appointment(
            patient["id"]
        )

        if not appointment:
            return response(
                conversation_id,
                tool_calls,
                "abandoned",
                None,
                patient["id"],
                None,
                "I couldn't find an active appointment to cancel.",
                len(turns),
            )

        result = cancel_appointment(
            appointment["id"]
        )

        add_tool_call(
            tool_calls,
            "cancel_appointment",
            {
                "appointment_id": appointment["id"],
            },
        )

        if result["status"] != "cancelled":
            return response(
                conversation_id,
                tool_calls,
                "abandoned",
                None,
                patient["id"],
                appointment["id"],
                "I couldn't cancel the appointment.",
                len(turns),
            )

        return response(
            conversation_id,
            tool_calls,
            "cancelled",
            None,
            patient["id"],
            appointment["id"],
            "Your appointment has been cancelled.",
            len(turns),
        )

    # =====================================
    # NOTHING USEFUL
    # =====================================

    return response(
        conversation_id,
        tool_calls,
        "abandoned",
        None,
        patient["id"] if patient else None,
        None,
        "I need more information to help with the appointment.",
        len(turns),
    )