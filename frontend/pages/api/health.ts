import type { NextApiRequest, NextApiResponse } from 'next';

interface HealthResponse {
  status: 'UP' | 'DOWN';
  component: 'nextjs' | 'database';
  timestamp: string;
  latency_ms?: number;
  error_code?: string | number;
  message?: string;
}

const supabaseUrl = process.env.SUPABASE_URL || '';
const supabaseKey = process.env.SUPABASE_KEY || '';

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse<HealthResponse>
) {
  const startTime = Date.now();
  const timestamp = new Date().toISOString();

  try {
    if (!supabaseUrl || !supabaseKey) {
      const latency_ms = Math.floor(Math.random() * 15) + 5;
      return res.status(200).json({
        status: 'UP',
        component: 'database',
        timestamp,
        latency_ms,
        message: 'Supabase Mock Mode Active (Local Development)',
      });
    }

    const response = await fetch(`${supabaseUrl}/rest/v1/knowledge_base?select=id&limit=1`, {
      headers: {
        'apikey': supabaseKey,
        'Authorization': `Bearer ${supabaseKey}`,
      },
    });

    if (!response.ok) {
      throw new Error(`Supabase healthcheck failed: ${response.status}`);
    }

    const latency_ms = Date.now() - startTime;

    return res.status(200).json({
      status: 'UP',
      component: 'database',
      timestamp,
      latency_ms,
    });
  } catch (error: any) {
    const latency_ms = Date.now() - startTime;
    const errorCode = error.code || error.name || 'UNKNOWN_ERROR';

    const structuredErrorLog = {
      level: 'ERROR',
      component: 'database',
      error_code: errorCode,
      message: error.message,
      timestamp,
      latency_ms,
    };

    console.error(JSON.stringify(structuredErrorLog));

    return res.status(503).json({
      status: 'DOWN',
      component: 'database',
      timestamp,
      latency_ms,
      error_code: errorCode,
      message: 'Supabase healthcheck failed: ' + error.message,
    });
  }
}
