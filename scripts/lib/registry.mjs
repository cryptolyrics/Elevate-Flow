import fs from 'fs';
import path from 'path';
import { parse } from 'yaml';

function readYaml(filePath) {
  const raw = fs.readFileSync(filePath, 'utf8');
  return parse(raw);
}

export function loadRegistry(rootDir) {
  const agentsPath = path.join(rootDir, 'registry', 'agents.yml');
  const jobsPath = path.join(rootDir, 'registry', 'jobs.yml');

  const agentsDoc = readYaml(agentsPath);
  const jobsDoc = readYaml(jobsPath);

  return { agentsDoc, jobsDoc };
}

export function validateRegistry(agentsDoc, jobsDoc) {
  const errors = [];

  if (!agentsDoc || !Array.isArray(agentsDoc.agents)) {
    errors.push('agents.yml must contain an agents array');
  }
  if (!jobsDoc || !Array.isArray(jobsDoc.jobs)) {
    errors.push('jobs.yml must contain a jobs array');
  }

  if (errors.length > 0) {
    return { valid: false, errors };
  }

  const byAgent = new Map();
  for (const agent of agentsDoc.agents) {
    if (!agent.agent_id) {
      errors.push('agents.yml entry missing agent_id');
      continue;
    }
    if (byAgent.has(agent.agent_id)) {
      errors.push(`Duplicate agent_id: ${agent.agent_id}`);
      continue;
    }
    byAgent.set(agent.agent_id, agent);
  }

  const seenJobs = new Set();
  for (const job of jobsDoc.jobs) {
    if (!job.job_id) {
      errors.push('jobs.yml entry missing job_id');
      continue;
    }
    if (seenJobs.has(job.job_id)) {
      errors.push(`Duplicate job_id: ${job.job_id}`);
    }
    seenJobs.add(job.job_id);

    if (!job.agent_id || !byAgent.has(job.agent_id)) {
      errors.push(`Unknown agent_id in jobs.yml: ${job.agent_id || '<missing>'}`);
      continue;
    }

    const agent = byAgent.get(job.agent_id);
    if (job.workspace !== agent.workspace) {
      errors.push(`Workspace mismatch for job ${job.job_id}: ${job.workspace} != ${agent.workspace}`);
    }

    if (!job.schedule || !job.schedule.cron || !job.schedule.timezone) {
      errors.push(`Job ${job.job_id} must define schedule.cron and schedule.timezone`);
    }

    const target = job.runtime?.target;
    if (target !== 'isolated' && target !== 'main') {
      errors.push(`Job ${job.job_id} runtime.target must be isolated or main`);
    }
  }

  return { valid: errors.length === 0, errors };
}

export function buildGenerated(agentsDoc, jobsDoc) {
  const agents = (agentsDoc.agents || []).map((a) => ({
    agentId: a.agent_id,
    workspace: a.workspace,
    model: a.default_model?.model || '',
    provider: a.default_model?.provider || '',
  }));

  const jobs = (jobsDoc.jobs || [])
    .filter((j) => j.enabled === true)
    .map((j) => ({
      jobId: j.job_id,
      agentId: j.agent_id,
      cron: j.schedule?.cron || '',
      timezone: j.schedule?.timezone || '',
      target: j.runtime?.target || '',
    }));

  return {
    agentsGenerated: {
      version: 1,
      agents,
    },
    cronGenerated: {
      version: 1,
      jobs,
    },
  };
}

export function writeGenerated(rootDir, generated) {
  const outDir = path.join(rootDir, 'openclaw', 'generated');
  fs.mkdirSync(outDir, { recursive: true });

  const agentsPath = path.join(outDir, 'agents.generated.json');
  const cronPath = path.join(outDir, 'cron.generated.json');

  fs.writeFileSync(agentsPath, `${JSON.stringify(generated.agentsGenerated, null, 2)}\n`, 'utf8');
  fs.writeFileSync(cronPath, `${JSON.stringify(generated.cronGenerated, null, 2)}\n`, 'utf8');
}

export function compareGenerated(rootDir, generated) {
  const agentsPath = path.join(rootDir, 'openclaw', 'generated', 'agents.generated.json');
  const cronPath = path.join(rootDir, 'openclaw', 'generated', 'cron.generated.json');

  const expectedAgents = `${JSON.stringify(generated.agentsGenerated, null, 2)}\n`;
  const expectedCron = `${JSON.stringify(generated.cronGenerated, null, 2)}\n`;

  const actualAgents = fs.existsSync(agentsPath) ? fs.readFileSync(agentsPath, 'utf8') : '';
  const actualCron = fs.existsSync(cronPath) ? fs.readFileSync(cronPath, 'utf8') : '';

  return {
    agentsMatch: actualAgents === expectedAgents,
    cronMatch: actualCron === expectedCron,
  };
}
