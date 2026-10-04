# Design Decisions

## Backend

- Python + FastAPI for the REST API.
- SQLite/in-memory clinic data from the provided `clinic.json`.
- Tool functions are deterministic and do not call an LLM.
- Patient lookup never selects between ambiguous patients automatically.
- Booking checks the requested slot before creating an appointment.
- Clinical and medical requests are escalated instead of handled by the agent.
- Prompt injection attempts are refused.
- Relative dates are resolved using the `today` value from the request.

## Agent

- The agent uses the six required clinic tools.
- Terminal states follow the provided schema.
- Safety checks run before booking or other appointment actions.
- The agent never books when patient identity is ambiguous.
- The agent stops immediately when an urgent clinical symptom appears.

## Frontend

- React + Vite.
- Two required views are represented by the Handoff Queue and Conversation Detail sections.
- The frontend calls the FastAPI `/agent/run` endpoint.
- No authentication or external database is used because it is not required for the take-home assignment.

## Testing

- All 15 provided conversation scripts produce the expected terminal states.
- Adversarial tests cover clinical escalation, prompt injection, and ambiguous patient handling.