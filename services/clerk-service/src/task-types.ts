export const TASK_PACKET_VERSION = "task_packet.v1";

export const TASK_STATUSES = [
  "NEW",
  "CLAIMED",
  "IN_PROGRESS",
  "BLOCKED",
  "IN_REVIEW",
  "DONE",
  "PARKED",
  "DISCARDED",
] as const;

export type TaskStatus = (typeof TASK_STATUSES)[number];

export const TASK_ACTIONS = [
  "task.create",
  "task.claim",
  "task.start",
  "task.block",
  "task.unblock",
  "task.request_review",
  "task.approve",
  "task.complete",
  "task.park",
  "task.discard",
  "task.comment",
  "task.reassign",
] as const;

export type TaskAction = (typeof TASK_ACTIONS)[number];

export interface TaskActor {
  agent_id: string;
  session_id?: string;
}

export interface TaskPacketEnvelope {
  version: typeof TASK_PACKET_VERSION;
  packet_id: string;
  timestamp: string;
  actor: TaskActor;
  action: TaskAction;
  payload: Record<string, unknown>;
}

export interface TaskHistoryEvent {
  packet_id: string;
  task_id: string;
  actor_id: string;
  action: TaskAction;
  from_status: TaskStatus | null;
  to_status: TaskStatus;
  packet_timestamp: string;
  accepted_at: string;
  notes?: string;
}

export interface CanonicalTaskRecord {
  task_id: string;
  title: string;
  status: TaskStatus;
  owner_agent: string | null;
  reviewer_agent?: string;
  created_at: string;
  created_by: string;
  priority: "P0" | "P1" | "P2" | "P3";
  source: string;
  summary: string;
  acceptance_criteria: string[];
  artifacts: string[];
  history: TaskHistoryEvent[];
  due_at?: string;
  blocked_by?: string[];
  depends_on?: string[];
  tags?: string[];
  project?: string;
  mission_link?: string;
  notes?: string;
  next_action?: string;
  closed_at?: string;
  closed_reason?: string;
  reason?: string;
  blocker_owner?: string;
  review_path?: string;
  blocked_at?: string;
  last_packet_id?: string;
  last_packet_timestamp?: string;
  last_accepted_at?: string;
}

export interface TaskIndexEntry {
  task_id: string;
  status: TaskStatus;
  owner_agent: string | null;
  reviewer_agent?: string;
  priority: CanonicalTaskRecord["priority"];
  title: string;
  updated_at: string;
  packet_id?: string;
}

export interface TaskIndex {
  generated_at: string;
  open_task_ids: string[];
  closed_task_ids: string[];
  tasks: Record<string, TaskIndexEntry>;
}

export interface TaskEventRecord {
  packet_id: string;
  task_id: string;
  actor_id: string;
  action: TaskAction;
  packet_timestamp: string;
  accepted_at: string;
  from_status: TaskStatus | null;
  to_status: TaskStatus;
  result: "ACCEPTED" | "REJECTED" | "NOOP";
  code?: string;
  message?: string;
}
