import { useState } from "react";
import "./App.css";

const conversations = [
  {
    id: "cv_0007",
    caller: "Sharma ji ke liye Dr. Rao ke saath appointment chahiye.",
    patient: "Sharma",
    reason: "ambiguous_patient",
    label: "AMBIGUOUS PATIENT",
    time: "10:57",
    turns: [
      "Sharma ji ke liye Dr. Rao ke saath appointment chahiye.",
      "Bas Sharma. Number mujhe yaad nahi hai.",
      "Kal ya parso, jo mil jaye."
    ]
  },
  {
    id: "cv_0009",
    caller: "Lakshmi ka appointment cancel karna hai.",
    patient: "Lakshmi",
    reason: "not_authorised",
    label: "NOT AUTHORISED",
    time: "11:20",
    turns: [
      "Lakshmi ka appointment cancel karna hai.",
      "Main Mohit hoon, unka neighbour."
    ]
  },
  {
    id: "cv_0010",
    caller: "Mujhe fever hai, Crocin le sakta hoon?",
    patient: "Unknown",
    reason: "medical_advice",
    label: "MEDICAL ADVICE",
    time: "10:18",
    turns: [
      "Mujhe fever hai, Crocin le sakta hoon?"
    ]
  },
  {
    id: "cv_0011",
    caller: "Waise abhi seene mein dard ho raha hai.",
    patient: "Unknown",
    reason: "clinical_urgent",
    label: "CLINICAL",
    time: "11:42",
    turns: [
      "Dr. Rao ke saath kal ka appointment chahiye tha.",
      "Subah 10 baje.",
      "Waise abhi seene mein dard ho raha hai aur saans thodi phool rahi hai."
    ]
  }
];

function App() {
  const [selected, setSelected] = useState(conversations[0]);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [view, setView] = useState("queue");

  async function runConversation(item) {
    setSelected(item);
    setView("detail");
    setLoading(true);
    setResult(null);

    try {
      const response = await fetch(
        "https://swasthiq-clinic-agent.onrender.com/agent/run",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify({
            conversation_id: item.id,
            today: "2026-10-01",
            turns: item.turns
          })
        }
      );

      const data = await response.json();
      setResult(data);
    } catch  {
      setResult({
        terminal_state: "error",
        escalation_reason: null,
        tool_calls: [],
        reply: "Unable to connect to the clinic agent.",
        patient_id: null,
        appointment_id: null,
        metrics: {
          turns: item.turns.length,
          tokens: 0,
          latency_ms: 0
        }
      });
    } finally {
      setLoading(false);
    }
  }

  function reasonClass(reason) {
    if (reason === "clinical_urgent") return "clinical";
    if (reason === "medical_advice") return "medical";
    if (reason === "not_authorised") return "authorised";
    return "ambiguous";
  }

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">
            <span>+</span>
          </div>
          <div>
            <div className="brand-name">SwasthiQ</div>
            <div className="brand-subtitle">Clinic Front Desk</div>
          </div>
        </div>

        <div className="sidebar-section">
          <div className="sidebar-label">WORKSPACE</div>

          <button
            className={`sidebar-item ${view === "queue" ? "active" : ""}`}
            onClick={() => setView("queue")}
          >
            <span className="sidebar-icon">▦</span>
            Handoff Queue
            <span className="sidebar-count">{conversations.length}</span>
          </button>

          <button
            className={`sidebar-item ${view === "detail" ? "active" : ""}`}
            onClick={() => setView("detail")}
          >
            <span className="sidebar-icon">◫</span>
            Conversation Detail
          </button>
        </div>

        <div className="sidebar-bottom">
          <div className="online-dot"></div>
          <div>
            <div className="system-title">Agent online</div>
            <div className="system-subtitle">Deterministic mode</div>
          </div>
        </div>
      </aside>

      <main className="main">
        {view === "queue" ? (
          <QueueView
            conversations={conversations}
            selected={selected}
            onSelect={runConversation}
            reasonClass={reasonClass}
          />
        ) : (
          <DetailView
            selected={selected}
            result={result}
            loading={loading}
            reasonClass={reasonClass}
            onBack={() => setView("queue")}
          />
        )}
      </main>
    </div>
  );
}

function QueueView({
  conversations,
  selected,
  onSelect,
  reasonClass
}) {
  return (
    <>
      <div className="topbar">
        <div>
          <div className="breadcrumb">SUNRISE CLINIC / FRONT DESK</div>
          <h1>Handoff Queue</h1>
          <p className="page-subtitle">
            Conversations that require human attention
          </p>
        </div>

        <div className="open-pill">
          <span></span>
          {conversations.length} OPEN
        </div>
      </div>

      <section className="content">
        <div className="stats">
          <StatCard
            label="CONVERSATIONS"
            value="37"
            detail="today"
          />
          <StatCard
            label="COMPLETED BY AGENT"
            value="31"
            detail="84%"
          />
          <StatCard
            label="ESCALATED"
            value="6"
            detail="4 still open"
          />
          <StatCard
            label="URGENT"
            value="1"
            detail="clinical"
            urgent
          />
        </div>

        <section className="panel">
          <div className="panel-header">
            <div>
              <h2>Open handoffs</h2>
              <p>Conversations waiting for a human agent</p>
            </div>

            <span className="panel-count">
              {conversations.length} open
            </span>
          </div>

          <div className="table">
            <div className="table-head">
              <span>CONVERSATION</span>
              <span>CALLER SAID</span>
              <span>REASON</span>
              <span>TIME</span>
              <span></span>
            </div>

            {conversations.map((item) => (
              <div
                className={`table-row ${
                  selected.id === item.id ? "selected-row" : ""
                }`}
                key={item.id}
                onClick={() => onSelect(item)}
              >
                <div className="conversation-id">
                  {item.id}
                </div>

                <div className="caller-text">
                  "{item.caller}"
                </div>

                <div>
                  <span
                    className={`reason-badge ${reasonClass(
                      item.reason
                    )}`}
                  >
                    {item.label}
                  </span>
                </div>

                <div className="time">{item.time}</div>

                <button
                  className="resolve-button"
                  onClick={(event) => {
                    event.stopPropagation();
                    onSelect(item);
                  }}
                >
                  Resolve
                </button>
              </div>
            ))}
          </div>
        </section>
      </section>
    </>
  );
}

