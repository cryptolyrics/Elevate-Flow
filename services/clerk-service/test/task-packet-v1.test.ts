import { parseTaskPacketV1, validateTaskPacketV1 } from "../src/task-packet-v1";

describe("task_packet.v1", () => {
  const validPacket = {
    version: "task_packet.v1",
    packet_id: "pkt-001",
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
    },
  };

  test("parses valid packet", () => {
    const packet = parseTaskPacketV1(validPacket);
    expect(packet.action).toBe("task.create");
    expect(packet.actor.agent_id).toBe("vlad");
  });

  test("rejects missing blocked_at on block", () => {
    const result = validateTaskPacketV1({
      ...validPacket,
      action: "task.block",
      payload: {
        task_id: "task-001",
        reason: "Need JJ",
        blocker_owner: "jj",
        review_path: "jj-review",
      },
    });

    expect(result.valid).toBe(false);
    if (!result.valid) {
      expect(result.code).toBe("SCHEMA_FAILURE");
    }
  });
});
