import path from "path";
import { safeAppendLines } from "./sandbox";
import { RejectionCode } from "./task-rejections";

export interface TaskRejectionEvent {
  packet_id?: string;
  task_id?: string;
  actor_id?: string;
  packet_timestamp?: string;
  rejected_at: string;
  code: RejectionCode | string;
  message: string;
  details?: Record<string, unknown>;
  run_id?: string;
  job_id?: string;
}

export function appendTaskRejection(root: string, event: TaskRejectionEvent): void {
  const day = event.rejected_at.slice(0, 10);
  safeAppendLines(root, path.join("tasks", "rejections", `${day}.jsonl`), [JSON.stringify(event)]);
}
