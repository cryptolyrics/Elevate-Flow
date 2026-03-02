import path from "path";
import { ClerkConfig, JobConfig } from "./config";
import { parsePacket } from "./packet";
import { FetchProvider, RunRecord } from "./provider";
import { normalizePacket } from "./normalize";
import { advanceState, loadState, touchPollState } from "./state";
import { safeWriteFile } from "./sandbox";

export interface JobPollResult {
  jobId: string;
  runsProcessed: number;
  failures: number;
  errors: string[];
}

export interface PollSummary {
  startedAt: string;
  finishedAt: string;
  totalRunsProcessed: number;
  totalFailures: number;
  jobs: JobPollResult[];
}

export class Poller {
  private timer: NodeJS.Timeout | null = null;
  private lastSummary: PollSummary | null = null;

  constructor(
    private readonly config: ClerkConfig,
    private readonly provider: FetchProvider,
  ) {}

  getLastSummary(): PollSummary | null {
    return this.lastSummary;
  }

  async pollOnce(): Promise<PollSummary> {
    const startedAt = new Date().toISOString();
    const jobs: JobPollResult[] = [];

    for (const job of this.config.jobs) {
      jobs.push(await this.processJob(job));
    }

    touchPollState(this.config.workspaceRoot);

    const summary: PollSummary = {
      startedAt,
      finishedAt: new Date().toISOString(),
      totalRunsProcessed: jobs.reduce((acc, j) => acc + j.runsProcessed, 0),
      totalFailures: jobs.reduce((acc, j) => acc + j.failures, 0),
      jobs,
    };

    this.lastSummary = summary;
    this.writeReport(summary);
    return summary;
  }

  start(): void {
    if (this.timer) {
      return;
    }

    const runLoop = async () => {
      try {
        await this.pollOnce();
      } catch (err) {
        this.writeDeadLetter("poller", "loop", err as Error, "");
      }
    };

    this.timer = setInterval(runLoop, this.config.pollIntervalSec * 1000);
  }

  stop(): void {
    if (this.timer) {
      clearInterval(this.timer);
      this.timer = null;
    }
  }

  private async processJob(job: JobConfig): Promise<JobPollResult> {
    const result: JobPollResult = {
      jobId: job.jobId,
      runsProcessed: 0,
      failures: 0,
      errors: [],
    };

    const state = loadState(this.config.workspaceRoot);
    const lastRunId = state.jobs[job.jobId]?.lastProcessedRunId;

    let runs: RunRecord[] = [];
    try {
      runs = await this.provider.listRunsAfter(job.jobId, lastRunId);
      runs = [...runs].sort((a, b) => {
        return new Date(a.startedAt).getTime() - new Date(b.startedAt).getTime();
      });
    } catch (err) {
      result.failures += 1;
      result.errors.push(`listRunsAfter failed: ${(err as Error).message}`);
      return result;
    }

    for (const run of runs) {
      let output = "";
      try {
        output = await this.provider.getRunOutput(run.runId);
        const packet = parsePacket(output);

        if (packet.agentId !== job.agentId) {
          throw new Error(`agent mismatch expected=${job.agentId} actual=${packet.agentId}`);
        }
        if (packet.runId && packet.runId !== run.runId) {
          throw new Error(`runId mismatch packet=${packet.runId} provider=${run.runId}`);
        }

        normalizePacket(this.config, job, packet);
        advanceState(this.config.workspaceRoot, job.jobId, run.runId);
        result.runsProcessed += 1;
      } catch (err) {
        result.failures += 1;
        result.errors.push(`run ${run.runId}: ${(err as Error).message}`);
        this.writeDeadLetter(job.jobId, run.runId, err as Error, output);
      }
    }

    return result;
  }

  private writeDeadLetter(jobId: string, runId: string, err: Error, output: string): void {
    const day = new Date().toISOString().slice(0, 10);
    const rel = path.join(".clerk", "dead-letter", day, `${jobId}-${runId}.json`);
    const payload = {
      timestamp: new Date().toISOString(),
      jobId,
      runId,
      error: err.message,
      outputSample: output.slice(0, 4000),
    };

    safeWriteFile(this.config.reportWorkspace, rel, JSON.stringify(payload, null, 2));
  }

  private writeReport(summary: PollSummary): void {
    const lines: string[] = [
      "# Clerk Poll Report",
      "",
      `Started: ${summary.startedAt}`,
      `Finished: ${summary.finishedAt}`,
      `Runs processed: ${summary.totalRunsProcessed}`,
      `Failures: ${summary.totalFailures}`,
      "",
      "## Jobs",
    ];

    for (const job of summary.jobs) {
      lines.push(`- ${job.jobId}: processed=${job.runsProcessed} failures=${job.failures}`);
      for (const err of job.errors) {
        lines.push(`  - error: ${err}`);
      }
    }

    safeWriteFile(this.config.reportWorkspace, path.join(".clerk", "report.md"), `${lines.join("\n")}\n`);
  }
}