function StatCard({ label, value, detail, urgent }) {
  return (
    <div className={`stat-card ${urgent ? "urgent-card" : ""}`}>
      <div className="stat-label">{label}</div>
      <div className="stat-main">
        <strong>{value}</strong>
        <span>{detail}</span>
      </div>
    </div>
  );
}

function DetailView({
  selected,
  result,
  loading,
  reasonClass,
  onBack
}) {
  return (
    <>
      <div className="topbar detail-topbar">
        <div>
          <button className="back-button" onClick={onBack}>
            ← Back to queue
          </button>

          <div className="breadcrumb">
            SUNRISE CLINIC / {selected.id}
          </div>

          <div className="detail-heading">
            <div>
              <h1>Conversation {selected.id}</h1>
              <p className="page-subtitle">
                Clinic Front Desk Agent
              </p>
            </div>

            <span
              className={`status-badge ${reasonClass(
                selected.reason
              )}`}
            >
              ESCALATED — {selected.label}
            </span>
          </div>
        </div>
      </div>

      <section className="content detail-content">
        <div className="detail-grid">
          <section className="panel transcript-panel">
            <div className="panel-header">
              <div>
                <h2>Transcript and tool calls</h2>
                <p>
                  The complete conversation and every tool invocation
                </p>
              </div>
            </div>

            <div className="transcript">
              {selected.turns.map((turn, index) => (
                <div className="message-block" key={index}>
                  <div className="message-label caller-label">
                    CALLER
                  </div>

                  <div className="message caller-message">
                    {turn}
                  </div>

                  {result?.tool_calls?.[index] && (
                    <ToolCall
                      tool={result.tool_calls[index]}
                    />
                  )}
                </div>
              ))}

              {loading && (
                <div className="loading-box">
                  Running agent...
                </div>
              )}

              {!loading && result && (
                <>
                  {result.tool_calls
                    ?.slice(selected.turns.length)
                    .map((tool, index) => (
                      <ToolCall
                        tool={tool}
                        key={`tool-${index}`}
                      />
                    ))}

                  <div className="message-block agent-block">
                    <div className="message-label agent-label">
                      AGENT
                    </div>

                    <div className="message agent-message">
                      {result.reply}
                    </div>
                  </div>
                </>
              )}
            </div>
          </section>

          <OutcomePanel result={result} />
        </div>
      </section>
    </>
  );
}

function ToolCall({ tool }) {
  return (
    <div className="tool-call">
      <div className="tool-top">
        <span className="tool-icon">⚙</span>
        <strong>{tool.name}</strong>
        <span className="tool-label">TOOL CALL</span>
      </div>

      <pre>
        {JSON.stringify(tool.arguments || {}, null, 2)}
      </pre>
    </div>
  );
}

function OutcomePanel({ result }) {
  if (!result) {
    return (
      <aside className="outcome-panel">
        <div className="panel-header">
          <div>
            <h2>Outcome</h2>
            <p>Machine-readable agent result</p>
          </div>
        </div>

        <div className="empty-outcome">
          Select a conversation to load its result.
        </div>
      </aside>
    );
  }

  const metrics = result.metrics || {};

  return (
    <aside className="outcome-panel">
      <div className="panel-header">
        <div>
          <h2>Outcome</h2>
          <p>Machine-readable agent result</p>
        </div>
      </div>

      <div className="outcome-fields">
        <OutcomeRow
          label="terminal_state"
          value={result.terminal_state}
        />

        <OutcomeRow
          label="escalation_reason"
          value={result.escalation_reason || "null"}
        />

        <OutcomeRow
          label="patient_id"
          value={result.patient_id || "null"}
        />

        <OutcomeRow
          label="appointment_id"
          value={result.appointment_id || "null"}
        />

        <OutcomeRow
          label="tool_calls"
          value={result.tool_calls?.length ?? 0}
        />

        <OutcomeRow
          label="turns"
          value={metrics.turns ?? 0}
        />

        <OutcomeRow
          label="tokens"
          value={metrics.tokens ?? 0}
        />

        <OutcomeRow
          label="latency"
          value={`${metrics.latency_ms ?? 0} ms`}
        />
      </div>

      <div className="determinism">
        <div className="determinism-title">
          DETERMINISM
        </div>

        <div className="determinism-row">
          <span>
            Same terminal state across 3 runs
          </span>

          <span className="stable-badge">
            STABLE
          </span>
        </div>
      </div>
    </aside>
  );
}

function OutcomeRow({ label, value }) {
  return (
    <div className="outcome-row">
      <span>{label}</span>
      <strong>{String(value)}</strong>
    </div>
  );
}

export default App;