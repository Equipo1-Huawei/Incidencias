# 🛡️ Sistema de Triage Autónomo & Defensa Activa
### Arquitectura de Referencia para Huawei Cloud MaaS Hackathon

> **Métrica Clave**: Reducción del MTTD (Mean Time to Detect) de **30 minutos a menos de 15 segundos**, diferenciando fallos de infraestructura de incidentes de ciberseguridad activos.

---

## 🏗️ Arquitectura del Stack

| Capa | Componente | Función |
|---|---|---|
| **Infraestructura** | Docker & Docker Compose | Red interna aislada `triage-net`, límites de memoria 512M en frontend |
| **Frontend Monitoreado** | Next.js (`:3000`) | Aplicación productiva con endpoint activo `/api/health` conectado a MongoDB Atlas |
| **Persistencia** | MongoDB Atlas (`motor`) | Base de conocimiento de remediaciones e histórico de incidentes |
| **Orquestación de Señales**| n8n (`:5678`) | Captura de logs de contenedores y `access.log`, filtrado regex y webhook |
| **Núcleo del Agente** | FastAPI + LangGraph (`:8000`) | Grafo asíncrono de razonamiento, validación y scoring de incidentes |
| **Dashboard Operador** | Streamlit (`:8501`) | Inspección visual en tiempo real de diagnósticos y métricas |
| **Modelos Fundacionales** | Huawei Cloud MaaS (Pangu 40B) | Razonamiento agéntico principal con failover automático a OpenAI |

---

## 🚀 Inicio Rápido

### 1. Configuración de Variables de Entorno
Copia la plantilla `.env.example` a `.env` y configura tus credenciales:
```bash
cp .env.example .env
```

### 2. Despliegue de Toda la Infraestructura con Docker Compose
```bash
docker-compose up -d --build
```
Servicios disponibles:
- **Next.js Frontend**: [http://localhost:3000](http://localhost:3000)
- **FastAPI Agent Webhook & Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **n8n Telemetry Orchestrator**: [http://localhost:5678](http://localhost:5678)
- **Streamlit Operator Dashboard**: [http://localhost:8501](http://localhost:8501)

### 3. Cargar Datos Iniciales (Seed de MongoDB Atlas)
```bash
cd backend
python -m src.db.fixtures
```

---

## 🧪 Pruebas de Chaos Engineering y Ciberseguridad

### Escenario A: Caída de Base de Datos (Egress Network Block)
Simula la pérdida de conectividad con MongoDB Atlas aplicando una regla en el contenedor:
```bash
bash scripts/block_atlas.sh
```
*Reversión:*
```bash
bash scripts/unblock_atlas.sh
```

### Escenario B: Stress de Memoria (OOM Controlled Crash)
Inyecta sobrecarga de memoria superior al límite de 512MB:
```bash
bash scripts/stress_memory.sh
```

### Escenario C: Detección de Ataques de Ciberseguridad
Genera logs sintéticos de inyecciones SQL, XSS y Path Traversal:
```bash
python scripts/mock_security_logs.py
```

---

## 🚦 Ejecución de Tests Automatizados

```bash
cd backend
pytest tests/ -v
```

---

## 📋 Plan de Contingencia en Vivo

- **Si MaaS presenta alta latencia o timeout**: El cliente `ResilientLLMClient` conmuta automáticamente a OpenAI o genera salida heurística segura en <1s.
- **Si falla la conexión a internet en la demo**: Ejecuta el dashboard de Streamlit de modo local contra los datos sintéticos precargados.
