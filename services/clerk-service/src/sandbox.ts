import fs from "fs";
import path from "path";

export class SandboxError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "SandboxError";
  }
}

export function resolveInSandbox(root: string, relativePath: string): string {
  if (!relativePath || relativePath.includes("\0")) {
    throw new SandboxError("Invalid path");
  }
  if (path.isAbsolute(relativePath)) {
    throw new SandboxError("Absolute paths not allowed");
  }

  const normalized = path.normalize(relativePath);
  if (normalized === ".." || normalized.startsWith(`..${path.sep}`)) {
    throw new SandboxError("Path traversal not allowed");
  }

  const rootAbs = path.resolve(root);
  const rootReal = fs.existsSync(rootAbs) ? fs.realpathSync(rootAbs) : rootAbs;
  const target = path.resolve(rootAbs, normalized);

  if (target !== rootAbs && !target.startsWith(`${rootAbs}${path.sep}`)) {
    throw new SandboxError("Escapes sandbox root");
  }

  const parts = normalized.split(path.sep).filter((p) => p.length > 0);
  let current = rootAbs;
  for (let i = 0; i < parts.length; i += 1) {
    current = path.join(current, parts[i]);
    if (!fs.existsSync(current)) {
      continue;
    }
    const real = fs.realpathSync(current);
    if (real !== rootReal && !real.startsWith(`${rootReal}${path.sep}`)) {
      throw new SandboxError("Symlink escape not allowed");
    }
  }

  return target;
}

export function safeWriteFile(root: string, relativePath: string, content: string): void {
  const target = resolveInSandbox(root, relativePath);
  fs.mkdirSync(path.dirname(target), { recursive: true });

  const tmp = `${target}.tmp-${process.pid}-${Date.now()}`;
  fs.writeFileSync(tmp, content, "utf8");
  fs.renameSync(tmp, target);
}

export function safeAppendLines(root: string, relativePath: string, lines: string[]): void {
  const target = resolveInSandbox(root, relativePath);
  fs.mkdirSync(path.dirname(target), { recursive: true });

  const payload = lines.length > 0 ? `${lines.join("\n")}\n` : "";
  if (payload.length > 0) {
    fs.appendFileSync(target, payload, "utf8");
  }
}
