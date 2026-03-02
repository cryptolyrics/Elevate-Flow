import fs from "fs";
import os from "os";
import path from "path";
import { OpenClawCliProvider } from "../src/openclaw-cli-provider";

function writeExecutableScript(contents: string): string {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "clerk-openclaw-"));
  const scriptPath = path.join(dir, "openclaw-mock.sh");
  fs.writeFileSync(scriptPath, contents, { encoding: "utf8", mode: 0o755 });
  return scriptPath;
}

describe("OpenClawCliProvider", () => {
  test("falls back from --job/--run to --id", async () => {
    const script = writeExecutableScript(`#!/bin/sh
args="$*"

if printf '%s' "$args" | grep -q -- "--job"; then
  echo "unknown flag: --job" >&2
  exit 2
fi

if printf '%s' "$args" | grep -q -- "--run"; then
  echo "unknown flag: --run" >&2
  exit 2
fi

if printf '%s' "$args" | grep -q -- "cron runs list"; then
  echo '[{"id":"run-1","job_id":"job-1","status":"completed","started_at":"2026-03-01T00:00:00Z"}]'
  exit 0
fi

if printf '%s' "$args" | grep -q -- "cron runs output"; then
  echo "packet-output"
  exit 0
fi

echo "unexpected args: $args" >&2
exit 3
`);

    try {
      const provider = new OpenClawCliProvider(script, 2000);
      const runs = await provider.listRunsAfter("job-1");
      expect(runs).toHaveLength(1);
      expect(runs[0].runId).toBe("run-1");

      const output = await provider.getRunOutput("run-1");
      expect(output.trim()).toBe("packet-output");
    } finally {
      fs.rmSync(path.dirname(script), { recursive: true, force: true });
    }
  });

  test("fails fast when CLI call times out", async () => {
    const script = writeExecutableScript(`#!/bin/sh
sleep 2
echo "[]"
`);

    try {
      const provider = new OpenClawCliProvider(script, 100);
      await expect(provider.listRunsAfter("job-1")).rejects.toThrow("timed out");
    } finally {
      fs.rmSync(path.dirname(script), { recursive: true, force: true });
    }
  });
});
