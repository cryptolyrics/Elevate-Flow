export const AGENT_ID_RE = /^[a-z][a-z0-9-]{1,31}$/;
export const JOB_ID_RE = /^[a-z0-9][a-z0-9._-]{2,63}$/;
export const RUN_ID_RE = /^[A-Za-z0-9._-]{3,128}$/;

function assertRegex(value: string, regex: RegExp, label: string): void {
  if (!regex.test(value)) {
    throw new Error(`Invalid ${label}: ${value}`);
  }
}

export function assertAgentId(agentId: string): void {
  assertRegex(agentId, AGENT_ID_RE, "agentId");
}

export function assertJobId(jobId: string): void {
  assertRegex(jobId, JOB_ID_RE, "jobId");
}

export function assertRunId(runId: string): void {
  assertRegex(runId, RUN_ID_RE, "runId");
}

export function isRelativeSafePath(value: string): boolean {
  if (!value || value.includes("\0")) {
    return false;
  }
  if (value.startsWith("/") || value.startsWith("\\")) {
    return false;
  }
  const normalized = value.replace(/\\/g, "/");
  if (normalized === "." || normalized === "..") {
    return false;
  }
  return !normalized.split("/").includes("..");
}
