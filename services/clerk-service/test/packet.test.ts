import { PacketParseError, parsePacket, validatePacket } from "../src/packet";

const VALID_PACKET = `===AGENT_ID===
baby-vlad
====

===STATUS_MD===
# Status
Completed task.
====

===LOG_JSONL===
{"level":"info","msg":"started"}
{"level":"info","msg":"done"}
====

===ARTIFACTS===
[{"path":"report.txt","content":"ok"}]
====

===PACKET_VERSION===
1.0
====

===RUN_ID===
run-123
====

===GENERATED_AT===
2026-03-01T10:00:00Z
====`;

describe("packet parser", () => {
  test("parses a valid packet", () => {
    const packet = parsePacket(VALID_PACKET);
    expect(packet.agentId).toBe("baby-vlad");
    expect(packet.logJsonl).toHaveLength(2);
    expect(packet.artifacts[0].path).toBe("report.txt");
  });

  test("rejects missing required block", () => {
    const invalid = `===AGENT_ID===\nbaby-vlad\n====\n\n===LOG_JSONL===\n{}\n====\n\n===ARTIFACTS===\n[]\n====`;
    expect(() => parsePacket(invalid)).toThrow(PacketParseError);
  });

  test("rejects reordered required blocks", () => {
    const invalid = `===STATUS_MD===\nabc\n====\n\n===AGENT_ID===\nbaby-vlad\n====\n\n===LOG_JSONL===\n{}\n====\n\n===ARTIFACTS===\n[]\n====`;
    expect(() => parsePacket(invalid)).toThrow(PacketParseError);
  });

  test("rejects invalid JSONL", () => {
    const invalid = `===AGENT_ID===\nbaby-vlad\n====\n\n===STATUS_MD===\nok\n====\n\n===LOG_JSONL===\n{broken}\n====\n\n===ARTIFACTS===\n[]\n====`;
    expect(() => parsePacket(invalid)).toThrow(PacketParseError);
  });

  test("validatePacket reports errors", () => {
    const result = validatePacket("bad");
    expect(result.valid).toBe(false);
    expect(result.error).toBeDefined();
  });
});
