const fs = require('fs');
const path = require('path');

function readJson(file) {
  return JSON.parse(fs.readFileSync(file, 'utf8'));
}

function listJson(dir) {
  if (!fs.existsSync(dir)) return [];
  return fs.readdirSync(dir)
    .filter((name) => name.endsWith('.json'))
    .sort()
    .map((name) => readJson(path.join(dir, name)));
}

function listJsonl(file) {
  if (!fs.existsSync(file)) return [];
  const raw = fs.readFileSync(file, 'utf8').trim();
  if (!raw) return [];
  return raw.split('\n').filter(Boolean).map((line) => JSON.parse(line));
}

function loadTaskState(workspaceRoot) {
  const tasksRoot = path.join(workspaceRoot, 'tasks');
  const openTasks = listJson(path.join(tasksRoot, 'open'));
  const closedTasks = listJson(path.join(tasksRoot, 'closed'));
  const indexPath = path.join(tasksRoot, 'index.json');
  const index = fs.existsSync(indexPath) ? readJson(indexPath) : null;
  const day = new Date().toISOString().slice(0, 10);
  const events = listJsonl(path.join(tasksRoot, 'events', `${day}.jsonl`));
  const rejections = listJsonl(path.join(tasksRoot, 'rejections', `${day}.jsonl`));
  return { tasksRoot, openTasks, closedTasks, index, events, rejections };
}

function ageHours(iso, nowIso = new Date().toISOString()) {
  if (!iso) return 0;
  return (new Date(nowIso).getTime() - new Date(iso).getTime()) / (1000 * 60 * 60);
}

module.exports = { loadTaskState, ageHours };
