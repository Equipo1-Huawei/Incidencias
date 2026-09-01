import type { NextApiRequest, NextApiResponse } from 'next';
import { MongoClient } from 'mongodb';

interface HealthResponse {
  status: 'UP' | 'DOWN';
  component: 'nextjs' | 'database';
  timestamp: string;
  latency_ms?: number;
  error_code?: string | number;
  message?: string;
}

const uri = process.env.MONGODB_ATLAS_URI || '';
let cachedClient: MongoClient | null = null;

async function getMongoClient(): Promise<MongoClient> {
  if (!cachedClient) {
    if (!uri) {
      throw new Error('MONGODB_ATLAS_URI is not defined');
    }
    cachedClient = new MongoClient(uri, {
      serverSelectionTimeoutMS: 2000,
      connectTimeoutMS: 2000,
    });
    await cachedClient.connect();
  }
  return cachedClient;
}

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse<HealthResponse>
) {
  const startTime = Date.now();
  const timestamp = new Date().toISOString();

  try {
    const client = await getMongoClient();
    const db = client.db('triage_monitoring');
    const healthCollection = db.collection('health_probes');

    // Realiza operación de lectura/escritura real de prueba
    const testId = `probe_${Date.now()}`;
    await healthCollection.insertOne({ _id: testId as any, timestamp, status: 'PROBING' });
    await healthCollection.deleteOne({ _id: testId as any });

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
    
    // Log estructurado a stdout para ingesta de n8n
    console.error(JSON.stringify(structuredErrorLog));

    return res.status(503).json({
      status: 'DOWN',
      component: 'database',
      timestamp,
      latency_ms,
      error_code: errorCode,
      message: 'MongoDB Atlas healthcheck failed: ' + error.message,
    });
  }
}
