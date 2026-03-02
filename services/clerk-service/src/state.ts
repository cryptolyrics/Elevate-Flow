import fs from "fs";
import { safeWriteFile, resolveInSandbox } from "./sandbox";

export interface JobState {
  lastProcessedRunId: string;
  lastProcessedAt: string;
}

export interface ClerkState {
  lastPollAt: string;
  jobs: Record<string, JobState>;
}

const STATE_PATH = ".clerk/state.json";

function defaultState(): ClerkState {
  return {
    lastPollAt: "",
    jobs: {},
  };
}

export function loadState(workspaceRoot: string): ClerkState {
  const abs = resolveInSandbox(workspaceRoot, STATE_PATH);
  if (!fs.existsSync(abs)) {
    return defaultState();
  }

  try {
    const parsed = JSON.parse(fs.readFileSync(abs, "utf8")) as ClerkState;
    return {
      lastPollAt: parsed.lastPollAt || "",
      jobs: parsed.jobs || {},
    };
  } catch {
    return defaultState();
  }
}

export function saveState(workspaceRoot: string, state: ClerkState): void {
  safeWriteFile(workspaceRoot, STATE_PATH, JSON.stringify(state, null, 2));
}

export function advanceState(workspaceRoot: string, jobId: string, runId: string): void {
  const state = loadState(workspaceRoot);
  state.jobs[jobId] = {
    lastProcessedRunId: runId,
    lastProcessedAt: new Date().toISOString(),
  };
  saveState(workspaceRoot, state);
}

export function touchPollState(workspaceRoot: string): void {
  const state = loadState(workspaceRoot);
  state.lastPollAt = new Date().toISOString();
  saveState(workspaceRoot, state);
}
