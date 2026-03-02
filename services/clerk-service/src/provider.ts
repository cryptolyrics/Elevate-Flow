export type RunStatus = "completed" | "failed" | "running" | "unknown";

export interface RunRecord {
  runId: string;
  jobId: string;
  startedAt: string;
  status: RunStatus;
}

export interface FetchProvider {
  listRunsAfter(jobId: string, lastRunId?: string): Promise<RunRecord[]>;
  getRunOutput(runId: string): Promise<string>;
}

export function sortRunsOldestFirst(runs: RunRecord[]): RunRecord[] {
  return [...runs].sort((a, b) => {
    return new Date(a.startedAt).getTime() - new Date(b.startedAt).getTime();
  });
}
