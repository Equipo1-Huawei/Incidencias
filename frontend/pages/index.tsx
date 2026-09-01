import React, { useState, useEffect } from 'react';

export default function Home() {
  const [health, setHealth] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);

  const checkHealth = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/health');
      const data = await res.json();
      setHealth(data);
    } catch (err: any) {
      setHealth({ status: 'DOWN', error_code: err.message });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    checkHealth();
  }, []);

  return (
    <div style={{ fontFamily: 'system-ui, sans-serif', padding: '2rem', maxWidth: '800px', margin: '0 auto' }}>
      <h1>🛡️ Production App (Monitored Node)</h1>
      <p>This service simulates the critical production frontend monitored by the Huawei Cloud MaaS Autonomous Triage Agent.</p>
      
      <div style={{
        marginTop: '1.5rem',
        padding: '1.5rem',
        borderRadius: '8px',
        border: '1px solid #ccc',
        backgroundColor: health?.status === 'UP' ? '#e6fffa' : '#ffe6e6'
      }}>
        <h2>Database Connection Status: <span style={{ color: health?.status === 'UP' ? '#0070f3' : '#e00' }}>{health?.status || 'CHECKING...'}</span></h2>
        <pre>{JSON.stringify(health, null, 2)}</pre>
        <button 
          onClick={checkHealth} 
          style={{ padding: '0.6rem 1.2rem', backgroundColor: '#0070f3', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer' }}
        >
          {loading ? 'Refreshing...' : 'Re-check Health'}
        </button>
      </div>
    </div>
  );
}
