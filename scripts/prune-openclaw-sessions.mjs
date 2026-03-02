#!/usr/bin/env node

import fs from "fs";
import os from "os";
import path from "path";

function parseArgs(argv) {
  const args = {
    apply: false,
    maxAgeHours: 8,
    maxSessions: 4,
    keepKeys: ["agent:main:main"],
    storePath: path.join(os.homedir(), ".openclaw", "agents", "main", "sessions", "sessions.json"),
  };

  for (let i = 2; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === "--apply") {
      args.apply = true;
      continue;
    }
    if (arg === "--store" && argv[i + 1]) {
      args.storePath = argv[i + 1];
      i += 1;
      continue;
    }
    if (arg === "--max-age-hours" && argv[i + 1]) {
      args.maxAgeHours = Number(argv[i + 1]);
      i += 1;
      continue;
    }
    if (arg === "--max-sessions" && argv[i + 1]) {
      args.maxSessions = Number(argv[i + 1]);
      i += 1;
      continue;
    }
    if (arg === "--keep-key" && argv[i + 1]) {
      args.keepKeys.push(argv[i + 1]);
      i += 1;
      continue;
    }
    if (arg === "--help" || arg === "-h") {
      printHelp();
      process.exit(0);
    }
  }

  if (!Number.isFinite(args.maxAgeHours) || args.maxAgeHours < 0) {
    throw new Error("--max-age-hours must be a non-negative number");
  }
  if (!Number.isFinite(args.maxSessions) || args.maxSessions < 1) {
    throw new Error("--max-sessions must be >= 1");
  }

  return args;
}

function printHelp() {
  console.log(`Usage:
  node scripts/prune-openclaw-sessions.mjs [options]

Options:
  --apply                    Write pruned result to sessions.json
  --store <path>             Override sessions store path
  --max-age-hours <n>        Keep non-pinned sessions newer than N hours (default: 8)
  --max-sessions <n>         Keep at most N total sessions (default: 4)
  --keep-key <session-key>   Session key to always keep (repeatable)
  --help                     Show this help

Default mode is dry-run (no file writes).`);
}

function unwrapSessions(doc) {
  if (Array.isArray(doc)) {
    return { shape: "array", sessions: doc };
  }
  if (doc && typeof doc === "object" && Array.isArray(doc.sessions)) {
    return { shape: "object", sessions: doc.sessions };
  }
  throw new Error("Unsupported sessions.json schema (expected array or { sessions: [] })");
}

function parseTimestamp(value) {
  if (!value) {
    return 0;
  }
  if (typeof value === "number" && Number.isFinite(value)) {
    // If likely epoch seconds convert to milliseconds.
    return value < 1e12 ? value * 1000 : value;
  }
  if (typeof value === "string") {
    const ts = Date.parse(value);
    return Number.isNaN(ts) ? 0 : ts;
  }
  return 0;
}

function sessionTimestamp(s) {
  const candidates = [
    s.updatedAt,
    s.lastUpdatedAt,
    s.lastMessageAt,
    s.lastSeenAt,
    s.createdAt,
    s.ts,
  ];
  for (const c of candidates) {
    const parsed = parseTimestamp(c);
    if (parsed > 0) {
      return parsed;
    }
  }
  return 0;
}

function ageHoursFromTs(ts, nowMs) {
  if (!ts) {
    return Number.POSITIVE_INFINITY;
  }
  return (nowMs - ts) / 3600000;
}

function isPinned(session, keepSet) {
  const key = String(session?.key || "");
  return keepSet.has(key);
}

function isLikelyActive(session) {
  if (session?.active === true) {
    return true;
  }
  const status = String(session?.status || "").toLowerCase();
  return status === "active" || status === "running";
}

