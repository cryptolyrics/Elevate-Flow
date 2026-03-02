/**
 * Sandbox Path Protection Tests
 */

import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';
import { validateSandbox, safeWriteFile, SandboxError } from '../src/write/sandbox';

describe('sandbox path protections', () => {
  const workspaceRoot = path.join(os.tmpdir(), 'clerk-test-' + Date.now());

  beforeAll(() => {
    fs.mkdirSync(workspaceRoot, { recursive: true });
  });

  afterAll(() => {
    // Clean up
    fs.rmSync(workspaceRoot, { recursive: true, force: true });
  });

  test('rejects absolute paths', () => {
    expect(() => validateSandbox(workspaceRoot, '/etc/passwd'))
      .toThrow(SandboxError);
    expect(() => validateSandbox(workspaceRoot, '/etc/passwd'))
      .toThrow('Absolute paths not allowed');
  });

  test('rejects path traversal ..', () => {
    expect(() => validateSandbox(workspaceRoot, '../etc/passwd'))
      .toThrow(SandboxError);
    expect(() => validateSandbox(workspaceRoot, 'foo/../../etc/passwd'))
      .toThrow(SandboxError);
    expect(() => validateSandbox(workspaceRoot, 'foo/..'))
      .toThrow('Path traversal not allowed');
  });

  test('rejects paths that escape sandbox via symlink trick', () => {
    // Create a symlink inside workspace that points outside
    const symlinkPath = path.join(workspaceRoot, 'evil-link');
    try {
      fs.symlinkSync(os.tmpdir(), symlinkPath);
      
      // Even if symlink exists, validateSandbox should reject
      // because we verify real paths against workspace root
      expect(() => validateSandbox(workspaceRoot, 'evil-link/file'))
        .toThrow(SandboxError);
    } finally {
      if (fs.existsSync(symlinkPath)) fs.unlinkSync(symlinkPath);
    }
  });

  test('accepts valid relative paths', () => {
    const result = validateSandbox(workspaceRoot, 'outputs/test.txt');
    expect(result).toBe(path.join(workspaceRoot, 'outputs/test.txt'));
  });

  test('accepts nested relative paths', () => {
    const result = validateSandbox(workspaceRoot, 'outputs/deep/nested/file.txt');
    expect(result).toBe(path.join(workspaceRoot, 'outputs/deep/nested/file.txt'));
  });

  test('safeWriteFile writes atomically within sandbox', () => {
    const content = 'Hello World';
    safeWriteFile(workspaceRoot, 'test-output.txt', content);
    
    const result = fs.readFileSync(path.join(workspaceRoot, 'test-output.txt'), 'utf-8');
    expect(result).toBe(content);
  });

  test('safeWriteFile creates directories as needed', () => {
    safeWriteFile(workspaceRoot, 'nested/dir/file.txt', 'content');
    
    const result = fs.readFileSync(path.join(workspaceRoot, 'nested/dir/file.txt'), 'utf-8');
    expect(result).toBe('content');
  });

  test('safeWriteFile rejects escape attempt', () => {
    expect(() => safeWriteFile(workspaceRoot, '../escape.txt', 'bad'))
      .toThrow(SandboxError);
  });
});
