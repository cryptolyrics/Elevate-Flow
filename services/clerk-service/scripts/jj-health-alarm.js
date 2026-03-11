#!/usr/bin/env node
const path = require('path');
const { loadTaskState, ageHours } = require('./task-state-utils');

const workspaceRoot = process.argv[2] ? path.resolve(process.argv[2]) : path.resolve(__dirname, '../..');
const nowIso = new Date().toISOString();
const { openTasks, index, rejections } = loadTaskState(workspaceRoot);

const staleBlocked = openTasks.filter((t) => t.status === 'BLOCKED' && ageHours(t.blocked_at, nowIso) > 8)
  .map((t) => ({
    issue_type: 'STALE_BLOCKED',
    task_id: t.task_id,
    owner_agent: t.owner_agent || null,
    blocker_owner: t.blocker_owner || null,
    threshold_hours: 8,
    age_hours: Number(ageHours(t.blocked_at, nowIso).toFixed(1)),
    required_next_action: 'review blocker and unblock, park, or escalate',
  }));

const overdueReview = openTasks.filter((t) => t.status === 'IN_REVIEW' && ageHours(t.last_accepted_at || t.created_at, nowIso) > 12)
  .map((t) => ({
    issue_type: 'OVERDUE_REVIEW',
    task_id: t.task_id,
    owner_agent: t.owner_agent || null,
    threshold_hours: 12,
    age_hours: Number(ageHours(t.last_accepted_at || t.created_at, nowIso).toFixed(1)),
    required_next_action: 'review or return task to active work',
  }));

const staleUnclaimed = openTasks.filter((t) => t.status === 'NEW' && ageHours(t.created_at, nowIso) > 4)
  .map((t) => ({
    issue_type: 'STALE_UNCLAIMED',
    task_id: t.task_id,
    owner_agent: null,
    threshold_hours: 4,
    age_hours: Number(ageHours(t.created_at, nowIso).toFixed(1)),
    required_next_action: 'assign owner or park/discard',
  }));

const brokenBlockedMetadata = openTasks.filter((t) => t.status === 'BLOCKED' && (!t.reason || !t.blocker_owner || !t.review_path || !t.blocked_at))
  .map((t) => ({
    issue_type: 'BROKEN_BLOCKED_METADATA',
    task_id: t.task_id,
    owner_agent: t.owner_agent || null,
    blocker_owner: t.blocker_owner || null,
    missing: [
      !t.reason ? 'reason' : null,
      !t.blocker_owner ? 'blocker_owner' : null,
      !t.review_path ? 'review_path' : null,
      !t.blocked_at ? 'blocked_at' : null,
    ].filter(Boolean),
    required_next_action: 'repair blocked-task metadata immediately',
  }));

const repeatedCodes = {};
for (const r of rejections) repeatedCodes[r.code] = (repeatedCodes[r.code] || 0) + 1;
const repeatedRejections = rejections.filter((r) => (repeatedCodes[r.code] || 0) > 1).map((r) => ({
  issue_type: 'REPEATED_REJECTION_PATTERN',
  code: r.code,
  task_id: r.task_id || null,
  actor_id: r.actor_id || null,
  message: r.message,
  required_next_action: 'inspect rejection pattern and repair upstream packet flow',
}));

const issues = [...staleBlocked, ...overdueReview, ...staleUnclaimed, ...brokenBlockedMetadata, ...repeatedRejections];

const result = {
  kind: 'jj_health_alarm.v1',
  generated_at: nowIso,
  source: {
    workspace_root: workspaceRoot,
    tasks_root: path.join(workspaceRoot, 'tasks'),
    index_present: Boolean(index),
  },
  status: issues.length === 0 ? 'CLEAN' : 'ALERT',
  counts: {
    stale_blocked: staleBlocked.length,
    overdue_review: overdueReview.length,
    stale_unclaimed: staleUnclaimed.length,
    broken_blocked_metadata: brokenBlockedMetadata.length,
    repeated_rejection_patterns: repeatedRejections.length,
    total_issues: issues.length,
  },
  issues,
};

console.log(JSON.stringify(result, null, 2));
