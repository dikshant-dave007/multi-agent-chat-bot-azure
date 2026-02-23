"""
Streamlit UI for Multi-Agent Automation System
"""
import os
import streamlit as st
import asyncio
from typing import Dict, Any

from src.orchestration.semantic_kernel_orchestrator import get_semantic_kernel_orchestrator
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Multi-Agent System",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@300;400;500;600&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap');

/* ── RESET ─────────────────────────────────────────── */
#MainMenu, footer, header,
[data-testid="stToolbar"],
[data-testid="stDecoration"] { visibility: hidden !important; display: none !important; }

:root {
    --bg:         #0a0a0b;
    --surface:    #111113;
    --panel:      #17171a;
    --border:     rgba(255,255,255,0.07);
    --border-hi:  rgba(255,255,255,0.14);
    --amber:      #d4922a;
    --amber-dim:  rgba(212,146,42,0.15);
    --amber-glow: rgba(212,146,42,0.3);
    --fg:         #e8e6df;
    --fg-2:       #7a7870;
    --fg-3:       #3d3c38;
    --green:      #3d9970;
    --green-dim:  rgba(61,153,112,0.15);
    --red:        #c0392b;
    --blue:       #4a7fa5;
    --blue-dim:   rgba(74,127,165,0.15);
    --purple:     #7c5cbf;
    --purple-dim: rgba(124,92,191,0.15);
    --pink:       #b05080;
    --pink-dim:   rgba(176,80,128,0.15);
    --mono:       'IBM Plex Mono', monospace;
    --sans:       'IBM Plex Sans', sans-serif;
    --r:          4px;
}

* { box-sizing: border-box; scrollbar-width: thin; scrollbar-color: var(--panel) var(--bg); }
*::-webkit-scrollbar { width: 4px; height: 4px; }
*::-webkit-scrollbar-track { background: var(--bg); }
*::-webkit-scrollbar-thumb { background: var(--panel); border-radius: 2px; }

html, body, #root,
.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stApp"],
.main, main {
    background: var(--bg) !important;
    font-family: var(--sans) !important;
    color: var(--fg) !important;
}

.block-container {
    padding: 1.5rem 1.5rem 0 !important;
    max-width: 100% !important;
    background: var(--bg) !important;
}

/* ── GLOBAL TEXT ───────────────────────────────────── */
.stApp *, .stApp p, .stApp span, .stApp div, .stApp label {
    font-family: var(--sans) !important;
    color: var(--fg) !important;
}
h1,h2,h3,h4,h5,h6 {
    font-family: var(--mono) !important;
    color: var(--fg) !important;
    letter-spacing: -0.01em;
}

/* ── SIDEBAR ───────────────────────────────────────── */
section[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border) !important;
    min-width: 260px !important;
}
[data-testid="stSidebar"] > div { background: var(--surface) !important; }
[data-testid="stSidebar"] * { font-family: var(--sans) !important; color: var(--fg) !important; }

[data-testid="stSidebar"] h1 {
    font-family: var(--mono) !important;
    font-size: 0.95rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    color: var(--fg) !important;
}
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    font-family: var(--mono) !important;
    font-size: 0.6rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.14em !important;
    text-transform: uppercase !important;
    color: var(--fg-2) !important;
    margin-bottom: 0.5rem !important;
}

/* ── METRICS ───────────────────────────────────────── */
[data-testid="metric-container"] {
    background: var(--panel) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--r) !important;
    padding: 0.6rem 0.75rem !important;
}
[data-testid="stMetricValue"] {
    font-family: var(--mono) !important;
    font-size: 1.1rem !important;
    color: var(--fg) !important;
}
[data-testid="stMetricLabel"] {
    font-family: var(--mono) !important;
    font-size: 0.6rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.1em !important;
    color: var(--fg-2) !important;
}

