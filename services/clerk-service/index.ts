/**
 * Clerk Service - Main Entry Point (SECURE VERSION)
 * Express server with health/status/agents endpoints and poller
 * Security: 127.0.0.1 only, X-MC-KEY auth
 */

import express, { Request, Response, NextFunction } from 'express';
import { loadConfig, getConfigPath, ClerkConfig } from './config';
import { loadState } from './write/state';
import { OpenClawCLI } from './fetch/openclaw-cli';
import { Poller } from './poller';

const app = express();
let config: ClerkConfig;
let poller: Poller;

// Auth middleware - require X-MC-KEY if MC_API_KEY is set
function requireAuth(req: Request, res: Response, next: NextFunction) {
  const expected = process.env.MC_API_KEY || '';
  if (!expected) {
    console.warn('MC_API_KEY not set - auth disabled');
    return next();
  }
  
  const token = req.headers['x-mc-key'] as string;
  if (!token || token !== expected) {
    res.status(401).json({ ok: false, error: 'unauthorized' });
    return;
  }
  next();
}

// Get agents stub - can be expanded to read from filesystem
async function getAgents() {
  // TODO: read from filesystem or gateway status
  return [
    { id: 'main', name: 'JJ', model: 'MiniMax-M2.5', workspace: 'workspace-jj' }
  ];
}

// Health endpoint - public
app.get('/health', (req: Request, res: Response) => {
  res.set('cache-control', 'no-store');
  res.json({ ok: true, ts: Date.now() });
});

// Status endpoint - protected
app.get('/status', requireAuth, (req: Request, res: Response) => {
  res.set('cache-control', 'no-store');
  const state = loadState(config?.workspaceRoot);
  res.json({ 
    ok: true, 
    lastPollAt: state?.lastPollAt || null,
    jobsCount: config?.jobs?.length || 0
  });
});

// Agents endpoint - protected
app.get('/agents', requireAuth, async (req: Request, res: Response) => {
  res.set('cache-control', 'no-store');
  try {
    const agents = await getAgents();
    res.json({ ok: true, agents });
  } catch (e: any) {
    res.status(500).json({ ok: false, error: String(e?.message || e) });
  }
});

// Alias for /v1/agents - protected
app.get('/v1/agents', requireAuth, async (req: Request, res: Response) => {
  res.set('cache-control', 'no-store');
  try {
    const agents = await getAgents();
    res.json({ ok: true, agents });
  } catch (e: any) {
    res.status(500).json({ ok: false, error: String(e?.message || e) });
  }
});

async function main() {
  const configPath = getConfigPath();
  console.log(`Loading config from: ${configPath}`);
  
  config = loadConfig(configPath);
  console.log(`Loaded config for ${config.jobs.length} jobs`);
  
  const provider = new OpenClawCLI();
  poller = new Poller(config, provider);
  
  console.log('Running initial poll...');
  const results = await poller.poll();
  console.log(`Poll complete: ${results.reduce((s, r) => s + r.runsProcessed, 0)} runs processed`);
  
  poller.start();
  
  const port = parseInt(process.env.PORT || '3000');
  const host = '127.0.0.1';
  app.listen(port, host, () => {
    console.log(`Clerk service listening on http://${host}:${port}`);
  });
}

export { app, main };

if (require.main === module) {
  main().catch(err => {
    console.error('Fatal error:', err);
    process.exit(1);
  });
}
