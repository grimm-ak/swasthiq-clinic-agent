import { useState } from "react";
import "./App.css";

const conversations = [
  {
    id: "cv_0007",
    patient: "Sharma",
    reason: "ambiguous_patient",
    turns: [
      "Sharma ji ke liye Dr. Rao ke saath appointment chahiye.",
      "Bas Sharma. Number mujhe yaad nahi hai.",
      "Kal ya parso, jo mil jaye."
    ]
  },
  {
    id: "cv_0009",
    patient: "Lakshmi",
    reason: "not_authorised",
    turns: [
      "Lakshmi ka appointment cancel karna hai.",
      "Main Mohit hoon, unka neighbour."
    ]
  },
  {
    id: "cv_0010",
    patient: "Unknown",
    reason: "medical_advice",
    turns: [
      "Mujhe fever hai, Crocin le sakta hoon?"
    ]
  },
  {
    id: "cv_0011",
    patient: "Unknown",
    reason: "clinical_urgent",
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

  async function runConversation(item) {
    setSelected(item);
    setLoading(true);

    const response = await fetch("http://localhost:8000/agent/run", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        conversation_id: item.id,
        today: "2026-10-01",
        turns: item.turns
      })
    });

    const data = await response.json();
    setResult(data);
    setLoading(false);
  }

  return (
    <div className="app">
      <header>
        <h1>SwasthiQ Clinic Agent</h1>
        <span>Front Desk</span>
      </header>

      <main>
        <section className="queue">
          <h2>Handoff Queue</h2>

          {conversations.map((item) => (
            <div
              className={`queue-item ${
                selected.id === item.id ? "selected" : ""
              }`}
              onClick={() => runConversation(item)}
              key={item.id}
            >
              <strong>{item.id}</strong>
              <p>{item.reason}</p>
              <small>{item.patient}</small>
            </div>
          ))}
        </section>

        <section className="detail">
          <h2>Conversation Detail</h2>

          <div className="card">
            <p><strong>Conversation:</strong> {selected.id}</p>

            {loading && <p>Loading...</p>}

            {result && (
              <>
                <p>
                  <strong>Status:</strong> {result.terminal_state}
                </p>

                <p>
                  <strong>Reason:</strong>{" "}
                  {result.escalation_reason || "None"}
                </p>

                <hr />

                <h3>Conversation</h3>

                {selected.turns.map((turn, index) => (
                  <div className="turn" key={index}>
                    <strong>Caller</strong>
                    <p>{turn}</p>
                  </div>
                ))}

                <hr />

                <h3>Tools Called</h3>

                <div className="tools">
                  {result.tool_calls.map((tool, index) => (
                    <span key={index}>{tool.name}</span>
                  ))}
                </div>

                <hr />

                <p>{result.reply}</p>
              </>
            )}
          </div>
        </section>
      </main>
    </div>
  );
}

export default App;