/* ── BUTTONS ───────────────────────────────────────── */
.stButton > button {
    background: var(--panel) !important;
    color: var(--fg-2) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--r) !important;
    font-family: var(--mono) !important;
    font-size: 0.75rem !important;
    font-weight: 400 !important;
    letter-spacing: 0.04em !important;
    padding: 0.4rem 0.75rem !important;
    transition: all 0.15s ease !important;
}
.stButton > button:hover {
    background: var(--panel) !important;
    color: var(--fg) !important;
    border-color: var(--border-hi) !important;
    transform: none !important;
}
.stButton > button[kind="secondary"] {
    color: var(--red) !important;
    opacity: 0.6;
}
.stButton > button[kind="secondary"]:hover {
    opacity: 1;
    border-color: var(--red) !important;
    background: rgba(192,57,43,0.08) !important;
}

/* ── DIVIDER ───────────────────────────────────────── */
hr, [data-testid="stDivider"] {
    border: none !important;
    border-top: 1px solid var(--border) !important;
    margin: 0.875rem 0 !important;
}

/* ── AGENT INFO CARD ───────────────────────────────── */
.agent-card {
    background: var(--panel);
    border: 1px solid var(--border);
    border-left: 2px solid var(--amber);
    border-radius: var(--r);
    padding: 0.875rem 1rem;
    margin-bottom: 0.75rem;
}
.agent-card .label {
    font-family: var(--mono);
    font-size: 0.55rem;
    font-weight: 500;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--fg-3);
    margin-bottom: 0.3rem;
}
.agent-card .name {
    font-family: var(--mono);
    font-size: 0.8rem;
    font-weight: 600;
    color: var(--fg);
    margin-bottom: 0.2rem;
}
.agent-card .desc {
    font-family: var(--sans);
    font-size: 0.75rem;
    color: var(--fg-2);
    line-height: 1.4;
}
.status-dot {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    font-family: var(--mono);
    font-size: 0.6rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--green);
    margin-bottom: 0.5rem;
}
.status-dot::before {
    content: '';
    width: 5px; height: 5px;
    border-radius: 50%;
    background: var(--green);
    animation: blink 2s infinite;
}
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0.35} }

.waiting-state {
    padding: 1.25rem 0.75rem;
    text-align: center;
    border: 1px dashed var(--border);
    border-radius: var(--r);
}
.waiting-state p {
    font-family: var(--mono) !important;
    font-size: 0.7rem !important;
    color: var(--fg-3) !important;
    margin: 0 !important;
}

/* ── CHAT MESSAGES ─────────────────────────────────── */
[data-testid="stVerticalBlock"],
[data-testid="stChatMessageContainer"],
.main .block-container {
    background: var(--bg) !important;
}

/* Kill ALL default Streamlit chat message backgrounds */
.stChatMessage,
[data-testid="stChatMessage"],
div[class*="stChatMessage"] {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
    margin: 0 0 0.5rem 0 !important;
}

/* Our custom message rows */
.msg-row {
    display: flex;
    flex-direction: column;
    padding: 0.875rem 1rem;
    border-radius: var(--r);
    margin-bottom: 0.5rem;
    border: 1px solid var(--border);
    background: var(--surface);
    position: relative;
}
.msg-row:hover { border-color: var(--border-hi); }

.msg-meta {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 0.5rem;
}
.msg-role {
    font-family: var(--mono);
    font-size: 0.6rem;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--fg-3);
}
.msg-role.user { color: var(--amber); }
.msg-role.assistant { color: var(--green); }

.msg-body {
    font-family: var(--sans);
    font-size: 0.875rem;
    color: var(--fg);
    line-height: 1.65;
}

/* ── COMPLETELY HIDE AVATARS ───────────────────────── */
[data-testid="chatAvatarIcon-user"],
[data-testid="chatAvatarIcon-assistant"],
.stChatMessage > div:first-child,
[data-testid="stChatMessage"] > div:first-child {
    display: none !important;
    width: 0 !important;
    min-width: 0 !important;
    height: 0 !important;
    overflow: hidden !important;
    visibility: hidden !important;
    position: absolute !important;
    pointer-events: none !important;
}

[data-testid="stChatMessageContent"],
.stChatMessage > div:last-child,
[data-testid="stChatMessage"] > div:last-child {
    width: 100% !important;
    flex: 1 !important;
    padding: 0 !important;
    margin: 0 !important;
    /* CRITICAL: force dark background on message content */
    background: var(--surface) !important;
    color: var(--fg) !important;
}

