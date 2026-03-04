/**
 * Poller Module
 * Orchestrates fetching, parsing, and writing
 */

import * as fs from 'fs';
import * as path from 'path';
import { ClerkConfig, JobConfig } from '../config';
import { FetchProvider, RunRecord } from '../fetch/openclaw-cli';
import { parsePacket, PacketParseError } from '../parse/packet';
import { writeStatus } from '../write/status';
import { writeLogs } from '../write/logs';
import { writeArtifacts } from '../write/artifacts';
import { advanceState, loadState, touchPollState } from '../write/state';
import { safeWriteFile, validateSandbox } from '../write/sandbox';
import { PollResult, generateReport, writeReport } from '../report/clerk-report';

export class Poller {
  private config: ClerkConfig;
  private provider: FetchProvider;
  private running = false;

  constructor(config: ClerkConfig, provider: FetchProvider) {
    this.config = config;
    this.provider = provider;
  }

  async poll(): Promise<PollResult[]> {
    const results: PollResult[] = [];
    const pollStart = new Date();

    for (const job of this.config.jobs) {
      const result = await this.processJob(job);
      results.push(result);
    }

    const pollEnd = new Date();
    const report = generateReport(
      this.config.workspaceRoot,
      this.config.jobs,
      pollStart,
      pollEnd,
      results
    );

    writeReport(this.config.reportWorkspace, report);
    touchPollState(this.config.workspaceRoot);
    return results;
  }

  private async processJob(job: JobConfig): Promise<PollResult> {
    const result: PollResult = {
      jobId: job.jobId,
      runsProcessed: 0,
      failures: 0,
      errors: []
    };

    try {
      const state = loadState(this.config.workspaceRoot);
      const lastRunId = state.jobs[job.jobId]?.lastProcessedRunId || null;

      const runs = await this.provider.listRunsAfter(job.jobId, lastRunId || undefined);

      // Process ALL runs after state, oldest first
      for (const run of runs) {
        try {
          await this.processRun(job, run);
          advanceState(this.config.workspaceRoot, job.jobId, run.runId);
          result.runsProcessed++;
        } catch (err) {
          result.failures++;
          result.errors.push(`Run ${run.runId}: ${(err as Error).message}`);
          await this.writeDeadLetter(job.jobId, run.runId, err as Error);
        }
      }
    } catch (err) {
      result.errors.push(`Job fetch: ${(err as Error).message}`);
      result.failures++;
    }

    return result;
  }

  private async processRun(job: JobConfig, run: RunRecord): Promise<void> {
    // Get output from CLI
    const output = await (this.provider as any).getRunOutput?.(run.runId);
    if (!output) {
      throw new Error('No output available for run');
    }

    // Parse packet
    const packet = parsePacket(output);

    // Validate agentId matches
    if (packet.agentId !== job.agentId) {
      throw new Error(`Agent ID mismatch: expected ${job.agentId}, got ${packet.agentId}`);
    }

    // Write canonical files
    writeStatus(this.config.workspaceRoot, job.jobId, packet.statusMd);
    writeLogs(this.config.workspaceRoot, job.jobId, packet.logJsonl);
    writeArtifacts(this.config.workspaceRoot, job.jobId, packet.artifacts);
  }

  private async writeDeadLetter(jobId: string, runId: string, error: Error): Promise<void> {
    const today = new Date().toISOString().split('T')[0];
    const dirPath = `clerk-dead-letter/${today}`;
    
    const deadLetter = {
      jobId,
      runId,
      error: error.message,
      timestamp: new Date().toISOString()
    };

    const targetPath = `${dirPath}/${jobId}-${runId}.json`;
    safeWriteFile(this.config.reportWorkspace, targetPath, JSON.stringify(deadLetter, null, 2));
  }

  start(): void {
    this.running = true;
    this.runLoop();
  }

  stop(): void {
    this.running = false;
  }

  private async runLoop(): Promise<void> {
    while (this.running) {
      try {
        await this.poll();
      } catch (err) {
        console.error('Poll error:', err);
      }

      await new Promise(resolve => 
        setTimeout(resolve, this.config.pollIntervalSec * 1000)
      );
    }
  }
}
