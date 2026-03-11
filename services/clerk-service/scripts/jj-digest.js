#!/usr/bin/env node
const path = require('path');
const { loadTaskState, ageHours } = require('./task-state-utils');

const workspaceRoot = process.argv[2] ? path.resolve(process.argv[2]) : path.resolve(__dirname, '../..');
const nowIso = new Date().toISOString();
const { openTasks, closedTasks, index, rejections } = loadTaskState(workspaceRoot);

const byOwner = {};
for (const task of openTasks) {
  const owner = task.owner_agent || 'unassigned';
  byOwner[owner] = (byOwner[owner] || 0) + 1;
}

const blocked = openTasks.filter((t) => t.status === 'BLOCKED').map((t) => ({
  task_id: t.task_id,
  title: t.title,
  owner_agent: t.owner_agent,
  reason: t.reason || null,
  blocker_owner: t.blocker_owner || null,
  review_path: t.review_path || null,
  blocked_at: t.blocked_at || null,
}));

const overdueReview = openTasks.filter((t) => t.status === 'IN_REVIEW' && ageHours(t.last_accepted_at || t.created_at, nowIso) > 12)
  .map((t) => ({ task_id: t.task_id, title: t.title, owner_agent: t.owner_agent, age_hours: Number(ageHours(t.last_accepted_at || t.created_at, nowIso).toFixed(1)) }));

const staleUnclaimed = openTasks.filter((t) => t.status === 'NEW' && ageHours(t.created_at, nowIso) > 4)
  .map((t) => ({ task_id: t.task_id, title: t.title, age_hours: Number(ageHours(t.created_at, nowIso).toFixed(1)) }));

const recentCompletions = closedTasks.filter((t) => t.status === 'DONE').slice(-10).map((t) => ({
  task_id: t.task_id,
  title: t.title,
  owner_agent: t.owner_agent,
  closed_at: t.closed_at || t.last_accepted_at || null,
}));

const rejectionCounts = {};
for (const r of rejections) rejectionCounts[r.code] = (rejectionCounts[r.code] || 0) + 1;
const notableRejections = rejections.filter((r) => (rejectionCounts[r.code] || 0) > 1).map((r) => ({
  code: r.code,
  task_id: r.task_id || null,
  actor_id: r.actor_id || null,
  message: r.message,
}));

const result = {
  kind: 'jj_digest.v1',
  generated_at: nowIso,
  source: {
    workspace_root: workspaceRoot,
    tasks_root: path.join(workspaceRoot, 'tasks'),
    index_present: Boolean(index),
  },
  summary: {
    open_tasks_by_owner: byOwner,
    blocked_count: blocked.length,
    overdue_review_count: overdueReview.length,
    stale_unclaimed_count: staleUnclaimed.length,
    recent_completion_count: recentCompletions.length,
    notable_rejection_count: notableRejections.length,
  },
  blocked_tasks: blocked,
  overdue_review: overdueReview,
  stale_unclaimed: staleUnclaimed,
  recent_completions: recentCompletions,
  notable_rejections: notableRejections,
};

console.log(JSON.stringify(result, null, 2));
