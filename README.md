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
│   ├── adv_001.json
│   ├── adv_002.json
│   ├── adv_003.json
│   ├── adv_004.json
│   ├── adv_005.json
│   ├── adv_006.json
│   ├── adv_007.json
│   └── adv_008.json
├── conversations/
├── clinic.json
├── runner.py
├── schema.md
├── DECISIONS.md
├── README.md
└── AI_TRANSCRIPT.txt
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

The evaluation endpoint accepts:

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

The response follows the required contract:

```json
{
  "conversation_id": "cv_0001",
  "tool_calls": [
    {
      "name": "lookup_patient",
      "arguments": {}
    },
    {
      "name": "search_slots",
      "arguments": {}
    },
    {
      "name": "book_appointment",
      "arguments": {}
    }
  ],
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

The tool-call arguments above are illustrative. The running agent records the actual arguments passed to each tool.

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

Relative dates are resolved using the `today` value supplied in the request rather than the system clock.

Safety checks run before appointment actions.

## Model and Efficiency

**Model:** Deterministic rule-based agent — no LLM model is called.

**LLM tokens per conversation:** 0.

No external model inference is used, so LLM token usage is zero for every conversation.

The API reports `tokens` and `latency_ms` in the response metrics.

Latency is also measured by `runner.py` for each conversation. Local latency depends on process/server warm-up and environment; the runner records the measured value for every run rather than using a fabricated fixed latency.

## Safety

The agent:

- Escalates urgent clinical symptoms immediately.
- Does not provide medical advice.
- Does not choose between ambiguous patient identities.
- Escalates requests without required authorization.
- Refuses prompt-injection attempts.
- Never invents patients, appointments, or slots.
- Does not continue booking after an urgent clinical escalation.
- Stops the booking flow when a clinical emergency appears during a conversation.

## Concurrency

Agent runs are protected by a server-side lock so concurrent requests are serialized.

The booking tool also checks the requested slot before creating an appointment, preventing duplicate bookings in the clinic state.

## Testing

### Provided conversation scripts

Run the 15 provided conversation scripts:

```bash
python3 runner.py
```

Expected result:

```text
15 script(s), 1 run(s) each
results in results/   failures: 0
```

The provided conversations cover:

- Straightforward booking
- Rescheduling
- Cancellation
- Closed clinic days
- Doctor leave
- Ambiguous patients
- Guardian authorization
- Unauthorized actions
- Medical advice
- Clinical emergencies
- Relative dates and Hindi clock times
- Incomplete conversations
- Prompt injection
- Already-booked slots

### Adversarial cases

The repository contains eight additional adversarial conversation scripts in `/adversarial`.

Run them three times to check both correctness and determinism:

```bash
python3 runner.py --dir adversarial --repeat 3
```

The final local verification produced:

```text
8 script(s), 3 run(s) each
deterministic across 3 runs

results in results/   failures: 0
```

This represents 24 successful adversarial runs.

The adversarial cases cover:

- Clinical emergency appearing during a booking
- Prompt injection and fake administrator authority
- Ambiguous patient identity
- Unauthorized third-party action
- Medical advice
- Non-actionable conversations
- Occupied appointment slots and alternative times
- Hindi relative dates and clock times

### Frontend checks

The frontend was also verified with:

```bash
npm run lint
npm run build
```

Both completed successfully.

## Determinism

The same conversation is designed to produce the same:

- `terminal_state`
- `escalation_reason`
- set of tool names

across repeated runs.

The adversarial suite was run three times and produced stable fingerprints across all eight cases.

## Live Demo

**Frontend:**

https://swasthiq-clinic-agent-frontend.onrender.com/

**Backend API:**

https://swasthiq-clinic-agent.onrender.com/

## GitHub

https://github.com/grimm-ak/swasthiq-clinic-agent

## Design Decisions

See [`DECISIONS.md`](DECISIONS.md) for the design decisions, ambiguities, safety choices, and implementation trade-offs.

## AI Transcript

The coding-assistant prompts used during development are included in:

```text
AI_TRANSCRIPT.txt
```

## Demo Video

To be added before submission.

## Submission

The final submission will include:

- Public GitHub repository
- Live frontend link
- Three-minute video
- AI transcript
- Approximate hours spent on the assignment
- What would be improved with another four hours
