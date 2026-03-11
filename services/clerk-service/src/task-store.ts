import fs from "fs";
import path from "path";
import { resolveInSandbox, safeAppendLines, safeWriteFile } from "./sandbox";
import { TaskPacketError } from "./task-rejections";
import { CanonicalTaskRecord, TaskEventRecord, TaskIndex, TaskIndexEntry, TaskPacketEnvelope } from "./task-types";
import { renderStatusMd, renderTasksMd } from "./task-render";
import { enforceOwnership, enforceTransition, nextStatusForAction } from "./task-lifecycle";

const OPEN_DIR = "tasks/open";
const CLOSED_DIR = "tasks/closed";
const EVENTS_DIR = "tasks/events";
const INDEX_FILE = "tasks/index.json";

function taskPath(taskId: string, closed: boolean): string {
  return path.join(closed ? CLOSED_DIR : OPEN_DIR, `${taskId}.json`);
}

function loadJson<T>(root: string, rel: string): T | null {
  const abs = resolveInSandbox(root, rel);
  if (!fs.existsSync(abs)) {
    return null;
  }
  return JSON.parse(fs.readFileSync(abs, "utf8")) as T;
}

export function loadTask(root: string, taskId: string): CanonicalTaskRecord | null {
  return loadJson<CanonicalTaskRecord>(root, taskPath(taskId, false)) || loadJson<CanonicalTaskRecord>(root, taskPath(taskId, true));
}

function deleteIfExists(root: string, rel: string): void {
  const abs = resolveInSandbox(root, rel);
  if (fs.existsSync(abs)) {
    fs.rmSync(abs, { force: true });
  }
}

function listTaskFiles(root: string, rel: string): CanonicalTaskRecord[] {
  const abs = resolveInSandbox(root, rel);
  if (!fs.existsSync(abs)) {
    return [];
  }
  return fs.readdirSync(abs)
    .filter((name) => name.endsWith(".json"))
    .sort()
    .map((name) => JSON.parse(fs.readFileSync(path.join(abs, name), "utf8")) as CanonicalTaskRecord);
}

function loadIndex(root: string): TaskIndex {
  return loadJson<TaskIndex>(root, INDEX_FILE) || {
    generated_at: "",
    open_task_ids: [],
    closed_task_ids: [],
    tasks: {},
  };
}

function saveIndex(root: string, index: TaskIndex): void {
  safeWriteFile(root, INDEX_FILE, JSON.stringify(index, null, 2));
}

function saveTask(root: string, record: CanonicalTaskRecord): void {
  const closed = ["DONE", "DISCARDED"].includes(record.status);
  safeWriteFile(root, taskPath(record.task_id, closed), JSON.stringify(record, null, 2));
  deleteIfExists(root, taskPath(record.task_id, !closed));
}

function applyPayload(record: CanonicalTaskRecord, packet: TaskPacketEnvelope, acceptedAt: string): CanonicalTaskRecord {
  const payload = packet.payload;
  const next = nextStatusForAction(packet.action, record.status);
  enforceTransition(record.status, next, packet.action);

  const updated: CanonicalTaskRecord = {
    ...record,
    status: next,
    owner_agent: packet.action === "task.claim" || packet.action === "task.reassign"
      ? String(payload.owner_agent)
      : record.owner_agent,
    reviewer_agent: typeof payload.reviewer_agent === "string" ? payload.reviewer_agent : record.reviewer_agent,
    notes: typeof payload.notes === "string" ? payload.notes : record.notes,
    next_action: typeof payload.next_action === "string" ? payload.next_action : record.next_action,
    artifacts: Array.isArray(payload.artifacts) ? (payload.artifacts as string[]) : record.artifacts,
    blocker_owner: typeof payload.blocker_owner === "string" ? payload.blocker_owner : record.blocker_owner,
    review_path: typeof payload.review_path === "string" ? payload.review_path : record.review_path,
    blocked_at: typeof payload.blocked_at === "string" ? payload.blocked_at : record.blocked_at,
    closed_at: ["DONE", "DISCARDED"].includes(next) ? (typeof payload.closed_at === "string" ? payload.closed_at : acceptedAt) : record.closed_at,
    closed_reason: typeof payload.closed_reason === "string" ? payload.closed_reason : record.closed_reason,
    last_packet_id: packet.packet_id,
    last_packet_timestamp: packet.timestamp,
    last_accepted_at: acceptedAt,
  };

  updated.history = [
    ...record.history,
    {
      packet_id: packet.packet_id,
      task_id: record.task_id,
      actor_id: packet.actor.agent_id,
      action: packet.action,
      from_status: record.status,
      to_status: next,
      packet_timestamp: packet.timestamp,
      accepted_at: acceptedAt,
      notes: typeof payload.notes === "string" ? payload.notes : undefined,
    },
  ];

  return updated;
}

