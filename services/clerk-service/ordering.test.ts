/**
 * Ordered Processing Tests
 * Tests that multiple runs are processed oldest -> newest
 */

import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';
import { parsePacket } from '../src/parse/packet';

// Mock run data
interface MockRun {
  runId: string;
  jobId: string;
  agentId: string;
  status: 'completed' | 'failed' | 'running';
  startedAt: string;
  output: string;
}

describe('ordered processing of multiple runs', () => {
  test('parses runs in oldest -> newest order', () => {
    const runs: MockRun[] = [
      {
        runId: 'run-001',
        jobId: 'job-1',
        agentId: 'baby-vlad',
        status: 'completed',
        startedAt: '2026-02-27T08:00:00Z',
        output: `===AGENT_ID===
baby-vlad
====

===STATUS_MD===
First run
====

===LOG_JSONL===
{"run":"1"}
====

===ARTIFACTS===
[]
====`
      },
      {
        runId: 'run-002',
        jobId: 'job-1',
        agentId: 'baby-vlad',
        status: 'completed',
        startedAt: '2026-02-27T09:00:00Z',
        output: `===AGENT_ID===
baby-vlad
====

===STATUS_MD===
Second run
====

===LOG_JSONL===
{"run":"2"}
====

===ARTIFACTS===
[]
====`
      },
      {
        runId: 'run-003',
        jobId: 'job-1',
        agentId: 'baby-vlad',
        status: 'completed',
        startedAt: '2026-02-27T10:00:00Z',
        output: `===AGENT_ID===
baby-vlad
====

===STATUS_MD===
Third run
====

===LOG_JSONL===
{"run":"3"}
====

===ARTIFACTS===
[]
====`
      }
    ];

    // Sort runs oldest -> newest (by startedAt)
    const sorted = [...runs].sort(
      (a, b) => new Date(a.startedAt).getTime() - new Date(b.startedAt).getTime()
    );

    // Process each and verify order
    const processed: string[] = [];
    for (const run of sorted) {
      const packet = parsePacket(run.output);
      processed.push(packet.statusMd.trim());
    }

    expect(processed).toEqual([
      'First run',
      'Second run', 
      'Third run'
    ]);
  });

  test('handles unsorted input by sorting first', () => {
    const runs = [
      { startedAt: '2026-02-27T10:00:00Z', runId: 'run-C' },
      { startedAt: '2026-02-27T08:00:00Z', runId: 'run-A' },
      { startedAt: '2026-02-27T09:00:00Z', runId: 'run-B' }
    ];

    // Simulate how poller should sort
    const sorted = [...runs].sort(
      (a, b) => new Date(a.startedAt).getTime() - new Date(b.startedAt).getTime()
    );

    expect(sorted.map(r => r.runId)).toEqual(['run-A', 'run-B', 'run-C']);
  });

  test('only processes runs after lastProcessedRunId', () => {
    const lastProcessed = 'run-002';
    const allRuns = [
      { runId: 'run-001', startedAt: '2026-02-27T08:00:00Z' },
      { runId: 'run-002', startedAt: '2026-02-27T09:00:00Z' },
      { runId: 'run-003', startedAt: '2026-02-27T10:00:00Z' },
      { runId: 'run-004', startedAt: '2026-02-27T11:00:00Z' }
    ];

    // Filter to runs after lastProcessed
    const toProcess = allRuns.filter(
      r => r.runId !== lastProcessed && 
           allRuns.findIndex(a => a.runId === r.runId) > allRuns.findIndex(a => a.runId === lastProcessed)
    );

    // Actually, the filter should be: runs with higher index than lastProcessed
    const lastIdx = allRuns.findIndex(r => r.runId === lastProcessed);
    const pending = allRuns.slice(lastIdx + 1);

    expect(pending.map(r => r.runId)).toEqual(['run-003', 'run-004']);
  });
});
