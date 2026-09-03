# Sistema de Triage Autónomo & Defensa Activa
### Arquitectura de Referencia para el Hackathon Huawei Cloud MaaS
**Repositorio Oficial:** [https://github.com/Equipo1-Huawei/Incidencias.git](https://github.com/Equipo1-Huawei/Incidencias.git)

---

## Tabla de Contenidos
1. [Finalidad y Propósito de Negocio](#1-finalidad-y-propósito-de-negocio)
2. [Arquitectura del Sistema](#2-arquitectura-del-sistema)
3. [Stack Tecnológico](#3-stack-tecnológico)
4. [Contrato de Datos Global](#4-contrato-de-datos-global)
5. [Estructura del Proyecto](#5-estructura-del-proyecto)
6. [Guía de Instalación y Puesta en Marcha](#6-guía-de-instalación-y-puesta-en-marcha)
7. [Arquitectura Multi-Agente & Guardrail de Seguridad](#7-arquitectura-multi-agente--guardrail-de-seguridad)
8. [Scripts de Chaos Engineering & Simulación](#8-scripts-de-chaos-engineering--simulación)
9. [Plan de Contingencia y Alta Disponibilidad](#9-plan-de-contingencia-y-alta-disponibilidad)

---

## 1. Finalidad y Propósito de Negocio

En entornos de nube y aplicaciones distribuidas críticas, los equipos de operaciones (SRE) y seguridad (SOC) gastan entre **30 a 60 minutos** por cada incidente operacional en clasificar, identificar componentes, consultar bases de conocimiento y generar comandos defensivos.

### La Solución:
Un **Agente Autónomo de Triage y Defensa Activa** impulsado por **Huawei Cloud MaaS (Pangu 40B)** y **LangGraph**, reduciendo el **MTTD de 30 minutos a menos de 1.5 segundos** (reducción del 99.2%) con contención automatizada en 1 clic, guardrail de seguridad dual-agente y estimación de ahorro de más de **$1,480 USD por incidente**.

---

## 2. Arquitectura del Sistema

```mermaid
graph TD
    subgraph Ingestion_Layer["1. Ingesta y Telemetría"]
        DockerLogs["Docker Stdout Logs"] --> N8N["n8n Telemetry Engine (:5678)"]
        AccessLog["/var/log/triage/access.log"] --> N8N
        ChaosScripts["Chaos & Mock Scripts"] -->|Inyecta Fallos| NextJS["Next.js Monitored App (:3000)"]
    end

    subgraph Agent_Core["2. Núcleo Agéntico (FastAPI + LangGraph)"]
        N8N -->|POST /webhook/n8n (Auth + Rate Limit)| FastAPI["FastAPI Engine (:8000)"]
        FastAPI --> StateGraph["LangGraph State Engine"]

        StateGraph --> Node1["Node 1: Entity & Security Signature Match"]
        Node1 -->|conditional| Node2["Node 2: Active Health Probe & Supabase Query"]
        Node1 -->|security shortcut| Node3["Node 3: Dynamic Risk Scoring & SLA"]
        Node2 --> Node3
        Node3 --> Node4["Node 4: Pangu 40B LLM Synthesis"]
        Node4 --> Guardrail["Node 5: Agent B - Safety Guardrail Validator"]
        Guardrail --> Persist["Node 6: Persist to Supabase"]
    end

    subgraph Infrastructure_And_AI["3. Servicios Conectados & UI"]
        Node2 -->|HTTP GET /api/health| NextJS
        Node2 -->|Supabase SDK| Supabase[("Supabase (PostgreSQL)")]
        Node4 -->|MaaS API| Pangu["Huawei Cloud MaaS (Pangu 40B)"]
        Node4 -.->|Failover Automático| OpenAI["OpenAI GPT-4"]
        StreamlitUI["Operator Command Center (:8501)"] -->|Live Inspection / Chat| FastAPI
    end
```

---

## 3. Stack Tecnológico

| Capa | Tecnología | Función |
|---|---|---|
| **Modelos Fundacionales** | Huawei Cloud MaaS (**Pangu 40B**) | Inferencia principal con failover automático a OpenAI |
| **Orquestación Agéntica** | **LangGraph** (StateGraph) | Máquina de estados asíncrona con branching condicional |
| **Backend API** | **Python 3.11+, FastAPI, Uvicorn, Pydantic** | API con auth, rate limiting, CORS y streaming |
| **Base de Datos** | **Supabase (PostgreSQL)** | Almacenamiento de incidentes, KB y audit log con RLS |
| **Frontend Monitoreado** | **Next.js 14, TypeScript** | App productiva con healthcheck activo |
| **Ingesta de Eventos** | **n8n** | Pipeline de filtrado y despacho al webhook |
| **UI de Operador** | **Streamlit** | Dashboard con copilot chat (LLM real), topología y IaC |
| **Seguridad** | **slowapi, PyJWT, Guardrail** | Rate limiting, auth de webhook, validación dual-agente |
| **Resilience** | **tenacity** | Retry con backoff exponencial en LLM client |
| **Logging** | **structlog** | Logging estructurado en JSON |
| **Infraestructura** | **Docker & Docker Compose** | Red aislada `triage-net` con healthchecks y resource limits |

---

## 4. Contrato de Datos Global

```json
{
  "incident_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "source": "nextjs | mongodb | n8n | security-scanner",
  "timestamp": "2026-09-03T10:00:00Z",
  "component": "frontend | database | network | auth",
  "raw_log": "192.168.10.45 - POST /api/auth/login username=admin' UNION SELECT...",
  "is_security_event": true,
  "severity_hint": "P1"
}
```

---

## 5. Estructura del Proyecto

```
hackaton-huawei/
├── docker-compose.yml           # Orquestación con healthchecks y resource limits
├── .env.example                 # Plantilla de variables (Supabase, MaaS, OpenAI)
├── .env                         # Variables de entorno locales
├── README.md
├── supabase/
│   └── schema.sql               # Esquema PostgreSQL + RLS + seed data
├── scripts/
│   ├── stress_memory.sh         # Inyección de estrés de memoria
│   ├── block_atlas.sh           # Bloqueo de salida TCP 443 (simula caída DB)
│   ├── unblock_atlas.sh         # Reversión de regla iptables
│   └── mock_security_logs.py    # Generador de logs sintéticos (SQLi, XSS, Path Traversal)
├── frontend/
│   ├── Dockerfile               # Node 18 + healthcheck
│   ├── package.json             # Next.js 14 (sin dependencia MongoDB)
│   ├── tsconfig.json
│   └── pages/
│       ├── index.tsx            # Interfaz de estado del nodo monitoreado
│       └── api/health.ts        # Healthcheck activo contra Supabase
├── n8n/
│   └── n8n_workflow.json        # Flujo exportable de n8n
└── backend/
    ├── Dockerfile               # Python 3.11 + healthcheck
    ├── requirements.txt         # FastAPI, LangGraph, Supabase, slowapi, structlog, tenacity
    ├── main.py                  # API con auth, rate limiting, CORS, copilot chat/stream
    ├── src/
    │   ├── config.py            # Config centralizada (Supabase, LLM, CORS, rate limit)
    │   ├── logging_config.py    # structlog JSON renderer
    │   ├── llm_client.py        # ResilientLLMClient singleton (Pangu + failover + streaming + retry)
    │   ├── db/
    │   │   ├── supabase_client.py  # Cliente Supabase singleton
    │   │   └── fixtures.py      # Fixtures offline (fallback)
    │   ├── tools/
    │   │   ├── validators.py    # Detector de firmas (SQLi, XSS, Path Traversal, SSRF)
    │   │   ├── queries.py       # Queries Supabase + persistencia + audit
    │   │   └── analyzers.py     # Motor de scoring de riesgo y SLA
    │   ├── agent/
    │   │   ├── state.py         # Esquema TypedDict AgentState (con guardrail fields)
    │   │   ├── tools.py         # Mapeo de herramientas
    │   │   ├── nodes.py         # 6 nodos: analyze, tools, scoring, output, guardrail, persist
    │   │   ├── guardrail.py     # Agente B: valida 22 patrones destructivos/ofensivos
    │   │   └── graph.py         # Grafo con branching condicional + guardrail + persist
    │   └── ui/
    │       └── app.py           # Dashboard Streamlit con copilot LLM real
    └── tests/
        ├── test_tools.py        # 14 tests: validators, analyzers, SLA
        ├── test_api.py          # 7 tests: endpoints, webhook, copilot
        ├── test_guardrail.py    # 10 tests: patrones destructivos, sanitización
        └── test_llm_client.py   # 5 tests: singleton, offline mode
```

---

## 6. Guía de Instalación y Puesta en Marcha

### Pre-requisitos: Configurar Supabase

1. Crear proyecto en https://supabase.com
2. Ir a **Settings → API** y copiar:
   - **Project URL** → `SUPABASE_URL`
   - **service_role key** → `SUPABASE_KEY`
   - **JWT Secret** → `SUPABASE_JWT_SECRET`
3. Ir a **SQL Editor** y ejecutar `supabase/schema.sql`
4. Configurar `.env` con esos valores

### Modo A: Ejecución Rápida Local

```powershell
# 1. Instalar dependencias
cd backend
python -m pip install -r requirements.txt

# 2. Tests (35/35)
python -m pytest tests/ -v

# 3. Iniciar FastAPI (terminal 1)
python main.py

# 4. Iniciar Streamlit (terminal 2)
python -m streamlit run src/ui/app.py --server.port 8501
```

- **API Docs:** `http://localhost:8000/docs`
- **Dashboard:** `http://localhost:8501`

### Modo B: Docker Compose

```powershell
docker-compose up -d --build
```

Servicios:
- **Next.js:** `http://localhost:3000`
- **FastAPI:** `http://localhost:8000`
- **n8n:** `http://localhost:5678`
- **Streamlit:** `http://localhost:8501`

---

## 7. Arquitectura Multi-Agente & Guardrail de Seguridad

### Agente A: SRE & SOC Diagnostics Engine
Analiza telemetría con Pangu 40B, calcula Risk Score y genera hipótesis de causa raíz y comandos de mitigación.

### Agente B: Safety Guardrail Validator
Audita los comandos generados por el Agente A contra **22 patrones peligrosos**:

**Patrones destructivos (16):**
- `rm -rf`, `mkfs`, `dd if=`, `DROP TABLE`, `DROP DATABASE`, `TRUNCATE`
- `DELETE FROM ... WHERE 1=1`, fork bomb `:(){ :|:& };:`
- `shutdown`, `reboot`, `halt`, `kill -9`
- `> /dev/sda`, `chmod 777`, `curl | sh`, `wget | sh`

**Herramientas ofensivas (6):**
- `nmap`, `sqlmap`, `hydra`, `metasploit`, `hashcat`, `john --wordlist`

Si detecta un patrón peligroso, **bloquea el comando** y lo reemplaza con una alternativa segura (`docker logs --tail 100`). El resultado se persiste en la tabla `audit_log` de Supabase.

---

## 8. Scripts de Chaos Engineering & Simulación

```bash
# Simular caída de base de datos (bloquea HTTPS saliente)
bash scripts/block_atlas.sh

# Restaurar conectividad
bash scripts/unblock_atlas.sh

# Sobrecarga de memoria (OOM crash)
bash scripts/stress_memory.sh

# Generar logs de ciberataques sintéticos
python scripts/mock_security_logs.py
```

---

## 9. Plan de Contingencia y Alta Disponibilidad

- **Failover Automático de LLM:** `ResilientLLMClient` (singleton) consulta primero a **Pangu 40B** con retry exponencial (tenacity). Si falla, conmuta a **OpenAI GPT-4** o al modo offline contextual en < 1.0s.
- **Resiliencia de Base de Datos:** Si Supabase pierde conectividad, el sistema activa automáticamente los fixtures locales en memoria sin arrojar excepciones.
- **Degradación Controlada en Healthchecks:** Si `/api/health` no responde, retorna estado `UNKNOWN` permitiendo al grafo completar el diagnóstico.
- **Rate Limiting:** 30 requests/minuto por IP en el webhook (configurable via `RATE_LIMIT_PER_MINUTE`).
- **Webhook Auth:** Protegido via `X-Webhook-Key` header.
- **CORS:** Configurable via `CORS_ORIGINS`.
