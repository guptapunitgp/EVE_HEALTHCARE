import { useState } from "react";
import api from "../lib/api";
import { PageHeader } from "../components/Layout";

const starters = ["What is a CBC test?", "How should I prepare for a blood test?", "What does a diagnostic report usually include?"];

export default function AssistantPage() {
  const [messages, setMessages] = useState([]);
  const [question, setQuestion] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const ask = async (text = question) => {
    const clean = text.trim();
    if (!clean || busy) return;
    const next = [...messages, { role: "user", text: clean }].slice(-12);
    setMessages(next); setQuestion(""); setBusy(true); setError("");
    try {
      const response = await api.post("/ai/education", { messages: next });
      setMessages([...next, { role: "model", text: response.data.answer }].slice(-12));
    } catch (exception) {
      setMessages(messages);
      setQuestion(clean);
      setError(exception.response?.data?.detail || "The assistant is unavailable right now. Please try again later.");
    } finally { setBusy(false); }
  };
  return <><PageHeader eyebrow="EDUCATION AND SUPPORT" title="EVE AI assistant" subtitle="Ask general questions about diagnostic tests and health topics."/><div className="assistant-layout"><div className="assistant-warning"><span>ⓘ</span><div><b>Educational information only</b><p>The assistant cannot diagnose, interpret personal results, or replace a qualified clinician. For urgent symptoms, contact local emergency services.</p></div></div><section className="chat-panel"><div className="chat-title"><span className="ai-orb">✧</span><div><b>EVE AI Assistant</b><small>General health education · Gemini</small></div><span className="online-status"><i/> Ready</span></div><div className="chat-messages"><div className="chat-bubble assistant-bubble"><b>Hello, I’m here to help you learn.</b><p>Ask about common tests, preparation steps, or general health terms. Please don’t share names, contact details, or personal medical records.</p></div>{messages.map((message,index)=><div key={`${index}-${message.role}`} className={`chat-bubble ${message.role==="user"?"user-bubble":"assistant-bubble"}`}>{message.text}</div>)}{busy&&<div className="chat-bubble assistant-bubble typing">Thinking…</div>}{error&&<div className="notice error">{error}</div>}{!messages.length&&<div className="starter-prompts">{starters.map((item)=><button key={item} onClick={()=>ask(item)}>{item} <span>↗</span></button>)}</div>}</div><form className="chat-input" onSubmit={(e)=>{e.preventDefault();void ask();}}><input maxLength={2000} value={question} onChange={(e)=>setQuestion(e.target.value)} placeholder="Ask a health-related question…"/><button className="primary-button" disabled={busy||!question.trim()} aria-label="Send question">➤</button></form></section></div></>;
}
