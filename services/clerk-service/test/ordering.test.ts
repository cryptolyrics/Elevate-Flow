import fs from "fs";
import os from "os";
import path from "path";
import { ClerkConfig } from "../src/config";
import { Poller } from "../src/poller";
import { FetchProvider, RunRecord } from "../src/provider";

function packet(status: string, runId: string): string {
  return `===AGENT_ID===
baby-vlad
====

===STATUS_MD===
${status}
====

===LOG_JSONL===
{"run":"${runId}"}
====

===ARTIFACTS===
[]
====

===RUN_ID===
${runId}
====`;
}

class FakeProvider implements FetchProvider {
  constructor(private readonly runs: RunRecord[], private readonly outputs: Record<string, string>) {}

  async listRunsAfter(_jobId: string): Promise<RunRecord[]> {
    return this.runs;
  }

  async getRunOutput(runId: string): Promise<string> {
    return this.outputs[runId];
  }
}

describe("poller ordering and idempotency", () => {
  const root = path.join(os.tmpdir(), `clerk-order-${Date.now()}`);

  beforeAll(() => {
    fs.mkdirSync(root, { recursive: true });
  });

  afterAll(() => {
    fs.rmSync(root, { recursive: true, force: true });
  });

  test("processes runs oldest to newest", async () => {
    const config: ClerkConfig = {
      workspaceRoot: root,
      reportWorkspace: root,
      pollIntervalSec: 60,
      fetchMode: "cli",
      openClawBin: "openclaw",
      host: "127.0.0.1",
      port: 3008,
      jobs: [
        {
          jobId: "job-1",
          agentId: "baby-vlad",
          workspace: "workspace-baby-vlad",
        },
      ],
    };

    const runs: RunRecord[] = [
      { runId: "run-3", jobId: "job-1", status: "completed", startedAt: "2026-03-01T10:02:00Z" },
      { runId: "run-1", jobId: "job-1", status: "completed", startedAt: "2026-03-01T10:00:00Z" },
      { runId: "run-2", jobId: "job-1", status: "completed", startedAt: "2026-03-01T10:01:00Z" },
    ];

    const provider = new FakeProvider(runs, {
      "run-1": packet("First", "run-1"),
      "run-2": packet("Second", "run-2"),
      "run-3": packet("Third", "run-3"),
    });

    const poller = new Poller(config, provider);
    await poller.pollOnce();

    const statusPath = path.join(root, "workspace-baby-vlad", "STATUS.md");
    const status = fs.readFileSync(statusPath, "utf8");
    expect(status.trim()).toBe("Third");

    const logPath = path.join(root, "workspace-baby-vlad", "logs", `${new Date().toISOString().slice(0, 10)}.jsonl`);
    const lines = fs.readFileSync(logPath, "utf8").trim().split("\n");
    expect(lines).toEqual([
      '{"run":"run-1"}',
      '{"run":"run-2"}',
      '{"run":"run-3"}',
    ]);
  });
});
