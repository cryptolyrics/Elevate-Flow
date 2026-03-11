import express from "express";
import { ClerkConfig } from "./config";
import { Poller } from "./poller";
import { loadState } from "./state";

type Req = any;
type Res = any;
type Next = any;

function requireMcKey(req: Req, res: Res, next: Next): void {
  const expected = process.env.MC_API_KEY;
  if (!expected) {
    res.status(503).json({ ok: false, error: "MC_API_KEY not configured" });
    return;
  }

  const incoming = req.get("x-mc-key");
  if (!incoming || incoming !== expected) {
    res.status(401).json({ ok: false, error: "unauthorized" });
    return;
  }

  next();
}

export function buildApp(config: ClerkConfig, poller: Poller): any {
  const app = express();

  app.get("/health", (_req: Req, res: Res) => {
    res.set("cache-control", "no-store");
    res.json({ ok: true, status: "healthy", ts: new Date().toISOString() });
  });

  app.get("/v1/status", requireMcKey, (_req: Req, res: Res) => {
    res.set("cache-control", "no-store");
    const state = loadState(config.workspaceRoot);
    res.json({
      ok: true,
      host: config.host,
      port: config.port,
      pollIntervalSec: config.pollIntervalSec,
      jobsConfigured: config.jobs.length,
      lastPollAt: state.lastPollAt || null,
      lastSummary: poller.getLastSummary(),
    });
  });

  app.get("/v1/jobs", requireMcKey, (_req: Req, res: Res) => {
    res.set("cache-control", "no-store");
    res.json({ ok: true, jobs: config.jobs });
  });

  app.get("/status", requireMcKey, (_req: Req, res: Res) => {
    res.redirect(307, "/v1/status");
  });

  return app;
}
