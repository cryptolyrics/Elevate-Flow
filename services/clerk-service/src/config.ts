import fs from "fs";
import path from "path";
import { assertAgentId, assertJobId, isRelativeSafePath } from "./ids";

export type FetchMode = "cli";

export interface JobConfig {
  jobId: string;
  agentId: string;
  workspace: string;
}

export interface ClerkConfig {
  workspaceRoot: string;
  reportWorkspace: string;
  pollIntervalSec: number;
  fetchMode: FetchMode;
  openClawBin: string;
  openClawTimeoutMs: number;
  host: string;
  port: number;
  jobs: JobConfig[];
}

function toAbsolute(input: string): string {
  return path.resolve(input);
}

export function getConfigPath(): string {
  return process.env.CLERK_CONFIG || path.join(process.cwd(), "config.json");
}

export function loadConfig(configPath: string): ClerkConfig {
  const raw = fs.readFileSync(configPath, "utf8");
  const parsed = JSON.parse(raw) as Partial<ClerkConfig>;

  if (!parsed.workspaceRoot) {
    throw new Error("workspaceRoot is required");
  }
  if (!parsed.reportWorkspace) {
    throw new Error("reportWorkspace is required");
  }
  if (!parsed.jobs || parsed.jobs.length === 0) {
    throw new Error("jobs is required and must be non-empty");
  }

  const cfg: ClerkConfig = {
    workspaceRoot: toAbsolute(parsed.workspaceRoot),
    reportWorkspace: toAbsolute(parsed.reportWorkspace),
    pollIntervalSec: parsed.pollIntervalSec || 120,
    fetchMode: parsed.fetchMode || "cli",
    openClawBin: parsed.openClawBin || "openclaw",
    openClawTimeoutMs: parsed.openClawTimeoutMs || 15000,
    host: parsed.host || "127.0.0.1",
    port: parsed.port || 3008,
    jobs: parsed.jobs,
  };

  if (cfg.pollIntervalSec < 15) {
    throw new Error("pollIntervalSec must be >= 15");
  }
  if (cfg.openClawTimeoutMs < 1000) {
    throw new Error("openClawTimeoutMs must be >= 1000");
  }
  if (cfg.host !== "127.0.0.1") {
    throw new Error("host must be 127.0.0.1 for local security");
  }

  const seen = new Set<string>();
  for (const job of cfg.jobs) {
    assertJobId(job.jobId);
    assertAgentId(job.agentId);
    if (!isRelativeSafePath(job.workspace)) {
      throw new Error(`Invalid job.workspace: ${job.workspace}`);
    }
    if (seen.has(job.jobId)) {
      throw new Error(`Duplicate jobId: ${job.jobId}`);
    }
    seen.add(job.jobId);
  }

  return cfg;
}