/* Force dark on ALL children of chat messages */
[data-testid="stChatMessageContent"] *,
[data-testid="stChatMessageContent"] p,
[data-testid="stChatMessageContent"] div,
[data-testid="stChatMessageContent"] span {
    background: transparent !important;
    color: var(--fg) !important;
    font-family: var(--sans) !important;
}

/* ── AGENT BADGES ──────────────────────────────────── */
.badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 0.2rem 0.6rem;
    border-radius: 2px;
    font-family: var(--mono);
    font-size: 0.58rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-top: 0.625rem;
}
.badge::before {
    content: '';
    width: 4px; height: 4px;
    border-radius: 50%;
    background: currentColor;
    opacity: 0.8;
}
.b-greeting  { background: var(--purple-dim); color: var(--purple); border: 1px solid rgba(124,92,191,0.2); }
.b-research  { background: var(--blue-dim);   color: var(--blue);   border: 1px solid rgba(74,127,165,0.2); }
.b-database  { background: var(--green-dim);  color: var(--green);  border: 1px solid rgba(61,153,112,0.2); }
.b-email     { background: var(--amber-dim);  color: var(--amber);  border: 1px solid rgba(212,146,42,0.2); }
.b-celebration { background: var(--pink-dim); color: var(--pink);   border: 1px solid rgba(176,80,128,0.2); }

/* ── THINKING STATUS ───────────────────────────────── */
[data-testid="stStatusWidget"],
[data-testid="stStatusWidget"] > div {
    background: var(--surface) !important;
    color: var(--fg) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--r) !important;
    font-family: var(--mono) !important;
    font-size: 0.75rem !important;
}
[data-testid="stStatusWidget"] * {
    background: transparent !important;
    color: var(--fg-2) !important;
    font-family: var(--mono) !important;
}

/* ── SPINNER ───────────────────────────────────────── */
.stSpinner > div {
    border-top-color: var(--amber) !important;
    border-right-color: var(--amber) !important;
    border-bottom-color: transparent !important;
    border-left-color: transparent !important;
}

/* ── ALERTS / INFO ─────────────────────────────────── */
[data-testid="stNotification"], div.stAlert {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--r) !important;
    color: var(--fg-2) !important;
    font-family: var(--mono) !important;
    font-size: 0.75rem !important;
}

/* ── CODE ──────────────────────────────────────────── */
code {
    background: var(--panel) !important;
    color: var(--amber) !important;
    padding: 0.1rem 0.35rem !important;
    border-radius: 3px !important;
    border: 1px solid var(--border) !important;
    font-family: var(--mono) !important;
    font-size: 0.85em !important;
}
pre { background: var(--panel) !important; border: 1px solid var(--border) !important; border-radius: var(--r) !important; padding: 0.875rem !important; }
pre code { color: var(--fg) !important; background: transparent !important; border: none !important; padding: 0 !important; }

/* ── CHAT INPUT ────────────────────────────────────── */
/* Remove ALL default Streamlit stBottom chrome */
[data-testid="stBottom"] {
    background: var(--bg) !important;
    border-top: 1px solid var(--border) !important;
    padding: 0.75rem 1.5rem 1rem !important;
    position: sticky !important;
    bottom: 0 !important;
    left: 0 !important;
    right: 0 !important;
    z-index: 100 !important;
}
[data-testid="stBottom"] > div {
    background: transparent !important;
    padding: 0 !important;
    margin: 0 !important;
    max-width: 100% !important;
}

/* The testid wrapper */
[data-testid="stChatInput"] {
    background: transparent !important;
    padding: 0 !important;
    margin: 0 !important;
    width: 100% !important;
    display: block !important;
}
[data-testid="stChatInput"] > div {
    background: transparent !important;
    padding: 0 !important;
    margin: 0 !important;
    width: 100% !important;
}

/* The BaseWeb textarea root — this is what actually wraps */
[data-baseweb="textarea"],
[data-baseweb="base-input"] {
    background: var(--panel) !important;
    border: 1px solid var(--border-hi) !important;
    border-radius: var(--r) !important;
    width: 100% !important;
    display: flex !important;
    align-items: center !important;
    overflow: hidden !important;
    min-height: 48px !important;
    max-height: 48px !important;
}
[data-baseweb="textarea"]:focus-within,
[data-baseweb="base-input"]:focus-within {
    border-color: var(--amber) !important;
    box-shadow: 0 0 0 2px var(--amber-glow) !important;
}

