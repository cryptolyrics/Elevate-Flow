import path from "path";
import { JobConfig, ClerkConfig } from "./config";
import { Packet } from "./packet";
import { resolveInSandbox, safeAppendLines, safeWriteFile, SandboxError } from "./sandbox";

function assertOutputArtifactPath(workspaceRoot: string, workspaceRel: string, artifactPath: string): string {
  const outputBaseRel = path.join(workspaceRel, "OUTPUTS");
  const outputBaseAbs = resolveInSandbox(workspaceRoot, outputBaseRel);
  const artifactAbs = resolveInSandbox(workspaceRoot, path.join(outputBaseRel, artifactPath));

  if (artifactAbs !== outputBaseAbs && !artifactAbs.startsWith(`${outputBaseAbs}${path.sep}`)) {
    throw new SandboxError("Artifact path escapes OUTPUTS");
  }

  return path.relative(path.resolve(workspaceRoot), artifactAbs);
}

function datePart(value?: string): string {
  if (value && !Number.isNaN(Date.parse(value))) {
    return value.slice(0, 10);
  }
  return new Date().toISOString().slice(0, 10);
}

export function normalizePacket(config: ClerkConfig, job: JobConfig, packet: Packet): void {
  const workspaceRel = job.workspace;

  resolveInSandbox(config.workspaceRoot, workspaceRel);

  const logFile = path.join(workspaceRel, "logs", `${datePart(packet.generatedAt)}.jsonl`);
  safeAppendLines(config.workspaceRoot, logFile, packet.logJsonl);

  for (const artifact of packet.artifacts) {
    const rel = assertOutputArtifactPath(config.workspaceRoot, workspaceRel, artifact.path);
    safeWriteFile(config.workspaceRoot, rel, artifact.content);
  }
}
