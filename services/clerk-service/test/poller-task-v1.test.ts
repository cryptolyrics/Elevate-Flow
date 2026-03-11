import fs from "fs";
import os from "os";
import path from "path";
import { ClerkConfig } from "../src/config";
import { Poller } from "../src/poller";
import { FetchProvider, RunRecord } from "../src/provider";

class FakeProvider implements FetchProvider {
  constructor(private readonly runs: RunRecord[], private readonly outputs: Record<string, string>) {}

  async listRunsAfter(_jobId: string): Promise<RunRecord[]> {
    return this.runs;
  }

  async getRunOutput(runId: string): Promise<string> {
    return this.outputs[runId];
  }
}

function pkt(packet_id: string, action: string, payload: Record<string, unknown>, actor = "vlad"): string {
  return JSON.stringify({
    version: "task_packet.v1",
    packet_id,
    timestamp: "2026-03-11T10:00:00Z",
    actor: { agent_id: actor },
    action,
    payload,
  });
}

describe("poller task_packet.v1 integration", () => {
  let root: string;

  beforeEach(() => {
    root = fs.mkdtempSync(path.join(os.tmpdir(), "clerk-poller-v1-"));
  });

  afterEach(() => {
    fs.rmSync(root, { recursive: true, force: true });
  });

  test("runs end-to-end mutation flow with duplicate replay and invalid mutation rejection", async () => {
    const config: ClerkConfig = {
      workspaceRoot: root,
      reportWorkspace: root,
      pollIntervalSec: 60,
      fetchMode: "cli",
      openClawBin: "openclaw",
      openClawTimeoutMs: 15000,
      host: "127.0.0.1",
      port: 3008,
      jobs: [{ jobId: "job-vlad", agentId: "vlad", workspace: "workspace-vlad" }],
    };

    const runs: RunRecord[] = [
      { runId: "run-1", jobId: "job-vlad", status: "completed", startedAt: "2026-03-11T10:00:01Z" },
      { runId: "run-2", jobId: "job-vlad", status: "completed", startedAt: "2026-03-11T10:00:02Z" },
      { runId: "run-3", jobId: "job-vlad", status: "completed", startedAt: "2026-03-11T10:00:03Z" },
      { runId: "run-4", jobId: "job-vlad", status: "completed", startedAt: "2026-03-11T10:00:04Z" },
      { runId: "run-5", jobId: "job-vlad", status: "completed", startedAt: "2026-03-11T10:00:05Z" },
      { runId: "run-6", jobId: "job-vlad", status: "completed", startedAt: "2026-03-11T10:00:06Z" },
      { runId: "run-7", jobId: "job-vlad", status: "completed", startedAt: "2026-03-11T10:00:07Z" },
    ];

    const outputs: Record<string, string> = {
      "run-1": pkt("pkt-1", "task.create", {
        task_id: "task-001",
        title: "Redesign Clerk",
        priority: "P1",
        source: "jj",
        summary: "Implement v1 task-state",
        acceptance_criteria: ["works"],
        owner_agent: null,
      }),
      "run-2": pkt("pkt-2", "task.claim", { task_id: "task-001", owner_agent: "vlad" }),
      "run-3": pkt("pkt-3", "task.start", { task_id: "task-001", next_action: "build" }),
      "run-4": pkt("pkt-4", "task.request_review", { task_id: "task-001", reviewer_agent: "jj" }),
      "run-5": pkt("pkt-5", "task.complete", { task_id: "task-001", closed_reason: "completed" }),
      "run-6": pkt("pkt-5", "task.complete", { task_id: "task-001", closed_reason: "completed" }),
      "run-7": pkt("pkt-7", "task.start", { task_id: "task-001", next_action: "illegal restart" }, "ali"),
    };

    const poller = new Poller(config, new FakeProvider(runs, outputs));
    const summary = await poller.pollOnce();

    expect(summary.totalRunsProcessed).toBe(6);
    expect(summary.totalFailures).toBe(1);
    expect(fs.existsSync(path.join(root, "tasks", "closed", "task-001.json"))).toBe(true);
    expect(fs.existsSync(path.join(root, "TASKS.md"))).toBe(true);
    expect(fs.existsSync(path.join(root, "STATUS.md"))).toBe(true);

    const rejectionPath = path.join(root, "tasks", "rejections", `${new Date().toISOString().slice(0, 10)}.jsonl`);
    const rejectionLines = fs.readFileSync(rejectionPath, "utf8").trim().split("\n");
    expect(rejectionLines).toHaveLength(1);
    expect(rejectionLines[0]).toContain("UNAUTHORIZED_ACTOR");
  });
});
