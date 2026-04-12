import { useEffect, useRef, useState } from "react";
import "./App.css";

const QUICK_ACTIONS = [
  "How do I reset my password?",
  "Reset password for student12",
  "Wi-Fi is not working in Room 204",
  "I need help with my Chromebook"
];

const STARTER_PILLS = [
  "Reset my password",
  "Wi-Fi or device help",
  "Schedule IT appointment"
];

const API_BASE_URL = process.env.REACT_APP_API_URL || "http://127.0.0.1:8000";

function MessageCard({ message, onAction }) {
  const metadata = message.metadata || {};
  const workflowResult = metadata.workflow_result || null;
  const passwordPolicy = metadata.password_policy || workflowResult?.password_policy || null;
  const ticket = metadata.ticket?.ticket || metadata.ticket || null;
  const userLookup = metadata.user_lookup?.user || null;
  const appointment = metadata.appointment || null;
  const appointmentSlots = metadata.appointment_slots || [];
  const escalationOptions = metadata.escalation_options || [];
  const followUpActions = metadata.follow_up_actions || [];
  const softwareRequestForm = metadata.software_request_form || null;
  const [requestType, setRequestType] = useState("Software");
  const [itemName, setItemName] = useState("");
  const [purpose, setPurpose] = useState("");
  const [deviceType, setDeviceType] = useState("");
  const [deadline, setDeadline] = useState("");

  const submitSoftwareRequest = () => {
    const formattedMessage = [
      "Software/Hardware Request",
      `Request Type: ${requestType}`,
      `Item: ${itemName || "Not specified"}`,
      `Purpose: ${purpose || "Not specified"}`,
      `Device Type: ${deviceType || "Not specified"}`,
      `Deadline: ${deadline || "Not specified"}`,
    ].join("\n");
    onAction(formattedMessage);
  };

  return (
    <>
      <p>{message.text}</p>

      {workflowResult?.temporary_password && (
        <div className="structured-card workflow-card">
          <div className="card-header">
            <h4>Password Reset Complete</h4>
            <span className="status-pill success-pill">Temporary password issued</span>
          </div>
          <div className="card-grid">
            <div>
              <p className="card-label">Username</p>
              <strong>{workflowResult.username}</strong>
            </div>
            <div>
              <p className="card-label">Temporary Password</p>
              <strong className="credential-chip">{workflowResult.temporary_password}</strong>
            </div>
            <div>
              <p className="card-label">Next Step</p>
              <strong>{workflowResult.must_change_password ? "Change at next sign-in" : "Optional"}</strong>
            </div>
            {userLookup && (
              <div>
                <p className="card-label">User Role</p>
                <strong>{userLookup.role}</strong>
              </div>
            )}
          </div>
        </div>
      )}

      {passwordPolicy && (
        <div className="structured-card policy-card">
          <div className="card-header">
            <h4>Password Policy</h4>
            <span className="status-pill neutral-pill">Role-based rules</span>
          </div>
          <ul className="policy-list">
            <li>Minimum length: {passwordPolicy.min_length}</li>
            <li>Uppercase required: {passwordPolicy.require_upper ? "Yes" : "No"}</li>
            <li>Lowercase required: {passwordPolicy.require_lower ? "Yes" : "No"}</li>
            <li>Number required: {passwordPolicy.require_digit ? "Yes" : "No"}</li>
            <li>Symbol required: {passwordPolicy.require_symbol ? "Yes" : "No"}</li>
          </ul>
          {passwordPolicy.reset_note && <p className="card-footnote">{passwordPolicy.reset_note}</p>}
        </div>
      )}

      {ticket && (
        <div className="structured-card ticket-card">
          <div className="card-header">
            <h4>Request Submitted</h4>
            <span className="status-pill warning-pill">{ticket.status}</span>
          </div>
          <div className="card-grid">
            <div>
              <p className="card-label">Ticket ID</p>
              <strong>{ticket.ticket_id}</strong>
            </div>
            <div>
              <p className="card-label">Urgency</p>
              <strong>{ticket.urgency}</strong>
            </div>
            <div className="card-span">
              <p className="card-label">Issue Summary</p>
              <strong>{ticket.issue_summary}</strong>
            </div>
          </div>
        </div>
      )}

      {appointment && (
        <div className="structured-card appointment-card">
          <div className="card-header">
            <h4>IT Appointment Scheduled</h4>
            <span className="status-pill success-pill">{appointment.status}</span>
          </div>
          <div className="card-grid">
            <div>
              <p className="card-label">Slot ID</p>
              <strong>{appointment.slot_id}</strong>
            </div>
            <div>
              <p className="card-label">Location</p>
              <strong>{appointment.location}</strong>
            </div>
            <div className="card-span">
              <p className="card-label">Starts At</p>
              <strong>{new Date(appointment.starts_at).toLocaleString()}</strong>
            </div>
          </div>
        </div>
      )}

      {appointmentSlots.length > 0 && (
        <div className="structured-card appointment-card">
          <div className="card-header">
            <h4>Available IT Appointment Slots</h4>
            <span className="status-pill neutral-pill">Choose a slot</span>
          </div>
          <div className="slot-list">
            {appointmentSlots.map((slot) => (
              <button
                key={slot.slot_id}
                className="action-pill"
                onClick={() => onAction(`Book appointment ${slot.slot_id} for my IT issue`)}
              >
                {slot.slot_id} · {new Date(slot.starts_at).toLocaleString()}
              </button>
            ))}
          </div>
        </div>
      )}

      {followUpActions.length > 0 && (
        <div className="structured-card escalation-card">
          <div className="card-header">
            <h4>Next Step</h4>
            <span className="status-pill neutral-pill">Available actions</span>
          </div>
          <div className="slot-list">
            {followUpActions.map((action) => (
              <button key={action} className="action-pill" onClick={() => onAction(action)}>
                {action}
              </button>
            ))}
          </div>
        </div>
      )}

      {escalationOptions.length > 0 && (
        <div className="structured-card escalation-card">
          <div className="card-header">
            <h4>Next Steps</h4>
            <span className="status-pill neutral-pill">Support options</span>
          </div>
          <div className="slot-list">
            {escalationOptions.map((option) => (
              <button key={option} className="action-pill" onClick={() => onAction(option)}>
                {option}
              </button>
            ))}
          </div>
        </div>
      )}

      {softwareRequestForm && (
        <div className="structured-card request-form-card">
          <div className="card-header">
            <h4>{softwareRequestForm.title}</h4>
            <span className="status-pill neutral-pill">IT request form</span>
          </div>
          <div className="request-form-grid">
            <label>
              <span className="card-label">Request Type</span>
              <select value={requestType} onChange={(event) => setRequestType(event.target.value)}>
                {softwareRequestForm.request_types.map((type) => (
                  <option key={type} value={type}>{type}</option>
                ))}
              </select>
            </label>
            <label>
              <span className="card-label">Item</span>
              <input value={itemName} onChange={(event) => setItemName(event.target.value)} placeholder="Example: Adobe Express" />
            </label>
            <label className="request-form-span">
              <span className="card-label">Purpose</span>
              <textarea value={purpose} onChange={(event) => setPurpose(event.target.value)} rows={3} placeholder="Describe why this is needed." />
            </label>
            <label>
              <span className="card-label">Device Type</span>
              <input value={deviceType} onChange={(event) => setDeviceType(event.target.value)} placeholder="Chromebook, MacBook, lab PC..." />
            </label>
            <label>
              <span className="card-label">Deadline</span>
              <input value={deadline} onChange={(event) => setDeadline(event.target.value)} placeholder="Example: Next Friday" />
            </label>
          </div>
          <button className="form-submit-button" onClick={submitSoftwareRequest}>
            Submit Request
          </button>
        </div>
      )}
    </>
  );
}

