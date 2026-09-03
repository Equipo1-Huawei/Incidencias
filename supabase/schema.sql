-- Supabase schema for Autonomous Triage & Active Defense System
-- Run this in Supabase SQL Editor or via supabase CLI migration

-- ============================================================
-- 1. INCIDENT HISTORY
-- ============================================================
CREATE TABLE IF NOT EXISTS incident_history (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    incident_id     TEXT NOT NULL,
    incident_type   TEXT,
    component       TEXT NOT NULL,
    severity        TEXT NOT NULL DEFAULT 'P2',
    source          TEXT,
    description     TEXT,
    is_security_event BOOLEAN NOT NULL DEFAULT FALSE,
    risk_score      DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    root_cause_hypothesis TEXT,
    escalation_team TEXT,
    mitigation_commands TEXT,
    diagnostics_checklist JSONB DEFAULT '[]'::jsonb,
    diagnostic_steps JSONB DEFAULT '[]'::jsonb,
    mttd_minutes    DOUBLE PRECISION,
    mttr_minutes    DOUBLE PRECISION,
    resolution      TEXT,
    timestamp       TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_incident_component_ts
    ON incident_history (component, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_incident_severity
    ON incident_history (severity);
CREATE INDEX IF NOT EXISTS idx_incident_security
    ON incident_history (is_security_event) WHERE is_security_event = TRUE;
CREATE INDEX IF NOT EXISTS idx_incident_risk
    ON incident_history (risk_score DESC);

-- ============================================================
-- 2. KNOWLEDGE BASE
-- ============================================================
CREATE TABLE IF NOT EXISTS knowledge_base (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    incident_type   TEXT NOT NULL,
    component       TEXT NOT NULL,
    symptom         TEXT,
    root_cause      TEXT,
    resolution_steps JSONB DEFAULT '[]'::jsonb,
    confidence      DOUBLE PRECISION NOT NULL DEFAULT 0.5,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_kb_component
    ON knowledge_base (component);
CREATE INDEX IF NOT EXISTS idx_kb_type
    ON knowledge_base (incident_type);

-- Full-text search index for knowledge base
CREATE INDEX IF NOT EXISTS idx_kb_fts
    ON knowledge_base USING gin (
        to_tsvector('english', coalesce(incident_type, '') || ' ' || coalesce(symptom, '') || ' ' || coalesce(root_cause, ''))
    );

-- ============================================================
-- 3. AUDIT LOG (Guardrail decisions, auth events, etc.)
-- ============================================================
CREATE TABLE IF NOT EXISTS audit_log (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type      TEXT NOT NULL,
    incident_id     TEXT,
    actor           TEXT,
    detail          JSONB DEFAULT '{}'::jsonb,
    approved        BOOLEAN,
    reason          TEXT,
    timestamp       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_audit_incident
    ON audit_log (incident_id);
CREATE INDEX IF NOT EXISTS idx_audit_type_ts
    ON audit_log (event_type, timestamp DESC);

-- ============================================================
-- 4. ROW LEVEL SECURITY (RLS)
-- ============================================================
ALTER TABLE incident_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE knowledge_base ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY;

-- Service role bypasses RLS (used by backend)
-- Anon/authenticated roles get read-only on knowledge_base
CREATE POLICY "kb_read_all" ON knowledge_base
    FOR SELECT TO anon, authenticated USING (true);

-- Authenticated users can read incident_history
CREATE POLICY "incidents_read_auth" ON incident_history
    FOR SELECT TO authenticated USING (true);

-- Authenticated users can read audit_log
CREATE POLICY "audit_read_auth" ON audit_log
    FOR SELECT TO authenticated USING (true);

-- ============================================================
-- 5. SEED DATA
-- ============================================================
INSERT INTO knowledge_base (incident_type, component, symptom, root_cause, resolution_steps, confidence)
VALUES
    ('Database Connectivity', 'database', 'MongoNetworkError or connection refused',
     'Database firewall rule blocking IP or egress network partition',
     '["1. Verify database Network Access whitelist", "2. Inspect firewall/iptables rules", "3. Test TCP connection", "4. Verify application connection string credentials"]'::jsonb,
     0.95),
    ('Memory Pressure', 'frontend', 'OOM killer triggered, container restarts',
     'Process memory allocation exceeds container limits (512M cgroup limit)',
     '["1. Check container memory usage: docker stats", "2. Review heap profile and recent deployments", "3. Increase memory limit if required", "4. Restart container"]'::jsonb,
     0.90),
    ('Security Alert', 'auth', 'SQL Injection attempt detected in login parameters',
     'Malicious payload detected from external IP attempting SQL injection',
     '["1. Block offending source IP in firewall/Security Group", "2. Enable WAF strict filtering rules", "3. Notify SOC and initiate credential audit"]'::jsonb,
     0.99)
ON CONFLICT DO NOTHING;

INSERT INTO incident_history (incident_id, incident_type, component, severity, mttd_minutes, mttr_minutes, resolution, timestamp)
VALUES
    ('hist-001', 'Database Connectivity', 'database', 'P1', 2.5, 14.0, 'Restored egress network rule', now() - interval '2 days'),
    ('hist-002', 'Memory Pressure', 'frontend', 'P2', 4.0, 20.0, 'Cleared memory leak and restarted service', now() - interval '5 days'),
    ('hist-003', 'High Latency', 'network', 'P3', 8.0, 35.0, 'Scaled container instances', now() - interval '10 days')
ON CONFLICT DO NOTHING;