function summarize(sessions, keepSet, nowMs) {
  return sessions.map((s, idx) => {
    const ts = sessionTimestamp(s);
    return {
      index: idx,
      key: String(s?.key || ""),
      kind: String(s?.kind || "unknown"),
      model: String(s?.model || "unknown"),
      ageHours: ageHoursFromTs(ts, nowMs),
      pinned: isPinned(s, keepSet),
      active: isLikelyActive(s),
      ts,
      raw: s,
    };
  });
}

function selectSessions(rows, maxAgeHours, maxSessions) {
  const pinned = rows.filter((r) => r.pinned);
  const active = rows.filter((r) => r.active && !r.pinned);
  const fresh = rows.filter((r) => !r.pinned && !r.active && r.ageHours <= maxAgeHours);
  const stale = rows.filter((r) => !r.pinned && !r.active && r.ageHours > maxAgeHours);

  const sortDesc = (a, b) => b.ts - a.ts;
  active.sort(sortDesc);
  fresh.sort(sortDesc);
  stale.sort(sortDesc);

  const keep = [...pinned];
  const slots = Math.max(0, maxSessions - keep.length);

  for (const row of [...active, ...fresh, ...stale]) {
    if (keep.length >= maxSessions || keep.length - pinned.length >= slots) {
      break;
    }
    keep.push(row);
  }

  const keepIndex = new Set(keep.map((k) => k.index));
  const remove = rows.filter((r) => !keepIndex.has(r.index));
  return { keep, remove };
}

function printPlan(rows, keep, remove) {
  const totalTokens = rows.reduce((acc, r) => {
    const ctx = Number(r?.raw?.tokens?.ctx || 0);
    return acc + (Number.isFinite(ctx) ? ctx : 0);
  }, 0);
  const removeTokens = remove.reduce((acc, r) => {
    const ctx = Number(r?.raw?.tokens?.ctx || 0);
    return acc + (Number.isFinite(ctx) ? ctx : 0);
  }, 0);

  console.log(`Session rows: ${rows.length}`);
  console.log(`Keep: ${keep.length}`);
  console.log(`Remove: ${remove.length}`);
  console.log(`Estimated ctx tokens total: ${totalTokens}`);
  console.log(`Estimated ctx tokens removed: ${removeTokens}`);
  console.log("");
  for (const r of remove) {
    const age = Number.isFinite(r.ageHours) ? `${r.ageHours.toFixed(1)}h` : "unknown";
    console.log(`- remove key=${r.key} kind=${r.kind} model=${r.model} age=${age}`);
  }
}

function writePruned(doc, shape, keepRows, storePath) {
  const backupPath = `${storePath}.bak.${Date.now()}`;
  fs.copyFileSync(storePath, backupPath);

  if (shape === "array") {
    fs.writeFileSync(storePath, `${JSON.stringify(keepRows.map((r) => r.raw), null, 2)}\n`, "utf8");
  } else {
    doc.sessions = keepRows.map((r) => r.raw);
    fs.writeFileSync(storePath, `${JSON.stringify(doc, null, 2)}\n`, "utf8");
  }

  return backupPath;
}

function main() {
  const args = parseArgs(process.argv);
  const keepSet = new Set(args.keepKeys);

  if (!fs.existsSync(args.storePath)) {
    throw new Error(`sessions.json not found: ${args.storePath}`);
  }

  const raw = fs.readFileSync(args.storePath, "utf8");
  const doc = JSON.parse(raw);
  const { shape, sessions } = unwrapSessions(doc);
  const nowMs = Date.now();
  const rows = summarize(sessions, keepSet, nowMs);
  const { keep, remove } = selectSessions(rows, args.maxAgeHours, args.maxSessions);

  printPlan(rows, keep, remove);

  if (!args.apply) {
    console.log("\nDry-run only. Re-run with --apply to write changes.");
    return;
  }

  const backup = writePruned(doc, shape, keep, args.storePath);
  console.log(`\nPruned sessions store written: ${args.storePath}`);
  console.log(`Backup written: ${backup}`);
}

try {
  main();
} catch (err) {
  console.error(`prune-openclaw-sessions failed: ${(err).message}`);
  process.exit(1);
}
