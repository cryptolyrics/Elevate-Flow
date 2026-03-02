/**
 * State Management & Idempotency Tests
 */

import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';
import { loadState, saveState, advanceState, ClerkState } from '../src/write/state';

describe('state idempotency', () => {
  const testWorkspace = path.join(os.tmpdir(), 'clerk-state-test-' + Date.now());

  beforeAll(() => {
    fs.mkdirSync(path.join(testWorkspace, 'outputs'), { recursive: true });
  });

  afterAll(() => {
    fs.rmSync(testWorkspace, { recursive: true, force: true });
  });

  test('loadState returns default for missing file', () => {
    const state = loadState(testWorkspace);
    expect(state.jobs).toEqual({});
    expect(state.lastPollAt).toBe('');
  });

  test('saveState writes atomic file', () => {
    const state: ClerkState = {
      jobs: { 'job-1': { lastProcessedRunId: 'run-123', lastProcessedAt: '2026-02-27T10:00:00Z' } },
      lastPollAt: '2026-02-27T10:00:00Z'
    };
    
    saveState(testWorkspace, state);
    
    const loaded = loadState(testWorkspace);
    expect(loaded.jobs['job-1'].lastProcessedRunId).toBe('run-123');
  });

  test('advanceState updates only specified job', () => {
    // First, save initial state with two jobs
    const initialState: ClerkState = {
      jobs: {
        'job-1': { lastProcessedRunId: 'run-100', lastProcessedAt: '2026-02-27T09:00:00Z' }
      },
      lastPollAt: ''
    };
    saveState(testWorkspace, initialState);
    
    // Advance state for job-2 only
    advanceState(testWorkspace, 'job-2', 'run-200');
    
    const loaded = loadState(testWorkspace);
    
    // job-1 should be unchanged
    expect(loaded.jobs['job-1'].lastProcessedRunId).toBe('run-100');
    
    // job-2 should be updated
    expect(loaded.jobs['job-2'].lastProcessedRunId).toBe('run-200');
  });

  test('state is idempotent - writing same run twice is safe', () => {
    const state: ClerkState = {
      jobs: { 'job-x': { lastProcessedRunId: 'run-1', lastProcessedAt: '2026-02-27T10:00:00Z' } },
      lastPollAt: '2026-02-27T10:00:00Z'
    };
    
    saveState(testWorkspace, state);
    saveState(testWorkspace, state);
    
    const loaded = loadState(testWorkspace);
    expect(loaded.jobs['job-x'].lastProcessedRunId).toBe('run-1');
  });

  test('loadState handles corrupted JSON gracefully', () => {
    const statePath = path.join(testWorkspace, 'outputs', 'clerk-state.json');
    fs.writeFileSync(statePath, 'not valid json{{{', 'utf-8');
    
    const state = loadState(testWorkspace);
    expect(state.jobs).toEqual({});
  });
});
