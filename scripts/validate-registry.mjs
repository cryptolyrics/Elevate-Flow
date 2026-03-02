import path from 'path';
import { fileURLToPath } from 'url';
import { buildGenerated, compareGenerated, loadRegistry, validateRegistry } from './lib/registry.mjs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const rootDir = path.resolve(__dirname, '..');

const { agentsDoc, jobsDoc } = loadRegistry(rootDir);
const validation = validateRegistry(agentsDoc, jobsDoc);

if (!validation.valid) {
  console.error('Registry validation failed:');
  for (const err of validation.errors) {
    console.error(`- ${err}`);
  }
  process.exit(1);
}

const generated = buildGenerated(agentsDoc, jobsDoc);
const diff = compareGenerated(rootDir, generated);

if (!diff.agentsMatch || !diff.cronMatch) {
  console.error('Generated OpenClaw snapshots are out of date. Run: npm run generate:openclaw');
  process.exit(1);
}

console.log('Registry and generated OpenClaw snapshots are valid.');
