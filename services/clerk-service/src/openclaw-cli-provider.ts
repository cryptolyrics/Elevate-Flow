import { spawn } from "child_process";
import { assertJobId, assertRunId } from "./ids";
import { FetchProvider, RunRecord, sortRunsOldestFirst } from "./provider";

function runCli(binary: string, args: string[]): Promise<string> {
  return new Promise((resolve, reject) => {
    const child = spawn(binary, args, {
      shell: false,
      stdio: ["ignore", "pipe", "pipe"],
    });

    let stdout = "";
    let stderr = "";

    child.stdout.on("data", (d) => {
      stdout += String(d);
    });

    child.stderr.on("data", (d) => {
      stderr += String(d);
    });

    child.on("error", (err) => reject(err));
    child.on("close", (code) => {
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
): Promise<string> {
  try {
    return await runCli(binary, primaryArgs);
  } catch (primaryErr) {
    try {
      return await runCli(binary, fallbackArgs);
    } catch {
      throw primaryErr;
    }
  }
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
  constructor(private readonly openClawBin: string) {}

  async listRunsAfter(jobId: string, lastRunId?: string): Promise<RunRecord[]> {
    assertJobId(jobId);

    const output = await runCli(this.openClawBin, [
      "cron",
      "runs",
      "--id",
      jobId,
    ]);

    const parsed = JSON.parse(output);
    const runsArray = Array.isArray(parsed) ? parsed : (parsed.runs || []);

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
    );
    return output;
  }
}