/* Kill the BaseWeb resize handle */
[data-baseweb="textarea"]::after,
[data-baseweb="base-input"]::after { display: none !important; }

/* THE actual textarea element */
.stChatInput textarea,
[data-testid="stChatInput"] textarea,
[data-baseweb="textarea"] textarea,
[data-baseweb="base-input"] textarea,
textarea[aria-label*="message"],
textarea[data-testid*="chat"] {
    background: transparent !important;
    color: var(--fg) !important;
    border: none !important;
    outline: none !important;
    box-shadow: none !important;
    font-family: var(--sans) !important;
    font-size: 0.875rem !important;
    padding: 0.75rem 1rem !important;
    line-height: 1.5 !important;
    resize: none !important;
    overflow: hidden !important;
    /* Explicit single-row height */
    height: 48px !important;
    min-height: 48px !important;
    max-height: 48px !important;
    width: 100% !important;
    box-sizing: border-box !important;
    display: block !important;
}
textarea::placeholder,
.stChatInput textarea::placeholder,
[data-testid="stChatInput"] textarea::placeholder {
    color: var(--fg-3) !important;
    font-style: normal !important;
}

/* Submit button */
[data-testid="stChatInput"] button {
    background: var(--amber) !important;
    color: #0a0a0b !important;
    border: none !important;
    border-radius: 3px !important;
    cursor: pointer !important;
    height: 34px !important;
    width: 34px !important;
    min-width: 34px !important;
    font-weight: 600 !important;
    transition: background 0.15s ease !important;
    flex-shrink: 0 !important;
    margin-right: 6px !important;
}
[data-testid="stChatInput"] button:hover {
    background: #e8a030 !important;
    transform: none !important;
    box-shadow: none !important;
}

/* The .stChatInput class Streamlit adds */
.stChatInput {
    background: var(--panel) !important;
    border: 1px solid var(--border-hi) !important;
    border-radius: var(--r) !important;
    overflow: hidden !important;
    display: flex !important;
    align-items: center !important;
    min-height: 48px !important;
    max-height: 48px !important;
    width: 100% !important;
}
.stChatInput:focus-within {
    border-color: var(--amber) !important;
    box-shadow: 0 0 0 2px var(--amber-glow) !important;
}

/* ── MARKDOWN in messages ──────────────────────────── */
.stMarkdown, .stMarkdown * { background: transparent !important; color: var(--fg) !important; font-family: var(--sans) !important; }

