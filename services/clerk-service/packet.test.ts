/**
 * Packet Parser Strictness Tests
 */

import { parsePacket, validatePacket, PacketParseError } from '../src/parse/packet';

describe('packet parser strictness', () => {
  const validPacket = `===AGENT_ID===
baby-vlad
====

===STATUS_MD===
# My Status
Hello world
====

===LOG_JSONL===
{"level":"info","msg":"hello"}
{"level":"warn","msg":"caution"}
====

===ARTIFACTS===
[]
====`;

  test('parses valid packet correctly', () => {
    const result = parsePacket(validPacket);
    expect(result.agentId).toBe('baby-vlad');
    expect(result.statusMd).toContain('# My Status');
    expect(result.logJsonl).toContain('{"level":"info"');
    expect(result.artifacts).toBe('[]');
  });

  test('rejects packet missing required block', () => {
    const missingStatus = `===AGENT_ID===
baby-vlad
====

===LOG_JSONL===
{}
====

===ARTIFACTS===
[]
====`;

    expect(() => parsePacket(missingStatus)).toThrow(PacketParseError);
    expect(() => parsePacket(missingStatus)).toThrow('Missing required block: STATUS_MD');
  });

  test('rejects packet with reordered blocks', () => {
    const reordered = `===STATUS_MD===
# Status
====

===AGENT_ID===
baby-vlad
====

===LOG_JSONL===
{}
====

===ARTIFACTS===
[]
====`;

    expect(() => parsePacket(reordered)).toThrow(PacketParseError);
    expect(() => parsePacket(reordered)).toThrow('Block order incorrect');
  });

  test('accepts optional PACKET_VERSION block', () => {
    const withVersion = validPacket + `

===PACKET_VERSION===
1.0
====`;

    const result = parsePacket(withVersion);
    expect(result.packetVersion).toBe('1.0');
  });

  test('accepts optional RUN_ID and GENERATED_AT blocks', () => {
    const withOptional = validPacket + `

===RUN_ID===
run-123
====

===GENERATED_AT===
2026-02-27T10:00:00Z
====`;

    const result = parsePacket(withOptional);
    expect(result.runId).toBe('run-123');
    expect(result.generatedAt).toBe('2026-02-27T10:00:00Z');
  });

  test('validatePacket returns valid:true for good packet', () => {
    const result = validatePacket(validPacket);
    expect(result.valid).toBe(true);
    expect(result.error).toBeUndefined();
  });

  test('validatePacket returns valid:false for bad packet', () => {
    const result = validatePacket('===AGENT_ID===\ntest====');
    expect(result.valid).toBe(false);
    expect(result.error).toBeDefined();
  });

  test('handles multiline content in blocks', () => {
    const multiline = `===AGENT_ID===
test
====

===STATUS_MD===
# Header
Line 2
Line 3

Paragraph

- bullet
====

===LOG_JSONL===
{}
====

===ARTIFACTS===
[]
====`;

    const result = parsePacket(multiline);
    expect(result.statusMd).toContain('Header');
    expect(result.statusMd).toContain('Line 2');
    expect(result.statusMd).toContain('Paragraph');
  });
});
