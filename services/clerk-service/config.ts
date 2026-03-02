/**
 * Clerk Service - Config Module
 * Loads and validates configuration from config.json
 */

import * as fs from 'fs';
import * as path from 'path';

export interface JobConfig {
  agentId: string;
  jobId: string;
  workspace: string;
}

export interface ClerkConfig {
  workspaceRoot: string;
  pollIntervalSec: number;
  jobs: JobConfig[];
  fetchMode: 'cli';
  reportWorkspace: string;
}

export function loadConfig(configPath: string): ClerkConfig {
  const raw = fs.readFileSync(configPath, 'utf-8');
  const config = JSON.parse(raw) as ClerkConfig;

  // Validate required fields
  if (!config.workspaceRoot) throw new Error('workspaceRoot required');
  if (!config.jobs || config.jobs.length === 0) throw new Error('jobs required');
  if (!config.reportWorkspace) throw new Error('reportWorkspace required');

  // Set defaults
  if (!config.pollIntervalSec) config.pollIntervalSec = 120;
  if (!config.fetchMode) config.fetchMode = 'cli';

  // Validate no duplicate jobId
  const jobIds = config.jobs.map(j => j.jobId);
  const duplicates = jobIds.filter((id, i) => jobIds.indexOf(id) !== i);
  if (duplicates.length > 0) {
    throw new Error(`Duplicate jobId: ${duplicates.join(', ')}`);
  }

  return config;
}

export function getConfigPath(): string {
  return process.env.CLERK_CONFIG || path.join(process.cwd(), 'config.json');
}