function createRecord(packet: TaskPacketEnvelope, acceptedAt: string): CanonicalTaskRecord {
  const payload = packet.payload;
  return {
    task_id: String(payload.task_id),
    title: String(payload.title),
    status: "NEW",
    owner_agent: payload.owner_agent === null || payload.owner_agent === undefined ? null : String(payload.owner_agent),
    reviewer_agent: typeof payload.reviewer_agent === "string" ? payload.reviewer_agent : undefined,
    created_at: acceptedAt,
    created_by: packet.actor.agent_id,
    priority: String(payload.priority) as CanonicalTaskRecord["priority"],
    source: String(payload.source),
    summary: String(payload.summary),
    acceptance_criteria: payload.acceptance_criteria as string[],
    artifacts: Array.isArray(payload.artifacts) ? (payload.artifacts as string[]) : [],
    history: [
      {
        packet_id: packet.packet_id,
        task_id: String(payload.task_id),
        actor_id: packet.actor.agent_id,
        action: packet.action,
        from_status: null,
        to_status: "NEW",
        packet_timestamp: packet.timestamp,
        accepted_at: acceptedAt,
      },
    ],
    tags: Array.isArray(payload.tags) ? (payload.tags as string[]) : undefined,
    project: typeof payload.project === "string" ? payload.project : undefined,
    mission_link: typeof payload.mission_link === "string" ? payload.mission_link : undefined,
    next_action: typeof payload.next_action === "string" ? payload.next_action : undefined,
    last_packet_id: packet.packet_id,
    last_packet_timestamp: packet.timestamp,
    last_accepted_at: acceptedAt,
  };
}

function writeEvent(root: string, event: TaskEventRecord): void {
  const day = event.accepted_at.slice(0, 10);
  safeAppendLines(root, path.join(EVENTS_DIR, `${day}.jsonl`), [JSON.stringify(event)]);
}

function refreshDerived(root: string, nowIso: string): void {
  const openTasks = listTaskFiles(root, OPEN_DIR);
  const closedTasks = listTaskFiles(root, CLOSED_DIR);
  const index: TaskIndex = {
    generated_at: nowIso,
    open_task_ids: openTasks.map((task) => task.task_id),
    closed_task_ids: closedTasks.map((task) => task.task_id),
    tasks: {},
  };

  for (const task of [...openTasks, ...closedTasks]) {
    const entry: TaskIndexEntry = {
      task_id: task.task_id,
      status: task.status,
      owner_agent: task.owner_agent,
      reviewer_agent: task.reviewer_agent,
      priority: task.priority,
      title: task.title,
      updated_at: task.last_accepted_at || task.created_at,
      packet_id: task.last_packet_id,
    };
    index.tasks[task.task_id] = entry;
  }

  saveIndex(root, index);
  safeWriteFile(root, "TASKS.md", renderTasksMd(openTasks, closedTasks));
  safeWriteFile(root, "STATUS.md", renderStatusMd(index, openTasks, closedTasks, nowIso));
}

export interface ApplyPacketResult {
  ok: true;
  noop?: true;
  task_id: string;
  packet_id: string;
  accepted_at: string;
}

export function applyTaskPacket(root: string, packet: TaskPacketEnvelope): ApplyPacketResult {
  const existing = loadTask(root, String(packet.payload.task_id || ""));
  if (existing?.last_packet_id === packet.packet_id) {
    return {
      ok: true,
      noop: true,
      task_id: existing.task_id,
      packet_id: packet.packet_id,
      accepted_at: existing.last_accepted_at || new Date().toISOString(),
    };
  }

  const acceptedAt = new Date().toISOString();
  let record: CanonicalTaskRecord;
  if (packet.action === "task.create") {
    if (existing) {
      throw new TaskPacketError("OWNERSHIP_VIOLATION", `task already exists: ${existing.task_id}`);
    }
    record = createRecord(packet, acceptedAt);
  } else {
    enforceOwnership(existing, packet);
    record = applyPayload(existing as CanonicalTaskRecord, packet, acceptedAt);
  }

  saveTask(root, record);
  writeEvent(root, {
    packet_id: packet.packet_id,
    task_id: record.task_id,
    actor_id: packet.actor.agent_id,
    action: packet.action,
    packet_timestamp: packet.timestamp,
    accepted_at: acceptedAt,
    from_status: packet.action === "task.create" ? null : (existing as CanonicalTaskRecord).status,
    to_status: record.status,
    result: "ACCEPTED",
  });
  refreshDerived(root, acceptedAt);

  return {
    ok: true,
    task_id: record.task_id,
    packet_id: packet.packet_id,
    accepted_at: acceptedAt,
  };
}

export function getDerivedIndex(root: string): TaskIndex {
  return loadIndex(root);
}
