import { assertAgentId } from "./ids";
import { REJECTION_CODES, TaskPacketError } from "./task-rejections";
import { TASK_ACTIONS, TASK_PACKET_VERSION, TASK_STATUSES, TaskPacketEnvelope } from "./task-types";

const PRIORITIES = new Set(["P0", "P1", "P2", "P3"]);
const TASK_ID_RE = /^[a-z0-9][a-z0-9._-]{2,127}$/;

function assertIso(value: unknown, label: string): string {
  if (typeof value !== "string" || Number.isNaN(Date.parse(value))) {
    throw new TaskPacketError("SCHEMA_FAILURE", `${label} must be ISO-8601`);
  }
  return value;
}

function assertTaskId(taskId: unknown): string {
  if (typeof taskId !== "string" || !TASK_ID_RE.test(taskId)) {
    throw new TaskPacketError("SCHEMA_FAILURE", "task_id is invalid");
  }
  return taskId;
}

function assertString(value: unknown, label: string): string {
  if (typeof value !== "string" || value.trim().length === 0) {
    throw new TaskPacketError("SCHEMA_FAILURE", `${label} must be a non-empty string`);
  }
  return value.trim();
}

function assertStringArray(value: unknown, label: string): string[] {
  if (!Array.isArray(value) || value.some((item) => typeof item !== "string")) {
    throw new TaskPacketError("SCHEMA_FAILURE", `${label} must be a string array`);
  }
  return value;
}

function assertPayloadBase(payload: unknown): Record<string, unknown> {
  if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
    throw new TaskPacketError("SCHEMA_FAILURE", "payload must be an object");
  }
  return payload as Record<string, unknown>;
}

function validatePayload(action: string, payload: Record<string, unknown>): void {
  switch (action) {
    case "task.create":
      assertTaskId(payload.task_id);
      assertString(payload.title, "title");
      if (!PRIORITIES.has(assertString(payload.priority, "priority"))) {
        throw new TaskPacketError("SCHEMA_FAILURE", "priority must be P0|P1|P2|P3");
      }
      assertString(payload.source, "source");
      assertString(payload.summary, "summary");
      assertStringArray(payload.acceptance_criteria, "acceptance_criteria");
      if (payload.owner_agent !== null && payload.owner_agent !== undefined) {
        assertAgentId(assertString(payload.owner_agent, "owner_agent"));
      }
      if (payload.reviewer_agent !== undefined) {
        assertAgentId(assertString(payload.reviewer_agent, "reviewer_agent"));
      }
      break;
    case "task.claim":
    case "task.reassign":
      assertTaskId(payload.task_id);
      assertAgentId(assertString(payload.owner_agent, "owner_agent"));
      break;
    case "task.start":
    case "task.unblock":
    case "task.request_review":
    case "task.approve":
    case "task.complete":
    case "task.park":
    case "task.discard":
    case "task.comment":
      assertTaskId(payload.task_id);
      break;
    case "task.block":
      assertTaskId(payload.task_id);
      assertString(payload.reason, "reason");
      assertString(payload.blocker_owner, "blocker_owner");
      assertString(payload.review_path, "review_path");
      assertIso(payload.blocked_at, "blocked_at");
      break;
    default:
      throw new TaskPacketError("UNSUPPORTED_ACTION", `unsupported action: ${action}`);
  }

  if (payload.task_id !== undefined) {
    assertTaskId(payload.task_id);
  }
  if (payload.notes !== undefined) {
    assertString(payload.notes, "notes");
  }
  if (payload.next_action !== undefined) {
    assertString(payload.next_action, "next_action");
  }
  if (payload.artifacts !== undefined) {
    assertStringArray(payload.artifacts, "artifacts");
  }
  if (payload.tags !== undefined) {
    assertStringArray(payload.tags, "tags");
  }
  if (payload.closed_at !== undefined) {
    assertIso(payload.closed_at, "closed_at");
  }
}

export function parseTaskPacketV1(raw: unknown): TaskPacketEnvelope {
  if (!raw || typeof raw !== "object" || Array.isArray(raw)) {
    throw new TaskPacketError("SCHEMA_FAILURE", "packet must be an object");
  }

  const packet = raw as Record<string, unknown>;
  if (packet.version !== TASK_PACKET_VERSION) {
    throw new TaskPacketError("SCHEMA_FAILURE", `version must be ${TASK_PACKET_VERSION}`);
  }

  const packetId = assertString(packet.packet_id, "packet_id");
  const timestamp = assertIso(packet.timestamp, "timestamp");

  const actor = packet.actor;
  if (!actor || typeof actor !== "object" || Array.isArray(actor)) {
    throw new TaskPacketError("SCHEMA_FAILURE", "actor must be an object");
  }
  const actorObj = actor as Record<string, unknown>;
  const actorId = assertString(actorObj.agent_id, "actor.agent_id");
  assertAgentId(actorId);

  const action = assertString(packet.action, "action");
  if (!TASK_ACTIONS.includes(action as any)) {
    throw new TaskPacketError("UNSUPPORTED_ACTION", `unsupported action: ${action}`);
  }

  const payload = assertPayloadBase(packet.payload);
  validatePayload(action, payload);

  return {
    version: TASK_PACKET_VERSION,
    packet_id: packetId,
    timestamp,
    actor: {
      agent_id: actorId,
      session_id: typeof actorObj.session_id === "string" ? actorObj.session_id : undefined,
    },
    action: action as TaskPacketEnvelope["action"],
    payload,
  };
}

export function validateTaskPacketV1(raw: unknown): { valid: true; packet: TaskPacketEnvelope } | { valid: false; code: typeof REJECTION_CODES[number]; message: string } {
  try {
    return { valid: true, packet: parseTaskPacketV1(raw) };
  } catch (err) {
    const error = err as TaskPacketError;
    return { valid: false, code: error.code || "SCHEMA_FAILURE", message: error.message };
  }
}
