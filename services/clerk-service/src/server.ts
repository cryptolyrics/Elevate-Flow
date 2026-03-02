import express, { NextFunction, Request, Response } from "express";
import { ClerkConfig } from "./config";
import { Poller } from "./poller";
import { loadState } from "./state";

function requireMcKey(req: Request, res: Response, next: NextFunction): void {
  const expected = process.env.MC_API_KEY;
  if (!expected) {
    res.status(503).json({ ok: false, error: "MC_API_KEY not configured" });
    return;
  }

  const incoming = req.header("x-mc-key");
  if (!incoming || incoming !== expected) {
    res.status(401).json({ ok: false, error: "unauthorized" });
    return;
  }

  next();
}

export function buildApp(config: ClerkConfig, poller: Poller) {
  const app = express();

  app.get("/health", (_req, res) => {
    res.set("cache-control", "no-store");
    res.json({ ok: true, status: "healthy", ts: new Date().toISOString() });
  });

  app.get("/v1/status", requireMcKey, (_req, res) => {
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

  app.get("/v1/jobs", requireMcKey, (_req, res) => {
    res.set("cache-control", "no-store");
    res.json({ ok: true, jobs: config.jobs });
  });

  app.get("/status", requireMcKey, (_req, res) => {
    res.redirect(307, "/v1/status");
  });

  return app;
}
