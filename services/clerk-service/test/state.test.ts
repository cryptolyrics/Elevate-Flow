import fs from "fs";
import os from "os";
import path from "path";
import { ClerkState, advanceState, loadState, saveState } from "../src/state";

describe("state", () => {
  const root = path.join(os.tmpdir(), `clerk-state-${Date.now()}`);

  beforeAll(() => {
    fs.mkdirSync(root, { recursive: true });
  });

  afterAll(() => {
    fs.rmSync(root, { recursive: true, force: true });
  });

  test("loadState returns default when missing", () => {
    const state = loadState(root);
    expect(state.jobs).toEqual({});
  });

  test("saveState and loadState round-trip", () => {
    const state: ClerkState = {
      lastPollAt: "2026-03-01T10:00:00Z",
      jobs: {
        "job-1": {
          lastProcessedRunId: "run-1",
          lastProcessedAt: "2026-03-01T10:00:00Z",
        },
      },
    };
    saveState(root, state);
    const loaded = loadState(root);
    expect(loaded.jobs["job-1"].lastProcessedRunId).toBe("run-1");
  });

  test("advanceState updates one job", () => {
    advanceState(root, "job-2", "run-2");
    const loaded = loadState(root);
    expect(loaded.jobs["job-2"].lastProcessedRunId).toBe("run-2");
  });
});
