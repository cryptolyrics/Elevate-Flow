import { spawn } from "child_process";
import { assertJobId, assertRunId } from "./ids";
import { FetchProvider, RunRecord, sortRunsOldestFirst } from "./provider";

function runCli(binary: string, args: string[], timeoutMs: number): Promise<string> {
  return new Promise((resolve, reject) => {
    const child = spawn(binary, args, {
      shell: false,
      stdio: ["ignore", "pipe", "pipe"],
    });

    let stdout = "";
    let stderr = "";
    let settled = false;

    const timeout = setTimeout(() => {
      if (settled) {
        return;
      }
      settled = true;
      child.kill("SIGKILL");
      reject(new Error(`OpenClaw CLI timed out after ${timeoutMs}ms: ${args.join(" ")}`));
    }, timeoutMs);

    child.stdout.on("data", (d) => {
      stdout += String(d);
    });

    child.stderr.on("data", (d) => {
      stderr += String(d);
    });

    child.on("error", (err) => {
      if (settled) {
        return;
      }
      settled = true;
      clearTimeout(timeout);
      reject(err);
    });

    child.on("close", (code) => {
      if (settled) {
        return;
      }
      settled = true;
      clearTimeout(timeout);
      if (code !== 0) {
        reject(new Error(`OpenClaw CLI failed (${code}): ${stderr.trim()}`));
        return;
      }
      resolve(stdout);
    });
  });
}

async function runCliWithFallback(
  binary: string,
  primaryArgs: string[],
  fallbackArgs: string[],
  timeoutMs: number,
): Promise<string> {
  try {
    return await runCli(binary, primaryArgs, timeoutMs);
  } catch (primaryErr) {
    try {
      return await runCli(binary, fallbackArgs, timeoutMs);
    } catch (fallbackErr) {
      throw new Error(
        `${(primaryErr as Error).message}; fallback failed: ${(fallbackErr as Error).message}`,
      );
    }
  }
}

async function runCliWithAttempts(
  binary: string,
  attempts: string[][],
  timeoutMs: number,
): Promise<string> {
  const errors: string[] = [];
  for (const args of attempts) {
    try {
      return await runCli(binary, args, timeoutMs);
    } catch (err) {
      errors.push(`${args.join(" ")} => ${(err as Error).message}`);
    }
  }
  throw new Error(`All OpenClaw CLI attempts failed: ${errors.join(" | ")}`);
}

function parseRunsArray(output: string): any[] {
  const trimmed = output.trim();
  if (!trimmed) {
    return [];
  }

  try {
    const parsed = JSON.parse(trimmed);
    if (Array.isArray(parsed)) {
      return parsed;
    }
    if (Array.isArray(parsed?.runs)) {
      return parsed.runs;
    }
    if (Array.isArray(parsed?.items)) {
      return parsed.items;
    }
    if (Array.isArray(parsed?.data)) {
      return parsed.data;
    }
    if (Array.isArray(parsed?.entries)) {
      return parsed.entries;
    }
  } catch {
    // Fallback for line-delimited JSON outputs.
  }

  const lineParsed = trimmed
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => {
      try {
        return JSON.parse(line);
      } catch {
        return null;
      }
    })
    .filter((v): v is Record<string, unknown> => v !== null);

  if (lineParsed.length > 0) {
    return lineParsed;
  }

  throw new Error("Unable to parse OpenClaw runs output as JSON");
}

function normalizeRun(raw: any, fallbackJobId: string): RunRecord {
  const runId = String(raw.runId || raw.id || "");
  const jobId = String(raw.jobId || raw.job_id || fallbackJobId);
  const startedAt = String(raw.startedAt || raw.started_at || new Date(0).toISOString());
  const status = String(raw.status || "unknown") as RunRecord["status"];

  assertRunId(runId);
  return {
    runId,
    jobId,
    startedAt,
    status: ["completed", "failed", "running"].includes(status) ? status : "unknown",
  };
}

export class OpenClawCliProvider implements FetchProvider {
  constructor(
    private readonly openClawBin: string,
    private readonly timeoutMs: number,
  ) {}

  async listRunsAfter(jobId: string, lastRunId?: string): Promise<RunRecord[]> {
    assertJobId(jobId);

    const output = await runCliWithAttempts(
      this.openClawBin,
      [
        // Historical CLI variants.
        ["cron", "runs", "list", "--job", jobId, "--json"],
        ["cron", "runs", "list", "--id", jobId, "--json"],
        // Current CLI (no --json, job filter via --id).
        ["cron", "runs", "--id", jobId, "--limit", "200"],
        ["cron", "runs", "--id", jobId],
      ],
      this.timeoutMs,
    );

    const runsArray = parseRunsArray(output);

    const completed = runsArray
      .map((r: any) => normalizeRun(r, jobId))
      .filter((r: RunRecord) => r.status === "completed");

    const ordered = sortRunsOldestFirst(completed);

    if (!lastRunId) {
      return ordered;
    }

    const idx = ordered.findIndex((r) => r.runId === lastRunId);
    if (idx === -1) {
      return ordered;
    }
    return ordered.slice(idx + 1);
  }

  async getRunOutput(runId: string): Promise<string> {
    assertRunId(runId);
    const output = await runCliWithFallback(
      this.openClawBin,
      ["cron", "runs", "output", "--run", runId],
      ["cron", "runs", "output", "--id", runId],
      this.timeoutMs,
    );
    return output;
  }
}
