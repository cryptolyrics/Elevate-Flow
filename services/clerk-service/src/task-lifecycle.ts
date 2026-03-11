import { TaskPacketError } from "./task-rejections";
import { CanonicalTaskRecord, TaskAction, TaskPacketEnvelope, TaskStatus } from "./task-types";

const ALLOWED: Record<TaskStatus, TaskStatus[]> = {
  NEW: ["CLAIMED"],
  CLAIMED: ["IN_PROGRESS", "PARKED", "DISCARDED"],
  IN_PROGRESS: ["BLOCKED", "IN_REVIEW", "PARKED", "DISCARDED"],
  BLOCKED: ["IN_PROGRESS", "PARKED"],
  IN_REVIEW: ["IN_PROGRESS", "DONE", "BLOCKED"],
  DONE: [],
  PARKED: ["CLAIMED"],
  DISCARDED: [],
};

export function nextStatusForAction(action: TaskAction, current: TaskStatus | null): TaskStatus {
  switch (action) {
    case "task.create":
      return "NEW";
    case "task.claim":
      return "CLAIMED";
    case "task.start":
      return "IN_PROGRESS";
    case "task.block":
      return "BLOCKED";
    case "task.unblock":
      return "IN_PROGRESS";
    case "task.request_review":
    case "task.approve":
      return "IN_REVIEW";
    case "task.complete":
      return "DONE";
    case "task.park":
      return "PARKED";
    case "task.discard":
      return "DISCARDED";
    case "task.comment":
      if (current === null) {
        throw new TaskPacketError("TASK_NOT_FOUND", "cannot comment missing task");
      }
      return current;
    case "task.reassign":
      if (current === null) {
        throw new TaskPacketError("TASK_NOT_FOUND", "cannot reassign missing task");
      }
      return current;
    default:
      throw new TaskPacketError("UNSUPPORTED_ACTION", `unsupported action: ${action}`);
  }
}

export function enforceTransition(current: TaskStatus | null, next: TaskStatus, action: TaskAction): void {
  if (current === null) {
    if (action !== "task.create") {
      throw new TaskPacketError("TASK_NOT_FOUND", "task does not exist");
    }
    return;
  }

  if (current === next && (action === "task.comment" || action === "task.reassign" || action === "task.approve")) {
    return;
  }

  if (!ALLOWED[current].includes(next)) {
    throw new TaskPacketError("INVALID_TRANSITION", `invalid transition ${current} -> ${next}`);
  }
}

export function enforceOwnership(record: CanonicalTaskRecord | null, packet: TaskPacketEnvelope): void {
  const payload = packet.payload;
  const actorId = packet.actor.agent_id;

  if (packet.action === "task.create") {
    return;
  }
  if (!record) {
    throw new TaskPacketError("TASK_NOT_FOUND", "task does not exist");
  }
  if (record.status === "DONE" || record.status === "DISCARDED") {
    throw new TaskPacketError("IMMUTABLE_CLOSED_TASK", `task is closed: ${record.status}`);
  }

  if (packet.action === "task.reassign") {
    const targetOwner = String(payload.owner_agent || "");
    if (actorId.startsWith("baby-") && targetOwner !== actorId) {
      throw new TaskPacketError("OWNERSHIP_VIOLATION", "subagent cross-lane reassignment requires approval");
    }
    return;
  }

  if (packet.action === "task.claim") {
    const targetOwner = String(payload.owner_agent || "");
    if (actorId !== targetOwner && actorId !== "jj") {
      throw new TaskPacketError("OWNERSHIP_VIOLATION", "claim owner must match actor or jj");
    }
    return;
  }

  if (record.owner_agent && actorId !== record.owner_agent && actorId !== "jj" && actorId !== "coppa") {
    throw new TaskPacketError("OWNERSHIP_VIOLATION", `actor ${actorId} cannot mutate task owned by ${record.owner_agent}`);
  }
}
