import { assertAgentId, assertRunId } from "./ids";

export interface Artifact {
  path: string;
  content: string;
}

export interface Packet {
  agentId: string;
  statusMd: string;
  logJsonl: string[];
  artifacts: Artifact[];
  packetVersion?: string;
  runId?: string;
  generatedAt?: string;
}

export class PacketParseError extends Error {
  constructor(public readonly code: string, message: string) {
    super(message);
    this.name = "PacketParseError";
  }
}

type Block = { name: string; content: string };

const REQUIRED = ["AGENT_ID", "STATUS_MD", "LOG_JSONL", "ARTIFACTS"] as const;
const OPTIONAL = ["PACKET_VERSION", "RUN_ID", "GENERATED_AT"] as const;
const ALL = new Set<string>([...REQUIRED, ...OPTIONAL]);

function parseBlocks(raw: string): Block[] {
  const blocks: Block[] = [];
  const re = /===([A-Z_]+)===\n([\s\S]*?)\n====(?:\n|$)/g;
  let lastIndex = 0;

  while (true) {
    const match = re.exec(raw);
    if (!match) {
      break;
    }

    const prefix = raw.slice(lastIndex, match.index);
    if (prefix.trim().length > 0) {
      throw new PacketParseError("PACKET_FORMAT", "Unexpected text outside block boundaries");
    }

    const name = match[1];
    const content = match[2];

    if (!ALL.has(name)) {
      throw new PacketParseError("UNKNOWN_BLOCK", `Unknown block: ${name}`);
    }

    if (blocks.some((b) => b.name === name)) {
      throw new PacketParseError("DUP_BLOCK", `Duplicate block: ${name}`);
    }

    blocks.push({ name, content });
    lastIndex = re.lastIndex;
  }

  if (raw.slice(lastIndex).trim().length > 0) {
    throw new PacketParseError("PACKET_FORMAT", "Trailing malformed packet data");
  }

  return blocks;
}

function validateOrder(blocks: Block[]): void {
  for (let i = 0; i < REQUIRED.length; i += 1) {
    if (!blocks[i] || blocks[i].name !== REQUIRED[i]) {
      throw new PacketParseError("BLOCK_ORDER", `Missing required block: ${REQUIRED[i]}`);
    }
  }

  const trailing = blocks.slice(REQUIRED.length).map((b) => b.name);
  let lastOptionalIndex = -1;
  for (const name of trailing) {
    const idx = OPTIONAL.indexOf(name as (typeof OPTIONAL)[number]);
    if (idx === -1 || idx <= lastOptionalIndex) {
      throw new PacketParseError("BLOCK_ORDER", "Optional block order incorrect");
    }
    lastOptionalIndex = idx;
  }
}

function parseLogJsonl(content: string): string[] {
  const lines = content
    .split("\n")
    .map((l) => l.trim())
    .filter((l) => l.length > 0);

  for (const line of lines) {
    try {
      JSON.parse(line);
    } catch {
      throw new PacketParseError("LOG_JSONL_INVALID", "LOG_JSONL contains invalid JSON line");
    }
  }

  return lines;
}

function parseArtifacts(content: string): Artifact[] {
  let parsed: any;
  try {
    parsed = JSON.parse(content);
  } catch {
    throw new PacketParseError("ARTIFACTS_INVALID", "ARTIFACTS block is not valid JSON");
  }

  if (!Array.isArray(parsed)) {
    throw new PacketParseError("ARTIFACTS_INVALID", "ARTIFACTS must be a JSON array");
  }

  const artifacts: Artifact[] = [];
  for (const item of parsed) {
    if (!item || typeof item.path !== "string" || typeof item.content !== "string") {
      throw new PacketParseError("ARTIFACTS_INVALID", "Each artifact must include string path and content");
    }
    artifacts.push({ path: item.path, content: item.content });
  }

  return artifacts;
}

export function parsePacket(raw: string): Packet {
  const blocks = parseBlocks(raw);
  validateOrder(blocks);

  const byName = new Map<string, string>();
  for (const b of blocks) {
    byName.set(b.name, b.content);
  }

  const agentId = String(byName.get("AGENT_ID") || "").trim();
  assertAgentId(agentId);

  const packetVersion = byName.get("PACKET_VERSION")?.trim();
  if (packetVersion && packetVersion !== "1.0") {
    throw new PacketParseError("PACKET_VERSION_UNSUPPORTED", `Unsupported packet version: ${packetVersion}`);
  }

  const runId = byName.get("RUN_ID")?.trim();
  if (runId) {
    assertRunId(runId);
  }

  const generatedAt = byName.get("GENERATED_AT")?.trim();
  if (generatedAt && Number.isNaN(Date.parse(generatedAt))) {
    throw new PacketParseError("GENERATED_AT_INVALID", "GENERATED_AT must be ISO-8601");
  }

  return {
    agentId,
    statusMd: String(byName.get("STATUS_MD") || ""),
    logJsonl: parseLogJsonl(String(byName.get("LOG_JSONL") || "")),
    artifacts: parseArtifacts(String(byName.get("ARTIFACTS") || "[]")),
    packetVersion,
    runId,
    generatedAt,
  };
}

export function validatePacket(raw: string): { valid: boolean; error?: string } {
  try {
    parsePacket(raw);
    return { valid: true };
  } catch (err) {
    return { valid: false, error: (err as Error).message };
  }
}
