import fs from "fs";
import os from "os";
import path from "path";
import { SandboxError, resolveInSandbox, safeWriteFile } from "../src/sandbox";

describe("sandbox", () => {
  const root = path.join(os.tmpdir(), `clerk-sandbox-${Date.now()}`);

  beforeAll(() => {
    fs.mkdirSync(root, { recursive: true });
  });

  afterAll(() => {
    fs.rmSync(root, { recursive: true, force: true });
  });

  test("rejects absolute paths", () => {
    expect(() => resolveInSandbox(root, "/etc/passwd")).toThrow(SandboxError);
  });

  test("rejects traversal", () => {
    expect(() => resolveInSandbox(root, "../escape.txt")).toThrow(SandboxError);
  });

  test("allows relative nested path", () => {
    const resolved = resolveInSandbox(root, "logs/2026-03-01.jsonl");
    expect(resolved.startsWith(root)).toBe(true);
  });

  test("safeWriteFile writes inside root", () => {
    safeWriteFile(root, "a/b/file.txt", "hello");
    const output = fs.readFileSync(path.join(root, "a/b/file.txt"), "utf8");
    expect(output).toBe("hello");
  });
});