function App() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([
    {
      id: "welcome-message",
      type: "assistant",
      text: "Welcome to the Constellations IT Support Agent. I can answer school IT questions, help with password resets, and route issues to support.",
      sessionId: null,
      intent: "knowledge",
      agent: "assistant",
      sources: [],
      metadata: {}
    }
  ]);
  const [sessionId] = useState(() => "session-" + Date.now());
  const [isLoading, setIsLoading] = useState(false);
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const chatFeedRef = useRef(null);
  const formatAgentLabel = (agent) => {
    if (!agent) {
      return "Support ready";
    }

    if (agent === "escalation") {
      return "Escalation and Scheduling Active";
    }

    if (agent === "workflow") {
      return "Workflow Agent Active";
    }

    if (agent === "knowledge") {
      return "Knowledge Agent Active";
    }

    return `${agent
      .split("_")
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(" ")} Active`;
  };
  const activeAssistantMessage = [...messages].reverse().find((message) => message.type === "assistant");
  const activeAgentLabel = isLoading
    ? "Analyzing Request"
    : formatAgentLabel(activeAssistantMessage?.agent);

  useEffect(() => {
    if (!chatFeedRef.current) {
      return;
    }

    chatFeedRef.current.scrollTop = chatFeedRef.current.scrollHeight;
  }, [messages, isChatOpen]);

  useEffect(() => {
    document.body.style.overflow = isChatOpen ? "hidden" : "";

    return () => {
      document.body.style.overflow = "";
    };
  }, [isChatOpen]);

  const openChat = () => {
    setIsChatOpen(true);
    setIsMenuOpen(false);
  };

  const closeChat = () => {
    setIsChatOpen(false);
  };

  const sendMessage = async (prefilledMessage) => {
    const outgoingMessage = (prefilledMessage ?? input).trim();
    if (!outgoingMessage || isLoading) return;

    if (["exit", "exit chat", "close chat", "close"].includes(outgoingMessage.toLowerCase())) {
      setInput("");
      closeChat();
      return;
    }

    setIsLoading(true);
    setMessages((currentMessages) => [
      ...currentMessages,
      {
        id: `user-${Date.now()}`,
        type: "user",
        text: outgoingMessage
      }
    ]);

    try {
      const response = await fetch(`${API_BASE_URL}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          message: outgoingMessage,
          session_id: sessionId
        })
      });

      if (!response.ok) {
        throw new Error("Support service unavailable");
      }

      const data = await response.json();

      setMessages((currentMessages) => [
        ...currentMessages,
        {
          id: `assistant-${Date.now()}`,
          type: "assistant",
          text: data.response,
          sessionId: data.session_id,
          intent: data.intent,
          agent: data.agent_used,
          sources: data.sources || [],
          metadata: data.metadata || {}
        }
      ]);
      setInput("");
      setIsChatOpen(true);
    } catch (error) {
      setMessages((currentMessages) => [
        ...currentMessages,
        {
          id: `error-${Date.now()}`,
          type: "assistant",
          text: "The IT support service is not reachable right now. Please try again in a moment or contact the school office.",
          sessionId,
          intent: "error",
          agent: "system",
          sources: [],
          metadata: {}
        }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleComposerKeyDown = async (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      await sendMessage();
    }
  };

  return (
    <div className="site-shell">
      <header className="site-header">
        <div className="brand-lockup">
          <div className="brand-mark">C</div>
          <div>
            <p className="brand-kicker">Constellations.com</p>
            <h1 className="brand-name">Constellations School</h1>
          </div>
        </div>

        <nav className="site-nav" aria-label="Primary">
          <a href="#academics">Academics</a>
          <a href="#families">Families</a>
          <a href="#student-life">Student Life</a>
          <button className="nav-agent-button" onClick={openChat}>
            IT Agent
          </button>
        </nav>

        <button
          className={`burger-button ${isMenuOpen ? "is-open" : ""}`}
          aria-label="Open navigation menu"
          onClick={() => setIsMenuOpen((open) => !open)}
        >
          <span />
          <span />
          <span />
        </button>
      </header>

      {isMenuOpen && (
        <div className="mobile-menu">
          <a href="#academics" onClick={() => setIsMenuOpen(false)}>Academics</a>
          <a href="#families" onClick={() => setIsMenuOpen(false)}>Families</a>
          <a href="#student-life" onClick={() => setIsMenuOpen(false)}>Student Life</a>
          <button className="mobile-agent-button" onClick={openChat}>
            Open IT Agent
          </button>
        </div>
      )}

      <main>
        <section className="hero-section">
          <div className="hero-copy">
            <p className="eyebrow">Welcome to Constellations School</p>
            <h2>Where curiosity, kindness, and creativity grow every day.</h2>
            <p className="hero-description">
              Constellations is a joyful K-12 learning community where students explore big ideas,
              families stay connected, and every classroom is designed to support discovery,
              belonging, and confidence.
            </p>
            <div className="hero-actions">
              <button className="primary-cta">Explore Programs</button>
              <button className="secondary-cta" onClick={openChat}>
                Open IT Agent
              </button>
            </div>
          </div>

          <div className="hero-panel">
            <div className="hero-card glow-card teal-card">
              <p className="mini-label">Learning By Doing</p>
              <h3>Students build, imagine, and solve real problems together.</h3>
              <ul>
                <li>Hands-on STEM projects and maker spaces</li>
                <li>Outdoor learning, arts, and collaborative classrooms</li>
                <li>Technology that supports creativity and exploration</li>
              </ul>
            </div>
            <div className="hero-card stats-card coral-card">
              <p className="mini-label">Family Favorites</p>
              <div className="stat-grid">
                <div>
                  <strong>Small</strong>
                  <span>Community-centered classrooms</span>
                </div>
                <div>
                  <strong>Joyful</strong>
                  <span>Arts, clubs, and student showcases</span>
                </div>
                <div>
                  <strong>Safe</strong>
                  <span>Responsive support for students and families</span>
                </div>
                <div>
                  <strong>Connected</strong>
                  <span>Easy access to resources and help</span>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="quick-launch-strip">
          <p>Need tech help while you browse?</p>
          <div className="quick-launch-actions">
            {QUICK_ACTIONS.map((action) => (
              <button key={action} onClick={() => sendMessage(action)}>
                {action}
              </button>
            ))}
          </div>
        </section>

        <section className="info-grid" id="academics">
          <article className="info-card">
            <p className="mini-label">Academics</p>
            <h3>Learning pathways from early years through graduation</h3>
            <p>
              Students grow through literacy, math, science, design, and project-based learning
              experiences tailored to every stage of the journey.
            </p>
          </article>
          <article className="info-card" id="families">
            <p className="mini-label">Family Resources</p>
            <h3>Helpful information for schedules, technology, and school connection</h3>
            <p>
              Find school updates, onboarding materials, device expectations, calendars, and
              support options that help families stay informed.
            </p>
          </article>
          <article className="info-card" id="student-life">
            <p className="mini-label">Student Life</p>
            <h3>Clubs, athletics, arts, and spaces where students shine</h3>
            <p>
              From robotics to performances to recess and leadership, campus life is full of
              opportunities to belong, contribute, and explore.
            </p>
          </article>
        </section>

        <section className="feature-band">
          <div className="feature-band-copy">
            <p className="eyebrow">Colorful School Life</p>
            <h3>A school website designed around learning, belonging, and family connection.</h3>
            <p>
              Browse programs, see campus highlights, and use the IT Agent whenever you need help
              with passwords, devices, Wi-Fi, or scheduling support with the school technology team.
            </p>
          </div>
          <div className="feature-band-grid">
            <article className="feature-tile mint-tile">
              <h4>Campus</h4>
              <p>Warm classrooms, outdoor spaces, and inviting places to learn together.</p>
            </article>
            <article className="feature-tile berry-tile">
              <h4>Innovation</h4>
              <p>Design thinking, digital fluency, and projects that turn ideas into action.</p>
            </article>
            <article className="feature-tile sun-tile">
              <h4>Community</h4>
              <p>Family partnership, student voice, and support that meets people where they are.</p>
            </article>
          </div>
        </section>

        <section className="resource-strip">
          <article className="resource-card">
            <p className="mini-label">Programs</p>
            <h3>Early Learning to Middle School</h3>
            <p>Developmentally responsive teaching with room for wonder, challenge, and growth.</p>
          </article>
          <article className="resource-card">
            <p className="mini-label">Family Portal</p>
            <h3>Schedules, updates, and school resources</h3>
            <p>Find essential family information and use the IT Agent whenever technology help is needed.</p>
          </article>
          <article className="resource-card resource-card-accent">
            <p className="mini-label">Need Support?</p>
            <h3>Technology help is one click away</h3>
            <p>{activeAgentLabel}. Open the IT Agent for passwords, devices, Wi-Fi, or appointments.</p>
            <button className="footer-cta" onClick={openChat}>
              Launch IT Agent
            </button>
          </article>
        </section>
      </main>

      <footer className="site-footer">
        <div>
          <p className="brand-kicker">Constellations School</p>
          <p className="footer-copy">
            A fictional K-12 district website created for the capstone demonstration.
          </p>
        </div>
        <div className="footer-actions">
          <button className="footer-link-button" onClick={openChat}>
            IT Agent
          </button>
          <button
            className="footer-link-button"
            onClick={() => sendMessage("Wi-Fi is not working in one classroom")}
          >
            Report Wi-Fi Issue
          </button>
        </div>
      </footer>

      <button className="floating-launcher" onClick={openChat}>
        IT Agent
      </button>

	      {isChatOpen && (
	        <div className="chat-overlay" role="dialog" aria-modal="true" aria-label="IT support chatbot">
	          <div className="chat-panel">
	            <div className="chat-panel-header">
              <div>
                <p className="mini-label">Constellations.com</p>
                <h3>Constellations IT Support</h3>
              </div>
              <button className="close-chat" onClick={closeChat} aria-label="Close support chat">
                Close
              </button>
            </div>

            <div className="chat-panel-intro">
              <p>
                Ask a question, request password help, or describe a device issue.
              </p>
            </div>

	            <div className="agent-status-bar" aria-live="polite">
	              <span className={`agent-status-dot ${isLoading ? "is-busy" : ""}`} />
	              <strong>{activeAgentLabel}</strong>
	            </div>

	            <div className="starter-pill-section">
	              <p className="starter-pill-title">What can I assist you with?</p>
	              <div className="chat-quick-actions">
	                {STARTER_PILLS.map((action) => (
                  <button key={action} onClick={() => sendMessage(action)} disabled={isLoading}>
                    {action}
                  </button>
	                ))}
	              </div>
	            </div>

	            <div className="chat-body">
	              <div className="chat-feed" ref={chatFeedRef}>
	                {messages.map((message) => (
	                  <div
	                    key={message.id}
	                    className={`message-row ${message.type === "user" ? "user-row" : "assistant-row"}`}
	                  >
	                    <div className={`message-bubble ${message.type === "user" ? "user-bubble" : "assistant-bubble"}`}>
	                      {message.type === "assistant" ? (
	                        <MessageCard message={message} onAction={sendMessage} />
	                      ) : (
	                        <p>{message.text}</p>
	                      )}
	                    </div>
	                  </div>
	                ))}

	                {isLoading && (
	                  <div className="message-row assistant-row">
	                    <div className="message-bubble assistant-bubble loading-bubble">
	                      <span />
	                      <span />
	                      <span />
	                    </div>
	                  </div>
	                )}
	              </div>

	            </div>

	            <div className="chat-composer">
              <textarea
                value={input}
                onChange={(event) => setInput(event.target.value)}
                onKeyDown={handleComposerKeyDown}
                placeholder="Ask the IT Agent anything..."
                rows={2}
              />
              <button onClick={() => sendMessage()} disabled={isLoading}>
                {isLoading ? "Sending..." : "Send"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
