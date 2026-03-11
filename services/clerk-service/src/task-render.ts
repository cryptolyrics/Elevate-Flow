import { CanonicalTaskRecord, TaskIndex } from "./task-types";

function taskLine(task: CanonicalTaskRecord): string {
  return `- [${task.priority}] ${task.task_id} (${task.status}) ${task.title}${task.owner_agent ? ` — ${task.owner_agent}` : ""}`;
}

function section(title: string, tasks: CanonicalTaskRecord[]): string[] {
  return [
    `## ${title}`,
    ...(tasks.length > 0 ? tasks.map(taskLine) : ["- none"]),
    "",
  ];
}

export function renderTasksMd(openTasks: CanonicalTaskRecord[], closedTasks: CanonicalTaskRecord[]): string {
  const byOwner = new Map<string, CanonicalTaskRecord[]>();
  for (const task of openTasks.filter((t) => !["BLOCKED", "IN_REVIEW", "PARKED"].includes(t.status))) {
    const key = task.owner_agent || "unassigned";
    byOwner.set(key, [...(byOwner.get(key) || []), task]);
  }

  const lines: string[] = ["# TASKS", ""];
  for (const owner of [...byOwner.keys()].sort()) {
    lines.push(`## ${owner}`);
    for (const task of byOwner.get(owner) || []) {
      lines.push(taskLine(task));
    }
    lines.push("");
  }

  lines.push(...section("Blocked", openTasks.filter((t) => t.status === "BLOCKED")));
  lines.push(...section("Review Queue", openTasks.filter((t) => t.status === "IN_REVIEW")));
  lines.push(...section("Recently Done", closedTasks.filter((t) => t.status === "DONE").slice(-10)));
  lines.push(...section("Parked", [...openTasks, ...closedTasks].filter((t) => t.status === "PARKED")));

  return `${lines.join("\n").trim()}\n`;
}

export function renderStatusMd(index: TaskIndex, openTasks: CanonicalTaskRecord[], closedTasks: CanonicalTaskRecord[], nowIso: string): string {
  const counts = {
    NEW: 0,
    CLAIMED: 0,
    IN_PROGRESS: 0,
    BLOCKED: 0,
    IN_REVIEW: 0,
    DONE: 0,
    PARKED: 0,
    DISCARDED: 0,
  };

  for (const task of [...openTasks, ...closedTasks]) {
    counts[task.status] += 1;
  }

  const now = new Date(nowIso).getTime();
  const overdueReviews = openTasks.filter((task) => task.status === "IN_REVIEW" && task.last_accepted_at && now - new Date(task.last_accepted_at).getTime() > 12 * 60 * 60 * 1000);
  const staleUnclaimed = openTasks.filter((task) => task.status === "NEW" && now - new Date(task.created_at).getTime() > 4 * 60 * 60 * 1000);
  const blockers = openTasks.filter((task) => task.status === "BLOCKED");
  const recentCompletions = closedTasks.filter((task) => task.status === "DONE").slice(-10);

  const lines: string[] = [
    "# STATUS",
    "",
    `Generated: ${index.generated_at}`,
    "",
    "## Task Counts",
    ...Object.entries(counts).map(([status, count]) => `- ${status}: ${count}`),
    "",
    "## Blockers by Owner",
    ...(blockers.length > 0 ? blockers.map((task) => `- ${task.blocker_owner || "unknown"}: ${task.task_id} ${task.title}`) : ["- none"]),
    "",
    "## Overdue Review Items",
    ...(overdueReviews.length > 0 ? overdueReviews.map((task) => `- ${task.task_id} ${task.title}`) : ["- none"]),
    "",
    "## Stale Unclaimed Tasks",
    ...(staleUnclaimed.length > 0 ? staleUnclaimed.map((task) => `- ${task.task_id} ${task.title}`) : ["- none"]),
    "",
    "## Recent Completions",
    ...(recentCompletions.length > 0 ? recentCompletions.map((task) => `- ${task.task_id} ${task.title}`) : ["- none"]),
    "",
  ];

  return `${lines.join("\n")}`;
}
