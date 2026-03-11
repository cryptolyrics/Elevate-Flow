export const REJECTION_CODES = [
  "SCHEMA_FAILURE",
  "UNAUTHORIZED_ACTOR",
  "UNSUPPORTED_ACTION",
  "TASK_NOT_FOUND",
  "INVALID_TRANSITION",
  "OWNERSHIP_VIOLATION",
  "IMMUTABLE_CLOSED_TASK",
  "DUPLICATE_PACKET_NOOP",
] as const;

export type RejectionCode = (typeof REJECTION_CODES)[number];

export class TaskPacketError extends Error {
  constructor(
    public readonly code: RejectionCode,
    message: string,
    public readonly details?: Record<string, unknown>,
  ) {
    super(message);
    this.name = "TaskPacketError";
  }
}

export interface RejectionResult {
  ok: false;
  code: RejectionCode;
  message: string;
  details?: Record<string, unknown>;
}

export interface NoopResult {
  ok: true;
  noop: true;
  code: "DUPLICATE_PACKET_NOOP";
  message: string;
}