/* ── MISC BACKGROUND FIXES ─────────────────────────── */
section[tabindex="0"], .element-container, div[class*="st-"] { background: transparent !important; }
</style>
""", unsafe_allow_html=True)

BACKEND_API_URL = os.getenv('BACKEND_API_URL', 'http://localhost:8000')

# ── SESSION STATE ────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "orchestrator" not in st.session_state:
    st.session_state.orchestrator = get_semantic_kernel_orchestrator()
if "last_processed_message" not in st.session_state:
    st.session_state.last_processed_message = None

# ── HELPERS ──────────────────────────────────────────────────────────────────
BADGE_MAP = {
    "greeting":    ("b-greeting",    "Greeting"),
    "research":    ("b-research",    "Research"),
    "database":    ("b-database",    "Database"),
    "email":       ("b-email",       "Email"),
    "celebration": ("b-celebration", "Celebration"),
}

AGENT_INFO = {
    "greeting":    {"name": "Greeting Agent",           "desc": "Handles greetings and casual conversation"},
    "research":    {"name": "Researcher Agent",          "desc": "Provides research and information retrieval"},
    "database":    {"name": "Database Agent",            "desc": "Accesses company data and records"},
    "email":       {"name": "Email Writer Agent",        "desc": "Composes professional emails"},
    "celebration": {"name": "Event & Celebration Agent", "desc": "Creates celebration posts and messages"},
}

def badge_html(intent: str) -> str:
    cls, label = BADGE_MAP.get(intent, ("b-research", intent.capitalize()))
    return f'<span class="badge {cls}">{label}</span>'

async def process_query(query: str) -> Dict[str, Any]:
    result = await st.session_state.orchestrator.process_request(user_query=query)
    return {
        "intent":   result.get("intent", "unknown"),
        "response": result.get("response", ""),
        "success":  result.get("success", False),
    }

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("Multi-Agent System")
    st.markdown("---")

    # Active agent card
    st.subheader("Active Agent")
    last_assistant = next(
        (m for m in reversed(st.session_state.messages) if m.get("role") == "assistant"),
        None
    )
    if last_assistant:
        intent = last_assistant.get("agent", "unknown")
        info = AGENT_INFO.get(intent, {"name": "Agent", "desc": ""})
        st.markdown(f"""
        <div class="agent-card">
            <div class="status-dot">Online</div>
            <div class="label">Current agent</div>
            <div class="name">{info['name']}</div>
            <div class="desc">{info['desc']}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown('<div class="waiting-state"><p>No agent active</p><p style="margin-top:4px;font-size:0.6rem;">Send a message to begin</p></div>', unsafe_allow_html=True)

    st.markdown("---")

    # Stats
    if st.session_state.messages:
        st.subheader("Statistics")
        counts: Dict[str, int] = {}
        for m in st.session_state.messages:
            if m.get("role") == "assistant":
                k = m.get("agent", "unknown")
                counts[k] = counts.get(k, 0) + 1
        for k, v in sorted(counts.items()):
            st.metric(k.capitalize(), v)
        st.markdown("---")

    # Quick-access buttons
    st.subheader("Agents")
    examples = [
        ("Greeting",           "Hello there!"),
        ("Research",           "Tell me about AI"),
        ("Database",           "Who is John Doe?"),
        ("Email",              "Write an email for meeting request"),
        ("Event / Celebration","Write a 5-year anniversary message for John Doe"),
    ]
    for label, query in examples:
        if st.button(label, key=f"ex_{label}", use_container_width=True):
            st.session_state.temp_query = query
            st.rerun()

    st.markdown("---")
    if st.button("Clear Chat", key="clear", use_container_width=True, type="secondary"):
        st.session_state.messages = []
        st.rerun()

# ── MAIN CHAT ─────────────────────────────────────────────────────────────────
chat_area = st.container()

with chat_area:
    if not st.session_state.messages:
        st.info("Multi-Agent System ready — send a message to begin.")
    else:
        for msg in st.session_state.messages:
            role    = msg.get("role", "user")
            content = msg.get("content", "")
            agent   = msg.get("agent")

            # Render using native chat_message but override visuals via CSS
            with st.chat_message(role):
                # Role label + content rendered as pure markdown HTML
                role_label = "YOU" if role == "user" else "AGENT"
                role_class = role  # "user" or "assistant"
                st.markdown(
                    f'<div class="msg-row">'
                    f'  <div class="msg-meta"><span class="msg-role {role_class}">{role_label}</span></div>'
                    f'  <div class="msg-body">{content}</div>'
                    + (badge_html(agent) if agent and role == "assistant" else "")
                    + '</div>',
                    unsafe_allow_html=True
                )

st.markdown("---")

# ── INPUT ─────────────────────────────────────────────────────────────────────
user_input = st.chat_input("Ask anything...", key="chat_input")

if user_input and user_input != st.session_state.last_processed_message:
    st.session_state.last_processed_message = user_input
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("user"):
        st.markdown(
            f'<div class="msg-row">'
            f'  <div class="msg-meta"><span class="msg-role user">YOU</span></div>'
            f'  <div class="msg-body">{user_input}</div>'
            f'</div>',
            unsafe_allow_html=True
        )

    placeholder = st.empty()
    with placeholder.status("Processing...", expanded=False):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(process_query(user_input))
            loop.close()
        except Exception as e:
            result = {"intent": "error", "response": f"Error: {str(e)}", "success": False}

    st.session_state.messages.append({
        "role":    "assistant",
        "content": result.get("response", "No response"),
        "agent":   result.get("intent", "unknown"),
    })
    placeholder.empty()
    st.rerun()

if __name__ == "__main__":
    pass
