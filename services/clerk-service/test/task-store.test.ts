import fs from "fs";
import os from "os";
import path from "path";
import { parseTaskPacketV1 } from "../src/task-packet-v1";
import { applyTaskPacket, getDerivedIndex, loadTask } from "../src/task-store";
import { TaskPacketError } from "../src/task-rejections";

describe("task store", () => {
  let root: string;

  beforeEach(() => {
    root = fs.mkdtempSync(path.join(os.tmpdir(), "clerk-task-store-"));
  });

  afterEach(() => {
    fs.rmSync(root, { recursive: true, force: true });
  });

  function packet(overrides: Record<string, unknown> = {}, payload: Record<string, unknown> = {}) {
    return parseTaskPacketV1({
      version: "task_packet.v1",
      packet_id: `pkt-${Date.now()}-${Math.random()}`,
      timestamp: "2026-03-11T10:00:00Z",
      actor: { agent_id: "vlad" },
      action: "task.create",
      payload: {
        task_id: "task-001",
        title: "Build validator",
        priority: "P1",
        source: "jj",
        summary: "Build the validator",
        acceptance_criteria: ["validator works"],
        owner_agent: null,
        ...payload,
      },
      ...overrides,
    });
  }

  test("applies create packet and writes canonical task files", () => {
    const result = applyTaskPacket(root, packet());
    expect(result.ok).toBe(true);

    const task = loadTask(root, "task-001");
    expect(task?.status).toBe("NEW");

    const index = getDerivedIndex(root);
    expect(index.open_task_ids).toContain("task-001");
    expect(fs.existsSync(path.join(root, "TASKS.md"))).toBe(true);
    expect(fs.existsSync(path.join(root, "STATUS.md"))).toBe(true);
  });

  test("duplicate packet id is noop", () => {
    const pkt = packet({ packet_id: "pkt-fixed" });
    const first = applyTaskPacket(root, pkt);
    const second = applyTaskPacket(root, pkt);

    expect(first.ok).toBe(true);
    expect(second.noop).toBe(true);
  });

  test("enforces lifecycle transitions", () => {
    applyTaskPacket(root, packet({ packet_id: "pkt-create" }));

    const invalidComplete = parseTaskPacketV1({
      version: "task_packet.v1",
      packet_id: "pkt-complete",
      timestamp: "2026-03-11T10:00:00Z",
      actor: { agent_id: "vlad" },
      action: "task.complete",
      payload: { task_id: "task-001" },
    });

    expect(() => applyTaskPacket(root, invalidComplete)).toThrow(TaskPacketError);
  });

  test("moves completed tasks to closed store", () => {
    applyTaskPacket(root, packet({ packet_id: "pkt-create" }));
    applyTaskPacket(root, parseTaskPacketV1({
      version: "task_packet.v1",
      packet_id: "pkt-claim",
      timestamp: "2026-03-11T10:01:00Z",
      actor: { agent_id: "vlad" },
      action: "task.claim",
      payload: { task_id: "task-001", owner_agent: "vlad" },
    }));
    applyTaskPacket(root, parseTaskPacketV1({
      version: "task_packet.v1",
      packet_id: "pkt-start",
      timestamp: "2026-03-11T10:02:00Z",
      actor: { agent_id: "vlad" },
      action: "task.start",
      payload: { task_id: "task-001", next_action: "finish" },
    }));
    applyTaskPacket(root, parseTaskPacketV1({
      version: "task_packet.v1",
      packet_id: "pkt-review",
      timestamp: "2026-03-11T10:03:00Z",
      actor: { agent_id: "vlad" },
      action: "task.request_review",
      payload: { task_id: "task-001", reviewer_agent: "jj" },
    }));
    applyTaskPacket(root, parseTaskPacketV1({
      version: "task_packet.v1",
      packet_id: "pkt-complete",
      timestamp: "2026-03-11T10:04:00Z",
      actor: { agent_id: "vlad" },
      action: "task.complete",
      payload: { task_id: "task-001", closed_reason: "completed" },
    }));

    expect(fs.existsSync(path.join(root, "tasks", "closed", "task-001.json"))).toBe(true);
    expect(fs.existsSync(path.join(root, "tasks", "open", "task-001.json"))).toBe(false);
  });
});
