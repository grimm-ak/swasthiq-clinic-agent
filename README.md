# SwasthiQ Clinic Front Desk Agent

A deterministic clinic front-desk agent built for the SwasthiQ SDE Intern take-home assignment.

## Features

- Appointment search and booking
- Appointment rescheduling
- Appointment cancellation
- Patient lookup
- Human escalation
- Clinical emergency escalation
- Medical-advice refusal/escalation
- Ambiguous-patient protection
- Prompt-injection refusal
- Double-booking protection
- Deterministic conversation outcomes
- React frontend with Handoff Queue and Conversation Detail

## Tech Stack

### Backend

- Python
- FastAPI
- Pydantic
- In-memory clinic state loaded from `clinic.json`

### Frontend

- React
- Vite
- CSS

## Project Structure

```text
swasthiq-clinic-agent/
├── backend/
│   ├── agent.py
│   ├── data.py
│   ├── main.py
│   ├── tools.py
│   └── requirements.txt
├── frontend/
├── adversarial/
├── conversations/
├── clinic.json
├── runner.py
├── schema.md
├── DECISIONS.md
└── README.md
```

## Running the Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

The API will be available at:

```text
http://localhost:8000
```

## Running the Frontend

In another terminal:

```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at:

```text
http://localhost:5173
```

## API

### POST `/agent/run`

Example request:

```json
{
  "conversation_id": "cv_0001",
  "today": "2026-10-01",
  "turns": [
    "Namaste, Dr. Rao ke saath appointment chahiye tha.",
    "Shanivaar subah, 3 tareekh.",
    "Main Harpreet Singh, number 9812200311."
  ]
}
```

The API returns the required response contract:

```json
{
  "conversation_id": "cv_0001",
  "tool_calls": [],
  "terminal_state": "booked",
  "escalation_reason": null,
  "patient_id": "pt_0013",
  "appointment_id": "ap_0021",
  "reply": "Your appointment has been booked.",
  "metrics": {
    "turns": 3,
    "tokens": 0,
    "latency_ms": 0
  }
}
```

## Agent Design

The agent is deterministic and does not make external LLM calls.

The clinic tools are deterministic ground-truth operations:

- `lookup_patient`
- `search_slots`
- `book_appointment`
- `reschedule_appointment`
- `cancel_appointment`
- `escalate_to_human`

Tools never call an LLM.

Relative dates are resolved using the `today` value supplied in the request.

Safety checks run before appointment actions.

### Model and Efficiency

**Model:** Deterministic rule-based agent — no LLM model is called.

**LLM tokens per conversation:** 0

The API reports `tokens` and `latency_ms` in the response metrics. Since no LLM is used, token usage is zero.

## Safety

The agent:

- Escalates urgent clinical symptoms immediately.
- Does not provide medical advice.
- Does not choose between ambiguous patient identities.
- Escalates requests without required authorization.
- Refuses prompt-injection attempts.
- Never invents patients, appointments, or slots.
- Does not continue booking after an urgent clinical escalation.

## Concurrency

Agent runs are protected by a server-side lock so concurrent requests are serialized.

The booking tool also checks the requested slot before creating an appointment, preventing duplicate bookings in the clinic state.

## Testing

Run the provided conversation scripts:

```bash
python3 runner.py
```

Expected result:

```text
15 script(s)
failures: 0
```

Run adversarial tests:

```bash
python3 adversarial/test_adversarial.py
```

Expected result:

```text
All adversarial tests passed.
```

The adversarial tests cover:

- Clinical emergency escalation
- Prompt injection refusal
- Ambiguous patient handling

## Design Decisions

See [DECISIONS.md](DECISIONS.md).

## Submission Links

### GitHub

https://github.com/grimm-ak/swasthiq-clinic-agent

### Live Demo

_To be added after deployment._

### Demo Video

_To be added._

### AI Transcript

_To be added._